from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = ("review_returns", "ai_development_truth", "canonical_truth", "pre_truth", "review_packs")
ALLOWED_ROOTS = (
    "piotw-web/", ".github/workflows/pages.yml", ".github/workflows/operational-portfolio.yml",
    "config/comparison/", "config/conditions/", "config/evidence/multi_source_records_v0_1.json",
    "config/piotw_comparison_v0_1.schema.json", "config/portfolios/",
    "docs/piotw-operational-portfolio-runbook-v0.1.md", "piotw_compare/", "piotw_conditions/",
    "piotw_evidence/", "piotw_intelligence/company_intelligence_v01.py", "piotw_orchestrator/",
    "scripts/run_operational_portfolio_v01.py", "scripts/verify_public_deployment_boundary.py",
    "tests/test_company_intelligence_v01.py", "tests/test_portfolio_orchestration_v01.py",
)


def main(paths: list[str]) -> int:
    violations = [path for path in paths if not any(path == root or path.startswith(root) for root in ALLOWED_ROOTS)]
    violations += [path for path in paths if any(part in path.lower() for part in BLOCKED)]
    if violations:
        print("Public deployment boundary rejected:")
        print("\n".join(sorted(set(violations))))
        return 1
    print(f"Public deployment boundary accepted for {len(paths)} path(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
