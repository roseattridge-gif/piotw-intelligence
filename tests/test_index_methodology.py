from scripts.validate_index_methodology import validate


def test_index_methodology_registries_are_internally_consistent() -> None:
    result = validate()
    assert result["methodology_version"] == "0.1.0"
    assert result["dimensions"] == 6
    assert result["features"] >= 30

