from __future__ import annotations

import re
from dataclasses import dataclass

from evidence_engine_v0_3_4.semantic import SemanticCandidate

FAMILY_BY_EVENT = {
    "restructuring": "restructuring_cost_action", "cost_reduction": "restructuring_cost_action",
    "efficiency_programme": "restructuring_cost_action", "simplification": "restructuring_cost_action",
    "redundancy": "workforce", "workforce_reduction": "workforce", "labour_constraint": "workforce",
    "hiring": "workforce", "skills_investment": "workforce",
    "site_closure": "delivery_capacity_sites", "footprint_reduction": "delivery_capacity_sites",
    "capacity_reduction": "delivery_capacity_sites", "capacity_mismatch": "delivery_capacity_sites",
    "capacity_expansion": "delivery_capacity_sites", "new_facility": "delivery_capacity_sites",
    "operational_disruption": "delivery_capacity_sites",
    "growth_language": "demand_growth", "demand_growth": "demand_growth",
    "demand_weakness": "demand_growth", "customer_weakness": "demand_growth",
    "order_book_strength": "demand_growth", "recovery_language": "demand_growth",
    "supply_chain_constraint": "supply_chain_resilience", "inflation_pressure": "supply_chain_resilience",
    "destocking": "supply_chain_resilience", "supplier_diversification": "supply_chain_resilience",
    "procurement_intervention": "supply_chain_resilience", "inventory_buffer": "supply_chain_resilience",
    "supplier_insolvency": "supply_chain_resilience", "sourcing_concentration": "supply_chain_resilience",
    "logistics_disruption": "supply_chain_resilience",
    "quality_failure": "quality_regulatory", "recall": "quality_regulatory",
    "regulatory_intervention": "quality_regulatory", "safety_issue": "quality_regulatory",
    "compliance_breach": "quality_regulatory", "warranty_issue": "quality_regulatory",
    "remediation_programme": "quality_regulatory", "regulatory_investigation": "quality_regulatory",
    "transformation": "leadership_change_execution", "leadership_change": "leadership_change_execution",
}


@dataclass(frozen=True)
class FamilyDecision:
    family: str
    disposition: str
    reason: str
    evidence_span: str


def route_family(event_type: str) -> str | None:
    return FAMILY_BY_EVENT.get(event_type)


def _target_relevant(candidate: SemanticCandidate) -> bool:
    return candidate.deterministic_metadata.get("subject_type") in {
        "target_company", "target_segment", "target_subsidiary"
    }


def _context_exclusion(family: str, candidate: SemanticCandidate) -> FamilyDecision | None:
    """Shared safety exclusions only; event sufficiency remains family-specific."""
    span = candidate.exact_candidate_span
    lower = span.lower()
    if not span.strip():
        return FamilyDecision(family, "reject", "missing_exact_provenance", span)
    if candidate.deterministic_metadata.get("heading_only") is True:
        return FamilyDecision(family, "reject", "heading_only", span)
    if candidate.deterministic_metadata.get("accounting_table_only") is True:
        return FamilyDecision(family, "reject", "accounting_table_only", span)
    if not _target_relevant(candidate):
        return FamilyDecision(family, "reject", "wrong_entity", span)
    if re.search(r"\b(?:no|not|without|did not|has not|have not|no plans? to)\b.{0,45}", lower):
        return FamilyDecision(family, "reject", "negated_event", span)
    if re.search(
        r"\b(?:risk of|could|might|possibility of|if we|were we to|failure to|future .* depends?)\b",
        lower,
    ) and not re.search(
        r"\b(?:announced|implemented|experienced|affected|impacted|occurred|continued)\b", lower
    ):
        return FamilyDecision(family, "reject", "hypothetical_only", span)
    if re.search(r"\b(?:in the past|at various times in the past|historically)\b", lower) and not re.search(
        r"\b(?:currently|ongoing|continues?|this (?:year|quarter|period)|now)\b", lower
    ):
        return FamilyDecision(family, "reject", "historical_only", span)
    if re.search(r"\b(?:formerly|in 20\d\d|last year|previously)\b", lower) and re.search(
        r"\b(?:complete|completed|concluded|ended|former|previous)\b", lower
    ):
        return FamilyDecision(family, "reject", "historical_only", span)
    return None


