from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from piotw_orchestrator.unknown_company_v01 import OrchestrationResult, UnknownCompanyOrchestrator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_DIRECTORY = ROOT / "data/derived/portfolio_runs"
DEFAULT_WEB_DIRECTORY = ROOT / "piotw-web/data/portfolio-runs"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class FaultInjection(BaseModel):
    source_family: str
    state: Literal["FAILED"]
    reason: str


class PortfolioCompanyConfig(BaseModel):
    company_id: str
    aliases: list[str]
    active: bool = True
    thesis_context: str | None = None
    source_families: list[str]
    development_fault_injection: FaultInjection | None = None


class PortfolioConfig(BaseModel):
    schema_version: Literal["piotw-portfolio-configuration-v0.1"]
    portfolio_id: str
    portfolio_name: str
    mode: Literal["DEVELOPMENT_CUSTOMER_DEMO", "OPERATIONAL"]
    synthetic: bool
    thesis: str | None = None
    companies: list[PortfolioCompanyConfig]


class PortfolioRunResult(BaseModel):
    run_id: str
    portfolio_id: str
    as_of: datetime
    payload: dict[str, object]
    run_path: str | None = None
    web_path: str | None = None


class PortfolioOrchestrator:
    policy_version = "piotw-portfolio-attention-policy-v0.1"

    def __init__(self, *, company_orchestrator: UnknownCompanyOrchestrator | None = None,
                 run_directory: Path = DEFAULT_RUN_DIRECTORY, web_directory: Path = DEFAULT_WEB_DIRECTORY) -> None:
        self.company_orchestrator = company_orchestrator or UnknownCompanyOrchestrator()
        self.run_directory = run_directory
        self.web_directory = web_directory

    @staticmethod
    def load_config(path: str | Path) -> PortfolioConfig:
        return PortfolioConfig.model_validate_json(Path(path).read_text())

    @staticmethod
    def _capability_status(result: OrchestrationResult) -> str:
        statuses = [item.status for item in result.manifest.source_availability]
        if "FAILED" in statuses:
            return "INSUFFICIENT_EVIDENCE"
        if result.intelligence.conditions:
            return "AVAILABLE"
        return "INSUFFICIENT_EVIDENCE"

    @staticmethod
    def _attention_item(config: PortfolioCompanyConfig, result: OrchestrationResult) -> dict[str, object]:
        intelligence = result.intelligence
        failed_sources = [source.source_family for source in result.manifest.source_availability if source.status == "FAILED"]
        qualified = intelligence.conditions
        available_comparisons = [item for item in intelligence.comparisons if item.status == "AVAILABLE"]
        missing = list(dict.fromkeys([source.reason for source in result.manifest.source_availability if source.status != "AVAILABLE"] + intelligence.missing_capabilities))
        urgency = "THIS_WEEK" if qualified else "ROUTINE"
        if failed_sources:
            urgency = "VALIDATE_SOURCE"
        evidence_confidence = intelligence.overall_confidence
        materialities = [condition.materiality for condition in qualified]
        potential_materiality = "HIGH" if "HIGH" in materialities else "MEDIUM" if materialities else "WITHHELD"
        observed_change = qualified[0].statement if qualified else (f"Source collection failed for {', '.join(failed_sources)}." if failed_sources else "No newly qualified operational condition in available evidence.")
        validation_question = qualified[0].caveats[0] if qualified and qualified[0].caveats else ("Restore the failed source and confirm whether evidence changed." if failed_sources else "What internal evidence would confirm or contradict the currently sparse outside-in view?")
        priority_band = 0 if qualified and potential_materiality == "HIGH" else 1 if qualified else 2 if failed_sources else 3
        return {
            "attention_id": f"attention-{result.run_id}", "company_id": config.company_id,
            "company_name": intelligence.company.display_name, "attention_state": "INVESTIGATE" if qualified else "VALIDATE" if failed_sources else "MONITOR",
            "observed_change": observed_change, "direction": qualified[0].direction if qualified else "WITHHELD",
            "change_velocity": "WITHHELD", "potential_materiality": potential_materiality,
            "evidence_confidence": evidence_confidence, "urgency": urgency,
            "thesis_relevance": config.thesis_context or "UNKNOWN", "coverage": intelligence.coverage.model_dump(mode="json"),
            "missing_information": missing, "validation_question": validation_question,
            "capability_status": PortfolioOrchestrator._capability_status(result),
            "capabilities": intelligence.capabilities.model_dump(mode="json"),
            "evidence_ids": [item.evidence_id for item in intelligence.evidence],
            "comparison_ids": [item.comparison_id for item in available_comparisons],
            "company_brief_href": f"/intelligence/{config.company_id}/value",
            "ordering_factors": {"policy_version": PortfolioOrchestrator.policy_version, "priority_band": priority_band,
                "qualified_condition_present": bool(qualified), "source_failure_present": bool(failed_sources),
                "potential_materiality": potential_materiality, "evidence_confidence": evidence_confidence,
                "note": "Transparent lexicographic policy; this is not a validated score. Unknown is never treated as zero."},
        }

    @staticmethod
    def _changes(previous: dict[str, object] | None, current: list[dict[str, object]]) -> list[dict[str, object]]:
        if not previous:
            return [{"change_type": "INITIAL_BASELINE", "company_id": item["company_id"], "statement": "Initial portfolio baseline created; no prior run exists.", "evidence_ids": item["evidence_ids"]} for item in current]
        old = {item["company_id"]: item for item in previous.get("attention_items", [])}
        changes = []
        for item in current:
            before = old.get(item["company_id"])
            if not before:
                changes.append({"change_type": "COMPANY_ADDED", "company_id": item["company_id"], "statement": "Company entered active monitoring.", "evidence_ids": item["evidence_ids"]})
                continue
            checks = [("ATTENTION_STATE_CHANGED", "attention_state"), ("COVERAGE_CHANGED", "capability_status"), ("MISSING_INFORMATION_CHANGED", "missing_information")]
            for change_type, field in checks:
                if before.get(field) != item.get(field):
                    changes.append({"change_type": change_type, "company_id": item["company_id"], "statement": f"{field.replace('_', ' ').title()} changed since the previous run.", "evidence_ids": item["evidence_ids"]})
            new_evidence = sorted(set(item["evidence_ids"]) - set(before.get("evidence_ids", [])))
            if new_evidence:
                changes.append({"change_type": "NEW_FACTUAL_EVIDENCE", "company_id": item["company_id"], "statement": f"{len(new_evidence)} new evidence reference(s) became available.", "evidence_ids": new_evidence})
        return changes or [{"change_type": "NO_MEANINGFUL_CHANGE", "company_id": None, "statement": "No deterministic portfolio change was detected.", "evidence_ids": []}]

    def run(self, config: PortfolioConfig, *, as_of: datetime, previous: dict[str, object] | None = None) -> PortfolioRunResult:
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=UTC)
        company_results = []
        items = []
        evidence_dates: list[str] = []
        for company in [item for item in config.companies if item.active]:
            try:
                result = self.company_orchestrator.build(company=company.company_id, as_of=as_of)
                if company.development_fault_injection:
                    target = next((source for source in result.manifest.source_availability if source.source_family == company.development_fault_injection.source_family), None)
                    if target:
                        target.status = "FAILED"; target.health = "development_fault_injection"; target.reason = company.development_fault_injection.reason
                persisted = self.company_orchestrator.persist(result, publish_to_web=True)
                evidence_dates.extend(item.publication_date for item in persisted.intelligence.evidence)
                manifest_path = Path(persisted.manifest_path).relative_to(ROOT).as_posix() if persisted.manifest_path else None
                intelligence_path = Path(persisted.intelligence_path).relative_to(ROOT).as_posix() if persisted.intelligence_path else None
                company_results.append({"company_id": company.company_id, "run_id": persisted.run_id, "status": "COMPLETE", "manifest_path": manifest_path, "intelligence_path": intelligence_path, "source_health": [item.model_dump(mode="json") for item in persisted.manifest.source_availability]})
                items.append(self._attention_item(company, persisted))
            except Exception as error:
                company_results.append({"company_id": company.company_id, "run_id": None, "status": "FAILED_ISOLATED", "error_type": type(error).__name__, "source_health": []})
                items.append({"attention_id": f"attention-failed-{company.company_id}", "company_id": company.company_id, "company_name": company.company_id.replace("-", " ").title(), "attention_state": "VALIDATE", "observed_change": "Company run failed; no operational conclusion is available.", "direction": "WITHHELD", "change_velocity": "WITHHELD", "potential_materiality": "WITHHELD", "evidence_confidence": "NOT_ASSESSED", "urgency": "VALIDATE_SOURCE", "thesis_relevance": company.thesis_context or "UNKNOWN", "coverage": {"status": "INSUFFICIENT"}, "missing_information": ["Restore the company run and source evidence."], "validation_question": "What prevented the company run from completing?", "capability_status": "WITHHELD", "capabilities": {}, "evidence_ids": [], "comparison_ids": [], "company_brief_href": None, "ordering_factors": {"policy_version": self.policy_version, "priority_band": 2, "note": "Failed run isolated; unknown is not zero."}})
        items.sort(key=lambda item: (item["ordering_factors"]["priority_band"], str(item["company_name"])))
        for rank, item in enumerate(items, 1):
            item["rank"] = rank
        changes = self._changes(previous, items)
        config_hash = _digest(config.model_dump(mode="json"))
        run_material = {"portfolio_id": config.portfolio_id, "as_of": as_of.isoformat(), "config_hash": config_hash, "company_run_ids": [item["run_id"] for item in company_results]}
        run_id = f"portfolio-{config.portfolio_id}-{as_of.strftime('%Y%m%dT%H%M%SZ')}-{_digest(run_material)[:12]}"
        payload = {"schema_version": "piotw-portfolio-run-v0.1", "run_id": run_id, "portfolio_id": config.portfolio_id, "portfolio_name": config.portfolio_name, "mode": config.mode, "synthetic": config.synthetic, "as_of": as_of.isoformat(), "configuration_hash": config_hash, "policy_version": self.policy_version, "ordering_explanation": "Qualified high-materiality conditions first, then other qualified conditions, isolated source failures, then monitoring cases; ties are alphabetical. No hidden score.", "latest_successful_run": run_id, "latest_evidence_date": max(evidence_dates, default=None), "capability_status": "AVAILABLE" if any(item["capability_status"] == "AVAILABLE" for item in items) else "INSUFFICIENT_EVIDENCE", "company_runs": company_results, "attention_items": items, "changes": changes, "operating_review_brief": {"summary": f"{len(items)} active companies; {sum(item['urgency'] != 'ROUTINE' for item in items)} require validation or review.", "top_attention_changes": [item["observed_change"] for item in items[:3]], "newly_urgent_items": [item["company_id"] for item in items if item["urgency"] in {"THIS_WEEK", "VALIDATE_SOURCE"}], "newly_available_evidence": [change for change in changes if change["change_type"] == "NEW_FACTUAL_EVIDENCE"], "source_failures": [item["company_id"] for item in items if item["urgency"] == "VALIDATE_SOURCE"], "management_validation_questions": [item["validation_question"] for item in items[:3]], "evidence_links": [{"company_id": item["company_id"], "href": item["company_brief_href"]} for item in items if item["company_brief_href"]]}, "buyer_test": {"questions": ["Which three companies should receive attention?", "Why is the first company ranked first?", "What management action should happen next?", "Which claims are observed, inferred, hypothesised or withheld?", "Does this belong on the next operating-review agenda?"], "logging": "LOCAL_BROWSER_ONLY_NO_ANALYTICS_INFRASTRUCTURE"}, "scientific_gate_run": False}
        return PortfolioRunResult(run_id=run_id, portfolio_id=config.portfolio_id, as_of=as_of, payload=payload)

    def persist(self, result: PortfolioRunResult) -> PortfolioRunResult:
        path = self.run_directory / result.run_id
        path.mkdir(parents=True, exist_ok=True)
        run_file = path / "portfolio_run.json"
        run_file.write_text(json.dumps(result.payload, indent=2, sort_keys=True, default=str) + "\n")
        self.web_directory.mkdir(parents=True, exist_ok=True)
        web_file = self.web_directory / f"{result.portfolio_id}.json"
        web_file.write_text(run_file.read_text())
        return result.model_copy(update={"run_path": str(run_file), "web_path": str(web_file)})
