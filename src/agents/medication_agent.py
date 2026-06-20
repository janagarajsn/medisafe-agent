"""Medication Manager sub-agent

Handles all CRUD operations for medications and dose tracking.
Receives delegated tasks from the root orchestrator.
"""

from google.adk.agents import LlmAgent

from src.tools.medication_tools import (
    add_medication,
    get_adherence_report,
    list_medications,
    mark_dose_taken,
    remove_medication,
    skip_dose,
)

_INSTRUCTION = """
You are the Medication Manager — a caring and precise sub-agent of MediSafe.

Your responsibilities:
- Add new medications to a user's regimen
- List their current active medications with schedule details
- Record when doses are taken or skipped
- Generate adherence reports to show how well the user follows their regimen
- Remove medications they no longer need

Guidelines:
- Always use the user_id passed to you from the orchestrator (default: "default_user").
- When adding a medication, confirm the name, dosage, frequency, and times before saving.
- When reporting adherence, celebrate improvements and be supportive about missed doses.
- Never provide medical advice — focus only on schedule management.
- If a user seems confused about their medication, encourage them to contact their doctor.
- Keep responses concise and warm.
"""

def make_medication_agent() -> LlmAgent:
    """Create a new Medication Manager agent instance."""
    return LlmAgent(
        name="medication_manager",
        model="gemini-3.5-flash",
        description=(
            "Manages medication schedules: add, list, track doses, report adherence, and remove medications."
        ),
        instruction=_INSTRUCTION,
        tools=[
            add_medication,
            list_medications,
            mark_dose_taken,
            skip_dose,
            get_adherence_report,
            remove_medication,
        ],
    )


# Convenience singleton for direct inspection / testing
medication_agent = make_medication_agent()
