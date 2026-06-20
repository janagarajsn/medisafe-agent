"""Tests for OpenFDA drug interaction and info tools."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.interaction_tools import check_drug_interactions, get_drug_info


def _mock_response(status_code: int, json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


# ── check_drug_interactions ───────────────────────────────────────────────────

class TestCheckDrugInteractions:
    def test_interaction_found(self):
        payload = {
            "results": [
                {
                    "drug_interactions": ["Aspirin may enhance the anticoagulant effect of Warfarin."],
                    "openfda": {"brand_name": ["Bayer Aspirin"]},
                }
            ]
        }
        with patch("requests.get", return_value=_mock_response(200, payload)):
            result = check_drug_interactions("Aspirin", "Warfarin")
        assert result["interactions_found"] is True
        assert result["count"] >= 1
        assert "warning" in result

    def test_no_interaction_found(self):
        payload = {
            "results": [
                {
                    "drug_interactions": ["May interact with ibuprofen."],
                    "openfda": {},
                }
            ]
        }
        with patch("requests.get", return_value=_mock_response(200, payload)):
            result = check_drug_interactions("Aspirin", "Lisinopril")
        assert result["interactions_found"] is False
        assert "disclaimer" in result

    def test_api_returns_non_200(self):
        with patch("requests.get", return_value=_mock_response(500, {})):
            result = check_drug_interactions("DrugA", "DrugB")
        assert result["interactions_found"] is False

    def test_network_exception(self):
        with patch("requests.get", side_effect=Exception("Network error")):
            result = check_drug_interactions("X", "Y")
        assert result["checked"] is False
        assert "error" in result["message"].lower()

    def test_timeout(self):
        import requests as req
        with patch("requests.get", side_effect=req.Timeout):
            result = check_drug_interactions("X", "Y")
        assert result["checked"] is False
        assert "timed out" in result["message"].lower()


# ── get_drug_info ─────────────────────────────────────────────────────────────

class TestGetDrugInfo:
    def test_drug_found_generic_name(self):
        payload = {
            "results": [
                {
                    "purpose": ["Lowers blood pressure"],
                    "warnings": ["Do not stop abruptly"],
                    "dosage_and_administration": ["Take once daily"],
                    "openfda": {
                        "brand_name": ["Prinivil"],
                        "generic_name": ["Lisinopril"],
                        "manufacturer_name": ["Merck"],
                    },
                }
            ]
        }
        with patch("requests.get", return_value=_mock_response(200, payload)):
            result = get_drug_info("Lisinopril")
        assert result["found"] is True
        assert result["generic_name"] == "Lisinopril"
        assert "disclaimer" in result

    def test_drug_not_found_returns_404(self):
        with patch("requests.get", return_value=_mock_response(404, {})):
            result = get_drug_info("CompletelyFakeDrug999")
        assert result["found"] is False

    def test_empty_results_list(self):
        with patch("requests.get", return_value=_mock_response(200, {"results": []})):
            result = get_drug_info("UnknownDrug")
        assert result["found"] is False

    def test_network_exception(self):
        with patch("requests.get", side_effect=Exception("fail")):
            result = get_drug_info("Aspirin")
        assert result["found"] is False
