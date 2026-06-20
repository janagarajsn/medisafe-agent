"""Tests for the SQLite database manager."""

import sqlite3

import pytest

import src.database.manager as _db_module
from src.database.manager import (
    add_medication,
    deactivate_medication,
    get_adherence,
    get_medications,
    record_dose,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add(user_id="u1", name="Aspirin", dosage="81mg", frequency="daily"):
    return add_medication(
        user_id=user_id,
        name=name,
        dosage=dosage,
        frequency=frequency,
        times_per_day=1,
        schedule_times="08:00",
        start_date="2026-01-01",
    )


# ── Add / List ────────────────────────────────────────────────────────────────

def test_add_returns_positive_id():
    med_id = _add()
    assert med_id > 0


def test_get_medications_returns_decrypted():
    _add(name="Lisinopril", dosage="10mg")
    meds = get_medications("u1")
    assert len(meds) == 1
    assert meds[0]["name"] == "Lisinopril"
    assert meds[0]["dosage"] == "10mg"


def test_name_is_encrypted_at_rest(monkeypatch, tmp_path):
    _add(name="SecretDrug", dosage="5mg")
    # Read raw value from the DB column — should NOT contain the plaintext.
    # Access _DB_PATH via the module so the monkeypatch value is used.
    conn = sqlite3.connect(_db_module._DB_PATH)
    rows = conn.execute("SELECT name_enc FROM medications").fetchall()
    conn.close()
    for (raw,) in rows:
        assert "SecretDrug" not in raw, "Medication name stored as plaintext!"


def test_multiple_users_isolated():
    _add(user_id="alice", name="Vitamin C")
    _add(user_id="bob", name="Zinc")
    assert len(get_medications("alice")) == 1
    assert get_medications("alice")[0]["name"] == "Vitamin C"
    assert len(get_medications("bob")) == 1


def test_empty_list_for_new_user():
    assert get_medications("nobody") == []


# ── Deactivate ────────────────────────────────────────────────────────────────

def test_deactivate_removes_from_active_list():
    med_id = _add()
    assert deactivate_medication("u1", med_id)
    assert get_medications("u1") == []


def test_deactivate_wrong_user_returns_false():
    med_id = _add(user_id="alice")
    assert not deactivate_medication("bob", med_id)


# ── Dose recording ────────────────────────────────────────────────────────────

def test_record_dose_returns_positive_id():
    med_id = _add()
    dose_id = record_dose("u1", med_id, "2026-06-20", "08:00", taken=True)
    assert dose_id > 0


def test_adherence_taken_100_percent():
    med_id = _add()
    record_dose("u1", med_id, "2026-06-20", "08:00", taken=True)
    # Query adherence over last 30 days so today's record is included
    data = get_adherence("u1", 30)
    assert len(data) == 1
    assert data[0]["taken"] == 1
    assert data[0]["total"] == 1
    assert data[0]["adherence_pct"] == 100.0


def test_adherence_skipped_0_percent():
    med_id = _add()
    record_dose("u1", med_id, "2026-06-20", "08:00", taken=False)
    data = get_adherence("u1", 30)
    assert data[0]["adherence_pct"] == 0.0


def test_adherence_empty_for_new_user():
    assert get_adherence("brand_new_user", 7) == []
