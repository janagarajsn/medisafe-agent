"""MediSafe Root Orchestrator

The root LlmAgent that:
  1. Understands user intent and routes to the right sub-agent.
  2. Calls medication database tools via an MCP server (stdio transport).
  3. Delegates health/interaction queries to the health_advisor sub-agent.
  4. Delegates medication CRUD to the medication_manager sub-agent.

The MCP connection is created once at startup; call toolset.close() when done.
"""

import os

from mcp import StdioServerParameters
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams

from src.agents.health_agent import make_health_agent
from src.agents.medication_agent import make_medication_agent

_INSTRUCTION = """
You are MediSafe — a compassionate, intelligent personal medication management concierge.

Your mission: help users manage their medications safely, build healthy habits,
and stay informed without replacing their healthcare team.

You have two specialist sub-agents you can delegate to:
  • medication_manager  — add/list/track/remove medications, dose recording, adherence reports
  • health_advisor      — drug interaction checks, FDA drug information lookup

You also have direct access to the MediSafe database via MCP tools (prefixed "mcp_").

Routing logic:
  - Managing medications, recording doses, adherence → delegate to medication_manager
  - Drug interactions, drug lookup → delegate to health_advisor
  - General encouragement, explaining results, summarising → handle directly

Behaviour:
  - Greet the user warmly on first interaction and ask their name.
  - Use the user's name once you know it.
  - Be encouraging about medication adherence — never shame for missed doses.
  - Remind users that you are a scheduling/information tool, not a doctor.
  - Keep responses concise and friendly.
  - If unsure which sub-agent to use, prefer medication_manager for anything schedule-related.

Security:
  - Never display or repeat raw database IDs unless the user explicitly needs them.
  - Never ask for, store, or repeat passwords, insurance numbers, or diagnoses.
"""

_MCP_SERVER_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "src",
    "mcp_server",
    "server.py",
)


def get_mcp_params() -> StdioConnectionParams:
    """Return StdioConnectionParams pointing at the MediSafe MCP server."""
    return StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[_MCP_SERVER_SCRIPT],
        )
    )


async def create_orchestrator() -> tuple[LlmAgent, McpToolset]:
    """Create the root orchestrator agent with a live MCP connection.

    Returns the agent and the toolset. Call ``await toolset.close()``
    when the session ends to cleanly shut down the MCP subprocess.
    """
    mcp_toolset = McpToolset(connection_params=get_mcp_params())

    # Fresh instances per session — ADK enforces a single-parent constraint,
    # so each orchestrator must own its own sub-agent objects.
    orchestrator = LlmAgent(
        name="medisafe_orchestrator",
        model="gemini-3.5-flash",
        description="MediSafe root orchestrator — personal AI medication concierge.",
        instruction=_INSTRUCTION,
        tools=[mcp_toolset],
        sub_agents=[make_medication_agent(), make_health_agent()],
    )
    return orchestrator, mcp_toolset
