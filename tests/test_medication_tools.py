"""Tests for medication management tool functions."""

import pytest

from src.tools.medication_tools import (
    add_medication,
    get_adherence_report,
    list_medications,
    mark_dose_taken,
    remove_medication,
    skip_dose,
)


# ── add_medication ────────────────────────────────────────────────────────────

def test_add_success():
    result = add_medication("u1", "Metformin", "500mg", "twice daily", 2, "08:00,20:00")
    assert result["success"] is True
    assert "medication_id" in result


def test_add_empty_name_returns_error():
    result = add_medication("u1", "", "10mg", "daily")
    assert result["success"] is False
    assert "error" in result


def test_add_empty_dosage_returns_error():
    result = add_medication("u1", "Aspirin", "", "daily")
    assert result["success"] is False


def test_add_times_per_day_too_high():
    result = add_medication("u1", "X", "1mg", "hourly", times_per_day=25)
    assert result["success"] is False


def test_add_times_per_day_zero():
    result = add_medication("u1", "X", "1mg", "daily", times_per_day=0)
    assert result["success"] is False


def test_add_whitespace_name_trimmed_or_rejected():
    result = add_medication("u1", "   ", "10mg", "daily")
    assert result["success"] is False


# ── list_medications ──────────────────────────────────────────────────────────

def test_list_empty_for_new_user():
    result = list_medications("nobody")
    assert result["medications"] == []
    assert result["count"] == 0


def test_list_after_add():
    add_medication("u1", "Atorvastatin", "20mg", "daily")
    result = list_medications("u1")
    assert result["count"] == 1
    assert result["medications"][0]["name"] == "Atorvastatin"


def test_list_multiple():
    add_medication("u1", "MedA", "1mg", "daily")
    add_medication("u1", "MedB", "2mg", "daily")
    assert list_medications("u1")["count"] == 2


# ── mark_dose_taken / skip_dose ───────────────────────────────────────────────

def test_mark_dose_taken_success():
    add_result = add_medication("u1", "Omeprazole", "20mg", "daily")
    med_id = add_result["medication_id"]
    result = mark_dose_taken("u1", med_id, "08:00")
    assert result["success"] is True
    assert "dose_id" in result


def test_skip_dose_success():
    add_result = add_medication("u1", "Lisinopril", "10mg", "daily")
    med_id = add_result["medication_id"]
    result = skip_dose("u1", med_id, "08:00")
    assert result["success"] is True


# ── get_adherence_report ──────────────────────────────────────────────────────

def test_adherence_no_records():
    result = get_adherence_report("nobody", 7)
    assert result["report"] == []
    assert result["overall_adherence_pct"] is None


def test_adherence_with_doses():
    add_result = add_medication("u1", "Vitamin D", "1000IU", "daily")
    med_id = add_result["medication_id"]
    mark_dose_taken("u1", med_id, "08:00")
    result = get_adherence_report("u1", 30)
    assert result["overall_adherence_pct"] == 100.0


# ── remove_medication ─────────────────────────────────────────────────────────

def test_remove_existing():
    add_result = add_medication("u1", "Zinc", "50mg", "daily")
    med_id = add_result["medication_id"]
    result = remove_medication("u1", med_id)
    assert result["success"] is True
    assert list_medications("u1")["count"] == 0


def test_remove_nonexistent():
    result = remove_medication("u1", 99999)
    assert result["success"] is False
