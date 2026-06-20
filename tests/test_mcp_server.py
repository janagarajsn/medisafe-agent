"""Tests for MCP server tool functions (called directly, not via MCP protocol)."""

import ast

import pytest

from src.mcp_server.server import (
    mcp_add_medication,
    mcp_check_drug_interactions,
    mcp_get_adherence_report,
    mcp_get_drug_info,
    mcp_list_medications,
    mcp_mark_dose_taken,
    mcp_remove_medication,
    mcp_skip_dose,
)


def _parse(result: str) -> dict:
    """Parse the stringified dict returned by MCP tool functions."""
    return ast.literal_eval(result)


# ── mcp_add_medication ────────────────────────────────────────────────────────

def test_mcp_add_success():
    result = _parse(mcp_add_medication("mcp_u1", "Omeprazole", "20mg", "daily"))
    assert result["success"] is True
    assert "medication_id" in result


def test_mcp_add_empty_name_error():
    result = _parse(mcp_add_medication("mcp_u1", "", "20mg", "daily"))
    assert result["success"] is False


# ── mcp_list_medications ──────────────────────────────────────────────────────

def test_mcp_list_empty():
    result = _parse(mcp_list_medications("nobody"))
    assert result["medications"] == []


def test_mcp_list_after_add():
    mcp_add_medication("mcp_u2", "Vitamin B12", "500mcg", "daily")
    result = _parse(mcp_list_medications("mcp_u2"))
    assert result["count"] == 1
    assert result["medications"][0]["name"] == "Vitamin B12"


# ── mcp_mark_dose_taken / mcp_skip_dose ──────────────────────────────────────

def test_mcp_mark_dose_taken():
    add_result = _parse(mcp_add_medication("mcp_u3", "Metformin", "500mg", "twice daily"))
    med_id = add_result["medication_id"]
    result = _parse(mcp_mark_dose_taken("mcp_u3", med_id, "08:00"))
    assert result["success"] is True


def test_mcp_skip_dose():
    add_result = _parse(mcp_add_medication("mcp_u3", "Aspirin", "81mg", "daily"))
    med_id = add_result["medication_id"]
    result = _parse(mcp_skip_dose("mcp_u3", med_id, "08:00"))
    assert result["success"] is True


# ── mcp_remove_medication ─────────────────────────────────────────────────────

def test_mcp_remove_existing():
    add_result = _parse(mcp_add_medication("mcp_u4", "Zinc", "50mg", "daily"))
    med_id = add_result["medication_id"]
    result = _parse(mcp_remove_medication("mcp_u4", med_id))
    assert result["success"] is True
    assert _parse(mcp_list_medications("mcp_u4"))["count"] == 0


def test_mcp_remove_nonexistent():
    result = _parse(mcp_remove_medication("mcp_u4", 99999))
    assert result["success"] is False


# ── mcp_get_adherence_report ──────────────────────────────────────────────────

def test_mcp_adherence_no_records():
    result = _parse(mcp_get_adherence_report("nobody", 7))
    assert result["report"] == []


# ── mcp_check_drug_interactions (mocked) ──────────────────────────────────────

def test_mcp_check_interactions_network_error():
    from unittest.mock import patch
    with patch("requests.get", side_effect=Exception("Network error")):
        result = _parse(mcp_check_drug_interactions("X", "Y"))
    assert result["checked"] is False


# ── mcp_get_drug_info (mocked) ────────────────────────────────────────────────

def test_mcp_get_drug_info_not_found():
    from unittest.mock import MagicMock, patch
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch("requests.get", return_value=mock_resp):
        result = _parse(mcp_get_drug_info("FakeDrug999"))
    assert result["found"] is False
