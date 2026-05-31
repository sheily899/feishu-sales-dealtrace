"""Vendor-neutral CRM writeback: map any GTM Superintelligence report to any CRM's fields, then
write with a pluggable writer (dry-run by default)."""
from .mapping import CRMUpdate, build_crm_patch, resolve_path
from .stages import (
    ResolvedStages,
    StageInfo,
    classify_hubspot_pipelines,
    classify_salesforce_stages,
    fetch_hubspot_stages,
    fetch_salesforce_stages,
)
from .writers import DryRunWriter, HubSpotWriter, SalesforceWriter, get_writer

__all__ = [
    "CRMUpdate",
    "build_crm_patch",
    "resolve_path",
    "DryRunWriter",
    "SalesforceWriter",
    "HubSpotWriter",
    "get_writer",
    "ResolvedStages",
    "StageInfo",
    "classify_salesforce_stages",
    "classify_hubspot_pipelines",
    "fetch_salesforce_stages",
    "fetch_hubspot_stages",
]
