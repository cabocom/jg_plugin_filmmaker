"""Pruebas de seguridad para refine_dialogue_to_direct_speech contra IndexError."""

import pytest

from jg_plugin_filmmaker.formatting import format_screenplay, refine_dialogue_to_direct_speech


@pytest.mark.parametrize(
    "raw_speech,verb,expected_contains",
    [
        ("", "pregunta", "¿...?"),
        ("?", "pregunta", "¿...?"),
        ("...", "pregunta", "¿...?"),
        ("que ?", "pregunta", "¿...?"),
        ("dónde está la salida", "pregunta", "¿Dónde está la salida?"),
        ("", "grita", "¡...!"),
        ("!", "grita", "¡...!"),
        ("...", "grita", "¡...!"),
        ("cuidado con el tren", "grita", "¡Cuidado con el tren!"),
        ("", "dice", "..."),
        ("...", "dice", "..."),
        ("que todo está bien", "dice", "Todo está bien."),
    ],
)
def test_refine_dialogue_handles_empty_and_punctuation_without_index_error(
    raw_speech: str, verb: str, expected_contains: str
):
    """Verifica que entradas vacías o solo con signos de puntuación no provoquen IndexError."""
    result = refine_dialogue_to_direct_speech(raw_speech, verb=verb)
    assert expected_contains in result


def test_format_screenplay_with_malformed_indirect_dialogue_paragraphs():
    """Verifica que format_screenplay no colapse ante oraciones ambiguas con solo signos."""
    screenplay_input = (
        "JUAN mira hacia la puerta y le pregunta qué ?\n\n"
        "MARÍA se asusta y le grita que !\n\n"
        "JUAN se acerca y dice que ..."
    )

    result = format_screenplay(screenplay_input)
    assert "¿...?" in result
    assert "¡...!" in result
    assert "JUAN" in result
    assert "MARÍA" in result
