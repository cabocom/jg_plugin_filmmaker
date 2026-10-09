"""Pruebas de integración del plugin con MockPluginRunner."""

import pytest
from jg_sdk.testing import MockPluginRunner

from jg_plugin_filmmaker.plugin import FilmmakerPlugin


@pytest.mark.asyncio
async def test_plugin_runner_integration():
    """Verifica la ejecución integrada del plugin dentro del runner de pruebas de jg_agente."""
    plugin = FilmmakerPlugin()
    async with MockPluginRunner(plugin) as runner:
        assert runner.metadata.name == "filmmaker"
        health = await runner.health_check()
        assert health["status"] == "ok"
        assert health["tools_count"] == 3

        # Ejecución de treatment_structuring
        res_struct = runner.run_tool(
            "treatment_structuring",
            {"raw_text": "Javi entra al bar.", "user_locks": {"pinned_terms": {"Javi": "Javier"}}},
        )
        assert res_struct.success is True
        assert "Javier" in res_struct.output

        # Ejecución de screenplay_formatter
        res_script = runner.run_tool(
            "screenplay_formatter",
            {"structured_text": "Javier observa el horizonte."},
        )
        assert res_script.success is True

        # Ejecución de shot_breakdown_detector
        res_shots = runner.run_tool(
            "shot_breakdown_detector",
            {"screenplay_text": "Javier camina hacia la puerta."},
        )
        assert res_shots.success is True
        assert "--- shot 1 (" in res_shots.output
