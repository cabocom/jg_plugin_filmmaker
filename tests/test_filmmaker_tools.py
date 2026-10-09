"""Pruebas unitarias para las herramientas canónicas de jg_plugin_filmmaker."""

import pytest
from jg_sdk.contracts import RiskLevel, ToolResult

from jg_plugin_filmmaker.plugin import FilmmakerPlugin
from jg_plugin_filmmaker.tools import (
    execute_screenplay_formatter,
    execute_shot_breakdown_detector,
    execute_treatment_structuring,
    get_filmmaker_tools,
    screenplay_formatter_tool,
    shot_breakdown_detector_tool,
    treatment_structuring_tool,
)


def test_plugin_metadata_and_registration():
    """Valida los metadatos canónicos del plugin y el registro de las 3 herramientas."""
    plugin = FilmmakerPlugin()
    meta = plugin.get_plugin_metadata()

    assert meta.name == "filmmaker"
    assert meta.version == "1.0.0"
    assert meta.author == "Javier Gálvez"
    assert "cinema" in meta.tags

    tools = plugin.register_tools()
    assert len(tools) == 3

    tool_names = [t.name for t in tools]
    assert "treatment_structuring" in tool_names
    assert "screenplay_formatter" in tool_names
    assert "shot_breakdown_detector" in tool_names

    for t in tools:
        assert t.risk_level == RiskLevel.LOW
        assert t.read_only is True


def test_treatment_structuring_basic_and_context():
    """Comprueba la normalización básica de tratamiento con contexto de escena."""
    raw = "el protagonista entra en el bar buscando respuestas"
    chars = [{"name": "Javier", "role": "protagonista"}]
    loc = {"name": "BAR CENTRAL", "type": "INT", "lighting_notes": "Luz tenue"}

    result = execute_treatment_structuring(
        raw_text=raw,
        characters_context=chars,
        location_context=loc,
    )

    assert isinstance(result, ToolResult)
    assert result.success is True
    assert "entra en el bar buscando respuestas" in result.output
    assert not result.output.startswith("En ")
    assert result.metadata["stage"] == "structured"


def test_treatment_structuring_respects_pinned_terms_in_user_locks():
    """Verifica que los términos fijados (pinned_terms) en user_locks se respetan estrictamente."""
    raw = "Javi nota que todo está en silencio. Javi busca su abrigo."
    user_locks = {
        "pinned_terms": {
            "Javi": "Javier",
        }
    }

    result = execute_treatment_structuring(
        raw_text=raw,
        user_locks=user_locks,
    )

    assert result.success is True
    assert "Javier nota que todo está en silencio." in result.output
    assert "Javier busca su abrigo." in result.output
    assert "Javi " not in result.output
    assert result.metadata["applied_locks_count"] >= 1


def test_treatment_structuring_respects_manual_diffs_in_user_locks():
    """Verifica que los overrides manuales del usuario en manual_diffs no son sobreescritos."""
    raw = "Juan nota que Javier está preocupado."
    user_locks = {
        "manual_diffs": [
            {
                "stage": "structured",
                "original_ai": "Juan nota que Javier está preocupado.",
                "user_override": "Juan sospecha profundamente de Javier.",
                "applied_at": "2026-10-09T18:30:00Z",
            }
        ]
    }

    result = execute_treatment_structuring(
        raw_text=raw,
        user_locks=user_locks,
    )

    assert result.success is True
    assert "Juan sospecha profundamente de Javier." in result.output
    assert "Juan nota que Javier está preocupado." not in result.output


def test_screenplay_formatter_standard_syntax():
    """Verifica la conversión a formato estándar de guión literario Fountain."""
    structured = (
        "Javier apoya el vaso en la barra de madera.\n\n"
        "Javier: (en voz baja) Ya están aquí.\n\n"
        "La campana de la entrada tintinea."
    )
    chars = [{"name": "Javier"}]
    loc = {"name": "BAR CENTRAL", "type": "INT", "time_of_day": "NOCHE"}

    result = execute_screenplay_formatter(
        structured_text=structured,
        characters_context=chars,
        location_context=loc,
    )

    assert result.success is True
    output = result.output

    assert "INT. BAR CENTRAL - NOCHE 1" in output
    assert "JAVIER" in output
    assert "(en voz baja)" in output
    assert "Ya están aquí." in output
    assert result.metadata["format"] == "fountain"


def test_screenplay_formatter_preserves_user_locks():
    """Verifica que screenplay_formatter aplica y mantiene los pinned_terms."""
    structured = "Javi camina hacia la barra."
    user_locks = {"pinned_terms": {"Javi": "Javier"}}

    result = execute_screenplay_formatter(
        structured_text=structured,
        user_locks=user_locks,
    )

    assert result.success is True
    assert "Javier" in result.output
    assert "Javi " not in result.output
    assert "Javier camina hacia la barra." in result.output


