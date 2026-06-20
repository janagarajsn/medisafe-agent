from datetime import date, datetime

from src.database import manager as db


def add_medication(
    user_id: str,
    name: str,
    dosage: str,
    frequency: str,
    times_per_day: int = 1,
    schedule_times: str = "08:00",
    start_date: str = "",
    end_date: str = "",
    notes: str = "",
) -> dict:
    """Add a new medication to the user's regimen (data stored encrypted).

    Args:
        user_id: Unique identifier for the user.
        name: Medication name, e.g. "Lisinopril".
        dosage: Dosage string, e.g. "10mg".
        frequency: How often it is taken, e.g. "daily", "twice daily".
        times_per_day: Number of individual doses per day (1–24).
        schedule_times: Comma-separated HH:MM times, e.g. "08:00,20:00".
        start_date: YYYY-MM-DD start date; defaults to today.
        end_date: Optional YYYY-MM-DD end date.
        notes: Optional free-text notes.

    Returns:
        dict with ``success``, ``medication_id``, and ``message``.
    """
    name = (name or "").strip()
    dosage = (dosage or "").strip()
    if not name:
        return {"success": False, "error": "Medication name cannot be empty."}
    if not dosage:
        return {"success": False, "error": "Dosage cannot be empty."}
    if not 1 <= times_per_day <= 24:
        return {"success": False, "error": "times_per_day must be between 1 and 24."}

    med_id = db.add_medication(
        user_id=user_id,
        name=name,
        dosage=dosage,
        frequency=frequency,
        times_per_day=times_per_day,
        schedule_times=schedule_times or "08:00",
        start_date=start_date or date.today().isoformat(),
        end_date=end_date or None,
        notes=notes or None,
    )
    return {
        "success": True,
        "medication_id": med_id,
        "message": f"Added {name} ({dosage}) to your medication list.",
    }


def list_medications(user_id: str) -> dict:
    """List all active medications for a user.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        dict with ``medications`` list and ``count``.
    """
    meds = db.get_medications(user_id)
    return {
        "medications": meds,
        "count": len(meds),
        "message": f"Found {len(meds)} active medication(s)." if meds else "No active medications found.",
    }


def mark_dose_taken(
    user_id: str,
    medication_id: int,
    scheduled_time: str = "",
) -> dict:
    """Record that a dose has been taken.

    Args:
        user_id: Unique identifier for the user.
        medication_id: Database ID of the medication.
        scheduled_time: HH:MM scheduled time; defaults to now.

    Returns:
        dict with ``success`` and ``message``.
    """
    time_str = scheduled_time or datetime.now().strftime("%H:%M")
    dose_id = db.record_dose(
        user_id=user_id,
        medication_id=medication_id,
        scheduled_date=date.today().isoformat(),
        scheduled_time=time_str,
        taken=True,
    )
    return {
        "success": True,
        "dose_id": dose_id,
        "message": f"Dose recorded for medication ID {medication_id} at {time_str}.",
    }


def skip_dose(
    user_id: str,
    medication_id: int,
    scheduled_time: str = "",
) -> dict:
    """Record that a dose was intentionally skipped.

    Args:
        user_id: Unique identifier for the user.
        medication_id: Database ID of the medication.
        scheduled_time: HH:MM scheduled time; defaults to now.

    Returns:
        dict with ``success`` and ``message``.
    """
    time_str = scheduled_time or datetime.now().strftime("%H:%M")
    dose_id = db.record_dose(
        user_id=user_id,
        medication_id=medication_id,
        scheduled_date=date.today().isoformat(),
        scheduled_time=time_str,
        taken=False,
    )
    return {
        "success": True,
        "dose_id": dose_id,
        "message": f"Skipped dose recorded for medication ID {medication_id} at {time_str}.",
    }


def get_adherence_report(user_id: str, days: int = 7) -> dict:
    """Return a medication adherence report for recent days.

    Args:
        user_id: Unique identifier for the user.
        days: Number of past days to include (default 7).

    Returns:
        dict with per-medication stats and overall adherence percentage.
    """
    data = db.get_adherence(user_id, days)
    if not data:
        return {
            "report": [],
            "overall_adherence_pct": None,
            "period_days": days,
            "message": f"No dose records found for the past {days} day(s).",
        }
    overall = sum(r["adherence_pct"] for r in data) / len(data)
    return {
        "report": data,
        "overall_adherence_pct": round(overall, 1),
        "period_days": days,
        "message": f"Overall adherence over {days} day(s): {overall:.1f}%",
    }


def remove_medication(user_id: str, medication_id: int) -> dict:
    """Deactivate a medication (remove from active list).

    Args:
        user_id: Unique identifier for the user.
        medication_id: Database ID of the medication to remove.

    Returns:
        dict with ``success`` and ``message``.
    """
    removed = db.deactivate_medication(user_id, medication_id)
    if removed:
        return {"success": True, "message": f"Medication ID {medication_id} removed from active list."}
    return {"success": False, "message": "Medication not found or already inactive."}