def _decision(family: str, candidate: SemanticCandidate, supported: bool, accept_reason: str,
              ambiguous_reason: str) -> FamilyDecision:
    return FamilyDecision(family, "accept" if supported else "ambiguous",
                          accept_reason if supported else ambiguous_reason,
                          candidate.exact_candidate_span)


class DemandGrowthFamilyVerifier:
    family = "demand_growth"

    def verify(self, candidate: SemanticCandidate) -> FamilyDecision:
        excluded = _context_exclusion(self.family, candidate)
        if excluded:
            return excluded
        lower = candidate.exact_candidate_span.lower()
        if re.search(r"\b(?:cost|costs|expense|expenses)\b.{0,45}\b(?:increased|grew|growth)\b", lower):
            return FamilyDecision(self.family, "reject", "expense_growth_is_not_demand_growth",
                                  candidate.exact_candidate_span)
        if re.search(r"\b(?:increased|grew)\b.{0,45}\b(?:cost|costs|expense|expenses)\b", lower):
            return FamilyDecision(self.family, "reject", "expense_growth_is_not_demand_growth",
                                  candidate.exact_candidate_span)
        if re.search(r"\b(?:strategy|aim|goal|need to|seek to|future success)\b", lower) and not re.search(
            r"\b(?:revenue|sales|orders?|backlog|demand|volume)\b.{0,50}\b(?:increased|grew|declined|decreased)\b", lower
        ):
            return FamilyDecision(self.family, "reject", "aspiration_not_observed_change",
                                  candidate.exact_candidate_span)
        if re.search(r"\bbacklog\b.{0,80}\b(?:key .*measure|forward-looking|focus on)\b", lower):
            return FamilyDecision(self.family, "reject", "metric_description_not_observed_change",
                                  candidate.exact_candidate_span)
        factual = bool(re.search(
            r"\b(?:revenue|sales|orders?|backlog|demand|unit sales|volume)\b.{0,100}"
            r"\b(?:increased|grew|growth|declined|decreased|fell|weakness|softened|strong|record)\b", lower
        ) or re.search(
            r"\b(?:increased|grew|declined|decreased|fell)\b.{0,100}"
            r"\b(?:revenue|sales|orders?|backlog|demand|volume)\b", lower
        ))
        return _decision(self.family, candidate, factual, "direct_demand_change", "demand_change_not_entailed")


class RestructuringCostActionFamilyVerifier:
    family = "restructuring_cost_action"

    def verify(self, candidate: SemanticCandidate) -> FamilyDecision:
        excluded = _context_exclusion(self.family, candidate)
        if excluded:
            return excluded
        lower = candidate.exact_candidate_span.lower()
        if re.search(r"\b(?:costs?|expenses?)\b.{0,45}\b(?:increased|rose|grew)\b", lower) and not re.search(
            r"\b(?:reduce|reduction|saving|restructur|efficien|simplif)\w*\b", lower
        ):
            return FamilyDecision(self.family, "reject", "cost_increase_is_not_cost_action",
                                  candidate.exact_candidate_span)
        if "cost reduction initiative" in lower and not re.search(
            r"\b(?:implemented|initiated|announced|pursue|launched|undertook|executing)\b", lower
        ):
            return FamilyDecision(self.family, "reject", "programme_or_product_name_only",
                                  candidate.exact_candidate_span)
        if re.search(
            r"\b(?:our )?(?:customer|customers|supplier|suppliers|competitor|competitors)\b"
            r".{0,100}\b(?:entered|announced|implemented|initiated|restructur|cost reduc|efficien)", lower
        ):
            return FamilyDecision(self.family, "reject", "third_party_action", candidate.exact_candidate_span)
        if re.search(r"\b(?:from time to time|may|could|risk of)\b", lower) and not re.search(
            r"\b(?:announced|implemented|initiated|incurred|recognized|recognised|approved|committed)\b", lower
        ):
            return FamilyDecision(self.family, "reject", "generic_or_hypothetical_action",
                                  candidate.exact_candidate_span)
        identity = re.search(
            r"\b(?:restructur|cost[- ]reduc|cost-saving|efficien|simplif|footprint optimi[sz]|"
            r"operating.model redesign|structural cost|consolidat|organi[sz]ational redesign|"
            r"workforce reshap|productivity initiative|productivity programme|productivity program)\w*\b", lower)
        action = re.search(
            r"\b(?:announced|implemented|initiated|pursue|pursuing|incurred|recognized|recognised|ongoing|"
            r"launched|undertook|executing|approved|committed|completed|began|closed|actions? to|"
            r"programme is|program is|are redesigning|is redesigning|implements?|implementing|continues? on)\b", lower
        )
        indirect = re.search(
            r"\b(?:eliminat(?:e|ed|ing) positions|consolidat(?:e|ed|ing) (?:sites|operations)|"
            r"reduce(?:d|ing)? (?:headcount|the cost base)|workforce reductions?)\b", lower
        )
        active_plan_evidence = bool(re.search(
            r"\b(?:our |the )?restructuring (?:accrual|liability|plan)\b", lower
        ) and re.search(
            r"\b(?:at|as of|expected to (?:be paid|impact)|fiscal 20\d\d plan|charges?|cash payments?)\b",
            lower,
        ))
        accounting_only = re.search(r"\b(?:provision|accounting policy|definition|defined as)\b", lower) and not (
            action or active_plan_evidence
        )
        if accounting_only:
            return FamilyDecision(self.family, "ambiguous", "accounting_reference_without_action",
                                  candidate.exact_candidate_span)
        return _decision(self.family, candidate, bool((identity and action) or indirect or active_plan_evidence),
                         "direct_or_indirect_target_action", "action_identity_not_entailed")


