from validation.adjudication import (
    agreement_report,
    deduplicate_candidate_events,
    listed_parent_for_event,
)


def test_duplicate_event_disclosures_count_once():
    event = {"parent_entity": "Parent plc", "affected_entity": "Division Ltd",
             "public_date": "2023-02-01", "event_description": "Plant closure programme"}
    assert len(deduplicate_candidate_events([event, dict(event)])) == 1


def test_subsidiary_event_maps_to_frozen_listed_parent():
    event = {"parent_entity": "Parent plc", "affected_entity": "Division Ltd",
             "public_date": "2023-02-01", "event_description": "Programme"}
    assert listed_parent_for_event(event, {"division ltd": "Parent plc"}) == "Parent plc"


def test_agreement_preserves_disagreements():
    first = [{"occasion_id": "a", "adjudication": "positive"},
             {"occasion_id": "b", "adjudication": "negative"}]
    second = [{"occasion_id": "a", "adjudication": "positive"},
              {"occasion_id": "b", "adjudication": "uncertain"}]
    report = agreement_report(first, second)
    assert report["raw_agreement"] == 0.5
    assert report["disagreements"] == [
        {"occasion_id": "b", "reviewer_1": "negative", "reviewer_2": "uncertain"}]
