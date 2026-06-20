"""Tests for ADK agent construction (no LLM calls made)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMedicationAgent:
    def test_agent_can_be_imported(self):
        from src.agents.medication_agent import medication_agent
        assert medication_agent is not None

    def test_agent_name(self):
        from src.agents.medication_agent import medication_agent
        assert medication_agent.name == "medication_manager"

    def test_agent_model(self):
        from src.agents.medication_agent import medication_agent
        assert "gemini" in medication_agent.model.lower()

    def test_agent_has_all_tools(self):
        from src.agents.medication_agent import medication_agent
        tool_names = {t.__name__ for t in medication_agent.tools}
        assert "add_medication" in tool_names
        assert "list_medications" in tool_names
        assert "mark_dose_taken" in tool_names
        assert "skip_dose" in tool_names
        assert "get_adherence_report" in tool_names
        assert "remove_medication" in tool_names

    def test_instruction_mentions_medical_advice_disclaimer(self):
        from src.agents.medication_agent import medication_agent
        assert "medical advice" in medication_agent.instruction.lower()


class TestHealthAgent:
    def test_agent_can_be_imported(self):
        from src.agents.health_agent import health_agent
        assert health_agent is not None

    def test_agent_name(self):
        from src.agents.health_agent import health_agent
        assert health_agent.name == "health_advisor"

    def test_agent_has_interaction_tools(self):
        from src.agents.health_agent import health_agent
        tool_names = {t.__name__ for t in health_agent.tools}
        assert "check_drug_interactions" in tool_names
        assert "get_drug_info" in tool_names

    def test_instruction_mentions_disclaimer(self):
        from src.agents.health_agent import health_agent
        assert "disclaimer" in health_agent.instruction.lower()


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_create_orchestrator_returns_agent(self):
        mock_toolset = MagicMock()
        mock_toolset.close = AsyncMock()

        with patch("src.agents.orchestrator.McpToolset", return_value=mock_toolset):
            from src.agents.orchestrator import create_orchestrator
            orchestrator, toolset = await create_orchestrator()

        assert orchestrator is not None
        assert orchestrator.name == "medisafe_orchestrator"

    @pytest.mark.asyncio
    async def test_orchestrator_has_sub_agents(self):
        mock_toolset = MagicMock()
        mock_toolset.close = AsyncMock()

        with patch("src.agents.orchestrator.McpToolset", return_value=mock_toolset):
            from src.agents.orchestrator import create_orchestrator
            orchestrator, _ = await create_orchestrator()

        sub_names = {a.name for a in orchestrator.sub_agents}
        assert "medication_manager" in sub_names
        assert "health_advisor" in sub_names

    @pytest.mark.asyncio
    async def test_orchestrator_instruction_mentions_security(self):
        mock_toolset = MagicMock()
        mock_toolset.close = AsyncMock()

        with patch("src.agents.orchestrator.McpToolset", return_value=mock_toolset):
            from src.agents.orchestrator import create_orchestrator
            orchestrator, _ = await create_orchestrator()

        assert "security" in orchestrator.instruction.lower() or "never" in orchestrator.instruction.lower()