class WorkforceFamilyVerifier:
    family = "workforce"

    def verify(self, candidate: SemanticCandidate) -> FamilyDecision:
        excluded = _context_exclusion(self.family, candidate)
        if excluded:
            return excluded
        lower, event = candidate.exact_candidate_span.lower(), candidate.candidate_event_type
        if event in {"redundancy", "workforce_reduction"}:
            supported = bool(re.search(
                r"\b(?:announced|began|completed|plans? to|will|consultation|reduced|reducing|eliminated)\b"
                r".{0,100}\b(?:redundan|workforce|headcount|positions?|roles?)\b|"
                r"\b(?:redundan|workforce reductions?|headcount reduction)\b.{0,80}"
                r"\b(?:announced|began|completed|planned|initiated|ongoing)\b",
                lower,
            ))
        elif event in {"hiring", "skills_investment"}:
            supported = bool(re.search(
                r"\b(?:we|company|group|segment)\b.{0,80}\b(?:hiring|recruiting|recruited|training|skills investment)\b|"
                r"\b(?:hiring|recruiting|recruited)\b.{0,80}\b(?:employees|engineers|staff|roles?)\b", lower
            ))
        else:
            supported = bool(re.search(
                r"\b(?:labou?r shortage|staff shortage|strike|employee turnover|workforce availability)\b"
                r".{0,100}\b(?:affected|impacted|constrained|disrupted|operations?|production)?", lower
            ))
        return _decision(self.family, candidate, supported, "direct_workforce_event", "workforce_event_not_entailed")


class DeliveryCapacitySitesFamilyVerifier:
    family = "delivery_capacity_sites"

    def verify(self, candidate: SemanticCandidate) -> FamilyDecision:
        excluded = _context_exclusion(self.family, candidate)
        if excluded:
            return excluded
        lower, event = candidate.exact_candidate_span.lower(), candidate.candidate_event_type
        patterns = {
            "site_closure": r"\b(?:closed|closing|will close|permanently shut|permanent shutdown|announced.{0,30}closure)\b.{0,70}\b(?:sites?|plants?|factor(?:y|ies)|facilit(?:y|ies))\b|\b(?:site|plant|factory|facility) closures?\b.{0,70}\b(?:resulting|implemented|announced|related actions?)\b|\bsite closure\b.{0,50}\b(?:announced|implemented|completed)\b",
            "footprint_reduction": r"\b(?:reduc|consolidat)\w*.{0,45}\b(?:footprint|sites|facilities|locations)\b",
            "capacity_reduction": r"\b(?:reduc|cut|removed)\w*.{0,45}\bcapacity\b|\bcapacity reduction\b",
            "capacity_mismatch": r"\b(?:excess|underutili[sz]ed|unused)\b.{0,35}\bcapacity\b",
            "capacity_expansion": r"\b(?:expanded|expanding|added|adding|will add|will increase|increased|commissioned)\w*.{0,70}\b(?:capacity|warehouse|facility|plant|production line|new line)\b|\b(?:capacity expansion|new production line)\b.{0,60}\b(?:announced|opened|commissioned|planned)\b",
            "new_facility": r"\b(?:opened|opening|built|building|constructing|commissioned)\b.{0,70}\b(?:new )?(?:facility|site|plant|factory|warehouse|distribution centre|distribution center)\b",
            "operational_disruption": r"\b(?:production|operations?|delivery|site|plant)\b.{0,60}\b(?:paused|halted|disrupted|interrupted|suspended|temporarily shut|temporary shutdown)\b|\b(?:operational disruption|temporary shutdown)\b.{0,60}\b(?:occurred|began|continued|during)\b",
        }
        return _decision(self.family, candidate, bool(re.search(patterns.get(event, r"(?!x)x"), lower)),
                         "direct_capacity_or_delivery_event", "capacity_or_delivery_event_not_entailed")


