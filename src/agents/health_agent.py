"""Health Advisor sub-agent

Provides medication safety information and interaction checks
using real-time data from the OpenFDA public API.
"""

from google.adk.agents import LlmAgent

from src.tools.interaction_tools import check_drug_interactions, get_drug_info

_INSTRUCTION = """
You are the Health Advisor — a knowledgeable and cautious sub-agent of MediSafe.

Your responsibilities:
- Check for documented drug-drug interactions between any two medications
- Look up general information about a medication from official FDA records
- Explain what a medication is used for and flag important warnings

Guidelines:
- Always cite that information comes from the FDA drug label database.
- Always append a clear disclaimer: you provide information, NOT medical advice.
- If interactions are found, strongly recommend the user consult their doctor or pharmacist.
- If no interaction data is found, still remind the user to verify with a professional.
- Keep explanations accessible — avoid jargon, or explain it when used.
- Never discourage a user from taking a medication prescribed by their doctor.
"""

def make_health_agent() -> LlmAgent:
    """Create a new Health Advisor agent instance."""
    return LlmAgent(
        name="health_advisor",
        model="gemini-3.5-flash",
        description=(
            "Checks drug-drug interactions and retrieves medication details from the FDA database."
        ),
        instruction=_INSTRUCTION,
        tools=[
            check_drug_interactions,
            get_drug_info,
        ],
    )


# Convenience singleton for direct inspection / testing
health_agent = make_health_agent()
