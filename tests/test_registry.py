"""The knowledge base must always be internally consistent."""
from dealtrace.registry import load_registry


def test_registry_loads():
    reg = load_registry()
    assert reg.call_types, "no call types loaded"
    assert reg.scorecards, "no scorecards loaded"
    assert reg.frameworks, "no frameworks loaded"
    assert reg.outcomes, "no outcomes loaded"


def test_registry_is_valid():
    reg = load_registry()
    problems = reg.validate()
    assert problems == [], "knowledge base integrity problems:\n" + "\n".join(problems)


def test_every_call_type_resolves_a_scorecard():
    reg = load_registry()
    for ct in reg.call_types.values():
        assert reg.scorecard_for(ct.id) is not None, f"{ct.id} has no scorecard"


def test_scorecard_weights_positive():
    reg = load_registry()
    for sc in reg.scorecards.values():
        assert sc.criteria, f"{sc.id} has no criteria"
        assert all(c.weight > 0 for c in sc.criteria), f"{sc.id} has non-positive weight"


def test_band_for_monotonic():
    reg = load_registry()
    sc = reg.scorecards["discovery"]
    assert sc.band_for(95) == "great"
    assert sc.band_for(70) == "good"
    assert sc.band_for(45) == "developing"
    assert sc.band_for(10) == "poor"