class SupplyChainResilienceFamilyVerifier:
    family = "supply_chain_resilience"

    def verify(self, candidate: SemanticCandidate) -> FamilyDecision:
        excluded = _context_exclusion(self.family, candidate)
        if excluded:
            return excluded
        lower, event = candidate.exact_candidate_span.lower(), candidate.candidate_event_type
        patterns = {
            "supplier_diversification": r"\b(?:we|group|company)\b.{0,80}\b(?:added|approved|qualified|diversified)\b.{0,60}\b(?:supplier|source|sourcing)\b",
            "procurement_intervention": r"\b(?:we|group|company)\b.{0,80}\b(?:launched|implemented|centralised|centralized)\b.{0,60}\bprocurement\b",
            "inventory_buffer": r"\b(?:we|group|company)\b.{0,80}\b(?:built|increased|established)\b.{0,60}\b(?:inventory|safety stock|buffer stock)\b",
            "supplier_insolvency": r"\b(?:supplier|vendor)\b.{0,60}\b(?:insolven|bankrupt|administration)\w*\b.{0,100}\b(?:affected|delayed|disrupted|our)\b",
            "sourcing_concentration": r"\b(?:we|group|company)\b.{0,80}\b(?:depends? on (?:a |one )?supplier|single.source|sole supplier|concentrated sourcing)\b",
            "logistics_disruption": r"\b(?:our|company|group)\b.{0,80}\b(?:shipments?|deliveries|logistics)\b.{0,70}\b(?:delayed|disrupted|interrupted)\b",
        }
        continuing_constraint = bool(re.search(
            r"\bthese included ongoing supply chain disruptions?\b|"
            r"\b(?:ongoing |global )?supply chain disruptions?\b.{0,120}"
            r"\b(?:included|have impacted|has impacted|impacted|continue|mitigated|procure|delays?|increased costs?)\b|"
            r"\b(?:implemented actions|implemented certain actions)\b.{0,100}"
            r"\bsupply chain disruptions?\b.{0,50}\bcontinue\b",
            lower,
        ))
        actual = bool(re.search(patterns.get(event,
            r"\b(?:we|our|company|group|operations?|production|deliveries)\b.{0,100}"
            r"\b(?:experienced|affected|impacted|constrained|disrupted|shortage|destocking|cost inflation)\b|"
            r"\b(?:supply chain disruption|component shortages?|material shortages?|commodity shortages?|destocking|cost inflation)\b"
            r".{0,100}\b(?:affected|impacted|reduced|delayed|continued|during)\b"), lower) or continuing_constraint)
        return _decision(self.family, candidate, actual, "direct_supply_condition", "supply_condition_not_entailed")


