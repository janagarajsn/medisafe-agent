"""MediSafe MCP Server

Exposes medication management tools via the Model Context Protocol (MCP)
so that any MCP-compatible client (including the Google ADK orchestrator)
can read and write medication data without direct Python imports.

Run standalone:
    python -m src.mcp_server.server
"""

import ast
import os
import sys

# Allow running as a subprocess from any working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server.fastmcp import FastMCP

from src.database import manager as db
from src.tools.interaction_tools import check_drug_interactions, get_drug_info
from src.tools.medication_tools import (
    add_medication,
    get_adherence_report,
    list_medications,
    mark_dose_taken,
    remove_medication,
    skip_dose,
)

mcp = FastMCP(
    "MediSafe",
    instructions=(
        "You are the MediSafe medication database server. "
        "All health data is stored encrypted at rest. "
        "Never expose raw encrypted values in responses."
    ),
)


# ── Medication management ─────────────────────────────────────────────────────

@mcp.tool()
def mcp_add_medication(
    user_id: str,
    name: str,
    dosage: str,
    frequency: str,
    times_per_day: int = 1,
    schedule_times: str = "08:00",
    start_date: str = "",
    end_date: str = "",
    notes: str = "",
) -> str:
    """Add a new medication to the user's regimen. Data is stored encrypted."""
    result = add_medication(
        user_id=user_id,
        name=name,
        dosage=dosage,
        frequency=frequency,
        times_per_day=times_per_day,
        schedule_times=schedule_times,
        start_date=start_date,
        end_date=end_date,
        notes=notes,
    )
    return str(result)


@mcp.tool()
def mcp_list_medications(user_id: str) -> str:
    """List all active medications for a user."""
    return str(list_medications(user_id))


@mcp.tool()
def mcp_mark_dose_taken(
    user_id: str,
    medication_id: int,
    scheduled_time: str = "",
) -> str:
    """Record that a medication dose has been taken."""
    return str(mark_dose_taken(user_id, medication_id, scheduled_time))


@mcp.tool()
def mcp_skip_dose(
    user_id: str,
    medication_id: int,
    scheduled_time: str = "",
) -> str:
    """Record that a medication dose was intentionally skipped."""
    return str(skip_dose(user_id, medication_id, scheduled_time))


@mcp.tool()
def mcp_get_adherence_report(user_id: str, days: int = 7) -> str:
    """Return a medication adherence report for the specified number of past days."""
    return str(get_adherence_report(user_id, days))


@mcp.tool()
def mcp_remove_medication(user_id: str, medication_id: int) -> str:
    """Deactivate a medication (remove it from the active list)."""
    return str(remove_medication(user_id, medication_id))


# ── Drug information ──────────────────────────────────────────────────────────

@mcp.tool()
def mcp_check_drug_interactions(drug1: str, drug2: str) -> str:
    """Check for known FDA-documented interactions between two medications."""
    return str(check_drug_interactions(drug1, drug2))


@mcp.tool()
def mcp_get_drug_info(drug_name: str) -> str:
    """Retrieve basic information about a medication from the FDA database."""
    return str(get_drug_info(drug_name))


if __name__ == "__main__":
    db.init_db()
    mcp.run()