def test_shot_breakdown_detector_canonical_syntax():
    """Verifica que shot_breakdown_detector emite estrictamente la sintaxis '--- shot N (tipo) ---'."""
    screenplay = (
        "INT. BAR CENTRAL - NOCHE 1\n\n"
        "Javier y Juan están sentados en la mesa del bar.\n\n"
        "Javier mira fijamente a Juan esperando una respuesta.\n\n"
        "Detalle del vaso apoyado sobre la madera."
    )

    result = execute_shot_breakdown_detector(screenplay_text=screenplay)

    assert result.success is True
    output = result.output

    # Comprobación de delimitadores canónicos estrictos
    assert "--- shot 1 (" in output
    assert "--- shot 2 (" in output
    assert "--- shot 3 (" in output

    shots = result.metadata["shots"]
    assert len(shots) == 3

    assert shots[0]["shot_number"] == 1
    assert shots[0]["shot_type"] in ["PG", "GPG", "PM"]

    assert shots[1]["shot_number"] == 2
    assert shots[1]["shot_type"] in ["PM", "PP"]

    assert shots[2]["shot_number"] == 3
    assert shots[2]["shot_type"] == "PD"

    assert result.metadata["total_shots"] == 3


def test_agent_tools_run_invocation():
    """Valida la ejecución de las herramientas a través del método AgentTool.run()."""
    all_tools = get_filmmaker_tools()
    assert len(all_tools) == 3

    # Invocación de treatment_structuring vía AgentTool
    res1 = treatment_structuring_tool.run(raw_text="Acción dramática de prueba.")
    assert res1.success is True

    # Invocación de screenplay_formatter vía AgentTool
    res2 = screenplay_formatter_tool.run(structured_text="El protagonista avanza.")
    assert res2.success is True

    # Invocación de shot_breakdown_detector vía AgentTool
    res3 = shot_breakdown_detector_tool.run(screenplay_text="Plano de acción.")
    assert res3.success is True
    assert "--- shot 1 (" in res3.output


@pytest.mark.asyncio
async def test_plugin_lifecycle_and_health():
    """Verifica los métodos del ciclo de vida y health_check del plugin."""
    plugin = FilmmakerPlugin()
    assert plugin._is_started is False

    await plugin.startup()
    assert plugin._is_started is True

    health = await plugin.health_check()
    assert health["status"] == "ok"
    assert health["plugin"] == "filmmaker"
    assert health["tools_count"] == 3

    await plugin.shutdown()
    assert plugin._is_started is False


def test_llm_inference_treatment_structuring_with_mock_llm():
    """Valida la inferencia con LLM inyectado para estructuración respetando user_locks."""

    class DummyChatModel:
        def __init__(self, answer: str):
            self.answer = answer
            self.last_messages = None

        def invoke(self, messages):
            self.last_messages = messages

            class DummyResponse:
                content = self.answer

            return DummyResponse()

    mock_llm = DummyChatModel(
        answer="En BAR CENTRAL (INT): Javier observa la ventana mientras Javi siente el frío exterior."
    )
    user_locks = {
        "pinned_terms": {
            "Javi": "Javier",
        }
    }

    result = execute_treatment_structuring(
        raw_text="Javier mira afuera con frío.",
        user_locks=user_locks,
        llm_client=mock_llm,
    )

    assert result.success is True
    # Comprobar que el LLM fue invocado y luego se aplicó el reemplazo de 'Javi' -> 'Javier'
    assert "Javier siente el frío" in result.output
    assert "Javi siente" not in result.output
    assert mock_llm.last_messages is not None


def test_llm_inference_screenplay_formatter_resolves_indirect_dialogue():
    """Valida que el LLM inyectado formatea diálogos y resuelve estilo indirecto."""

    class DummyChatModel:
        def invoke(self, messages):
            class DummyResponse:
                content = (
                    "INT. BAR CENTRAL - NOCHE 1\n\n"
                    "JAVIER\n"
                    "(con miedo)\n"
                    "Ya están llegando.\n\n"
                    "JUAN\n"
                    "¿Quién está llegando?"
                )

            return DummyResponse()

    mock_llm = DummyChatModel()
    result = execute_screenplay_formatter(
        structured_text="Javier mira a Juan con miedo y le dice que ya están llegando. Juan le pregunta quién.",
        llm_client=mock_llm,
    )

    assert result.success is True
    assert "INT. BAR CENTRAL - NOCHE 1" in result.output
    assert "JAVIER\n(con miedo)\nYa están llegando." in result.output
    assert "JUAN\n¿Quién está llegando?" in result.output


def test_llm_inference_shot_breakdown_parses_canonical_delimiters():
    """Valida que el desglose con LLM parsea delimitadores canónicos '--- shot N (tipo) ---'."""

    class DummyChatModel:
        def invoke(self, messages):
            class DummyResponse:
                content = (
                    "--- shot 1 (PG) ---\n"
                    "INT. BAR CENTRAL - NOCHE 1\n"
                    "Javier está sentado en una esquina solitaria.\n\n"
                    "--- shot 2 (PP) ---\n"
                    "Primer plano de los ojos asustados de Javier.\n\n"
                    "--- shot 3 (PD) ---\n"
                    "Detalle de las manos temblando sobre la mesa."
                )

            return DummyResponse()

    mock_llm = DummyChatModel()
    result = execute_shot_breakdown_detector(
        screenplay_text="Guión de prueba",
        llm_client=mock_llm,
    )

    assert result.success is True
    assert "--- shot 1 (PG) ---" in result.output
    assert "--- shot 2 (PP) ---" in result.output
    assert "--- shot 3 (PD) ---" in result.output

    shots = result.metadata["shots"]
    assert len(shots) == 3
    assert shots[0]["shot_type"] == "PG"
    assert shots[1]["shot_type"] == "PP"
    assert shots[2]["shot_type"] == "PD"