class QualityRegulatoryFamilyVerifier:
    family = "quality_regulatory"

    def verify(self, candidate: SemanticCandidate) -> FamilyDecision:
        excluded = _context_exclusion(self.family, candidate)
        if excluded:
            return excluded
        lower, event = candidate.exact_candidate_span.lower(), candidate.candidate_event_type
        if event == "recall":
            supported = bool(re.search(r"\b(?:we|company|group)\b.{0,80}\b(?:recalled|initiated a recall|issued a recall)\b|\bproduct recall\b.{0,60}\b(?:initiated|announced|during)\b", lower))
        elif event in {"regulatory_intervention", "regulatory_investigation"}:
            supported = bool(re.search(r"\b(?:regulator|authority|agency)\b.{0,90}\b(?:ordered|restricted|suspended|fined|enforcement)\b", lower))
            if event == "regulatory_investigation":
                supported = bool(re.search(r"\b(?:regulator|authority|agency)\b.{0,90}\b(?:opened|launched|commenced|is conducting)\b.{0,60}\binvestigation\b", lower))
        elif event == "safety_issue":
            supported = bool(re.search(r"\b(?:safety incident|safety issue|injury)\b.{0,90}\b(?:occurred|resulted|caused|required)\b", lower))
        elif event == "compliance_breach":
            supported = bool(re.search(r"\b(?:breached|violated|non-compliance|noncompliance)\b.{0,90}\b(?:requirement|regulation|permit|standard)\b", lower))
        elif event == "warranty_issue":
            supported = bool(re.search(r"\b(?:warranty claims?|warranty costs?)\b.{0,90}\b(?:increased|rose|required|resulted)\b", lower))
        elif event == "remediation_programme":
            supported = bool(re.search(r"\b(?:launched|implemented|initiated|began)\b.{0,80}\b(?:remediation|corrective action)\b", lower))
        else:
            supported = bool(re.search(r"\b(?:defect|quality failure|nonconformance|quality issue)\w*\b.{0,90}\b(?:affected|caused|resulted|required|during)\b", lower))
        return _decision(self.family, candidate, supported, "direct_quality_or_regulatory_event",
                         "quality_or_regulatory_event_not_entailed")


class LeadershipChangeExecutionFamilyVerifier:
    family = "leadership_change_execution"

    def verify(self, candidate: SemanticCandidate) -> FamilyDecision:
        excluded = _context_exclusion(self.family, candidate)
        if excluded:
            return excluded
        lower = candidate.exact_candidate_span.lower()
        if re.search(r"\b(?:biography|previous employer|prior to joining|formerly served)\b", lower):
            return FamilyDecision(self.family, "reject", "biography_or_prior_employer",
                                  candidate.exact_candidate_span)
        if candidate.candidate_event_type == "leadership_change":
            supported = bool(re.search(
                r"\b(?:appointed|named|resigned|stepped down|departed|will join|succeeded)\b.{0,75}"
                r"\b(?:chief|ceo|cfo|coo|president|director|officer|chair)\b|"
                r"\b(?:chief|ceo|cfo|coo|president|director|officer|chair)\b.{0,75}"
                r"\b(?:appointed|resigned|stepped down|departed)\b", lower
            ))
        else:
            supported = bool(re.search(
                r"\b(?:launched|initiated|implemented|executing|underway|ongoing)\b.{0,100}"
                r"\b(?:transformation|change programme|change program)\b|"
                r"\b(?:transformation|change programme|change program)\b.{0,100}"
                r"\b(?:launched|initiated|implemented|underway|ongoing|continue|deployed)\b|"
                r"\b(?:continue on|continuing|multi-year)\b.{0,100}\b(?:transformation|change) initiative\b",
                lower,
            ))
        return _decision(self.family, candidate, supported, "direct_change_execution_event",
                         "change_execution_event_not_entailed")


FAMILY_VERIFIERS = {
    "demand_growth": DemandGrowthFamilyVerifier(),
    "restructuring_cost_action": RestructuringCostActionFamilyVerifier(),
    "workforce": WorkforceFamilyVerifier(),
    "delivery_capacity_sites": DeliveryCapacitySitesFamilyVerifier(),
    "supply_chain_resilience": SupplyChainResilienceFamilyVerifier(),
    "quality_regulatory": QualityRegulatoryFamilyVerifier(),
    "leadership_change_execution": LeadershipChangeExecutionFamilyVerifier(),
}


def verify_candidate(candidate: SemanticCandidate) -> FamilyDecision:
    family = route_family(candidate.candidate_event_type)
    if family not in FAMILY_VERIFIERS:
        return FamilyDecision(family or "unrouted", "ambiguous", "family_not_implemented",
                              candidate.exact_candidate_span)
    return FAMILY_VERIFIERS[family].verify(candidate)
