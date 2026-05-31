"""CRM mapping is pure/offline — lock path resolution, transforms, and patch build."""
from gtmsi.crm import build_crm_patch, get_writer, resolve_path
from gtmsi.crm.writers import DryRunWriter, HubSpotWriter, SalesforceWriter
from gtmsi.registry import load_registry


def test_writer_endpoints_match_verified_docs():
    sf = get_writer("salesforce", instance_url="https://acme.my.salesforce.com", access_token="t")
    assert isinstance(sf, SalesforceWriter)
    # Verified: PATCH/POST {instance_url}/services/data/vXX.X/sobjects/<Object>/<Id>
    assert sf.base == "https://acme.my.salesforce.com/services/data/v60.0/sobjects"
    hs = get_writer("hubspot", access_token="t")
    assert isinstance(hs, HubSpotWriter)
    assert hs.base == "https://api.hubapi.com/crm/v3/objects"
    assert isinstance(get_writer("dry-run"), DryRunWriter)


def test_resolve_path_nested_and_list_by_id():
    report = {
        "overall_score": 71.4,
        "classification": {"call_type": "discovery"},
        "dimensions": [
            {"dimension_id": "champion", "rationale": "strong champion"},
            {"dimension_id": "economic_buyer", "rationale": "EB not engaged"},
        ],
        "coaching": {"next_call_focus": ["book a meeting", "send ROI"]},
    }
    assert resolve_path(report, "overall_score") == 71.4
    assert resolve_path(report, "classification.call_type") == "discovery"
    assert resolve_path(report, "dimensions.economic_buyer.rationale") == "EB not engaged"
    assert resolve_path(report, "coaching.next_call_focus") == ["book a meeting", "send ROI"]


def test_generic_mapping_builds_patch_with_transforms():
    reg = load_registry()
    mapping = reg.crm_mapping("generic")
    coaching_report = {
        "classification": {"call_type": "discovery"},
        "overall_score": 71.4,
        "summary": "Strong discovery, weak close.",
        "coaching": {"next_call_focus": ["Book a meeting", "Send ROI"]},
        "metadata": {"activity_id": "00T123"},
    }
    updates = build_crm_patch(mapping, {"coaching_report": coaching_report})
    assert updates, "no updates produced"
    u = updates[0]
    assert u.crm == "generic"
    assert u.record_id == "00T123"
    # round transform on overall_score
    assert u.fields["call_score"] == 71
    # title_case transform on call_type
    assert u.fields["call_type"] == "Discovery"
    # join_lines transform on the list
    assert "- Book a meeting" in u.fields["next_steps"]


def test_resolve_path_numeric_index_and_missing():
    report = {"risks": [{"title": "A"}, {"title": "B"}]}
    assert resolve_path(report, "risks.0.title") == "A"
    assert resolve_path(report, "risks.5.title") is None  # out of range -> None
    assert resolve_path(report, "nope.deep") is None


def test_transforms_percent_and_skip_when_empty():
    from gtmsi.crm.mapping import _apply_transform, build_crm_patch

    assert _apply_transform(0.72, "percent") == "72%"
    assert _apply_transform(71.6, "round") == 72
    assert _apply_transform(None, "round") is None
    # when_empty: skip means a missing field is omitted entirely.
    mapping = {
        "crm": "x",
        "objects": [
            {"source": "coaching_report", "object": "O", "id_field": "metadata.id",
             "fields": [
                 {"crm_field": "present", "from": "overall_score", "transform": "round"},
                 {"crm_field": "absent", "from": "does.not.exist", "when_empty": "skip"},
             ]}
        ],
    }
    updates = build_crm_patch(mapping, {"coaching_report": {"overall_score": 80, "metadata": {"id": "1"}}})
    assert updates[0].fields == {"present": 80}


def test_deal_report_maps_to_opportunity():
    reg = load_registry()
    mapping = reg.crm_mapping("salesforce")
    deal_report = {
        "kind": "deal-health",
        "subject": {"id": "006XXICEBERG", "name": "Acme"},
        "overall_score": 58,
        "band": "promising",
        "risk": "medium",
        "summary": "Mid-stage, single-threaded.",
        "risks": [{"title": "Single-threaded", "severity": "high"}],
        "recommended_actions": [{"action": "Multi-thread to Finance"}],
        "dimensions": [{"dimension_id": "champion", "rationale": "ok champion"}],
    }
    updates = build_crm_patch(mapping, {"deal_report": deal_report})
    opp = next(u for u in updates if u.object == "Opportunity")
    assert opp.record_id == "006XXICEBERG"
    assert opp.fields["GTMSI_Deal_Health__c"] == 58
    assert opp.fields["GTMSI_Deal_Risk__c"] == "Medium"
    assert "Single-threaded" in opp.fields["GTMSI_Top_Risks__c"]
