"""CRM stage classification is pure/offline — lock won/lost/open logic + 'where opps sit'."""
from gtmsi.crm import classify_hubspot_pipelines, classify_salesforce_stages


def test_salesforce_classification_and_distribution():
    rows = [
        {"MasterLabel": "Prospecting", "IsClosed": False, "IsWon": False, "SortOrder": 1},
        {"MasterLabel": "Negotiation", "IsClosed": False, "IsWon": False, "SortOrder": 4},
        {"MasterLabel": "Closed Won", "IsClosed": True, "IsWon": True, "SortOrder": 6},
        {"MasterLabel": "Closed Lost", "IsClosed": True, "IsWon": False, "SortOrder": 7},
    ]
    dist = [
        {"StageName": "Prospecting", "cnt": 38, "amt": 1_240_000},
        {"StageName": "Negotiation", "cnt": 9, "amt": 1_650_000},
    ]
    r = classify_salesforce_stages(rows, dist)
    assert r.won == ["Closed Won"]
    assert r.lost == ["Closed Lost"]
    assert r.open == ["Prospecting", "Negotiation"]
    busiest = r.busiest_open_stages()
    assert busiest[0].label == "Prospecting" and busiest[0].open_count == 38


def test_salesforce_custom_stage_labels():
    # Org renamed its stages — classification must rely on flags, not the label text.
    rows = [
        {"MasterLabel": "7. Signed", "IsClosed": True, "IsWon": True, "SortOrder": 7},
        {"MasterLabel": "Dead", "IsClosed": True, "IsWon": False, "SortOrder": 8},
        {"MasterLabel": "Discovery", "IsClosed": False, "IsWon": False, "SortOrder": 1},
    ]
    r = classify_salesforce_stages(rows)
    assert r.won == ["7. Signed"]
    assert r.lost == ["Dead"]
    assert r.open == ["Discovery"]


def test_hubspot_classification_string_metadata():
    # HubSpot returns isClosed/probability as STRINGS.
    pipelines = [
        {"label": "Sales Pipeline", "stages": [
            {"id": "appointmentscheduled", "label": "Appointment Scheduled", "displayOrder": 0,
             "metadata": {"isClosed": "false", "probability": "0.2"}},
            {"id": "closedwon", "label": "Closed Won", "displayOrder": 5,
             "metadata": {"isClosed": "true", "probability": "1.0"}},
            {"id": "closedlost", "label": "Closed Lost", "displayOrder": 6,
             "metadata": {"isClosed": "true", "probability": "0.0"}},
        ]},
    ]
    r = classify_hubspot_pipelines(pipelines, stage_counts={"appointmentscheduled": 12})
    assert r.won == ["Closed Won"]
    assert r.lost == ["Closed Lost"]
    assert r.open == ["Appointment Scheduled"]
    assert r.busiest_open_stages()[0].open_count == 12


def test_hubspot_open_stage_with_zero_probability_is_not_lost():
    # Regression: an OPEN early-funnel stage commonly has probability "0.0".
    # isClosed=false is authoritative — it must be Open, never Closed-Lost.
    pipelines = [{"label": "Sales", "stages": [
        {"id": "lead", "label": "Lead", "metadata": {"isClosed": "false", "probability": "0.0"}},
        {"id": "won", "label": "Won", "metadata": {"isClosed": "true", "probability": "1.0"}},
        {"id": "lost", "label": "Lost", "metadata": {"isClosed": "true", "probability": "0.0"}},
    ]}]
    r = classify_hubspot_pipelines(pipelines)
    assert "Lead" in r.open
    assert "Lead" not in r.lost
    assert r.won == ["Won"] and r.lost == ["Lost"]
