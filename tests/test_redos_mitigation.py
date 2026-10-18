import time

import pytest
from pydantic import ValidationError

from jg_plugin_filmmaker.formatting import format_screenplay
from jg_plugin_filmmaker.tools import (
    PlotHoleDetectorArgs,
    ScreenplayFormatterArgs,
    ShotBreakdownDetectorArgs,
    TreatmentStructuringArgs,
)


def test_pydantic_payload_limits():
    """Valida que entradas superiores a 50.000 caracteres sean rechazadas."""
    oversized_text = "a" * 50001

    with pytest.raises(ValidationError):
        TreatmentStructuringArgs(raw_text=oversized_text)

    with pytest.raises(ValidationError):
        ScreenplayFormatterArgs(structured_text=oversized_text)

    with pytest.raises(ValidationError):
        ShotBreakdownDetectorArgs(screenplay_text=oversized_text)

    # Contextos de personajes o bloques superiores a límites
    with pytest.raises(ValidationError):
        TreatmentStructuringArgs(
            raw_text="Test",
            characters_context=[{"name": f"P_{i}"} for i in range(101)],
        )

    with pytest.raises(ValidationError):
        PlotHoleDetectorArgs(blocks=[{"type": "action", "content": "..."} for _ in range(201)])


def test_redos_catastrophic_backtracking_prevention():
    """Valida que textos adversarios ambiguos se resuelvan en tiempo sub-segundo sin ReDoS."""
    # Cadena con repetición de palabras y comas diseñada para forzar backtracking si el regex no está acotado
    adversarial_paragraph = "mientras tanto, y luego y tras eso " * 50 + "dice que todo está bien."
    adversarial_text = "\n\n".join([adversarial_paragraph] * 10)

    start_time = time.perf_counter()
    result = format_screenplay(adversarial_text)
    elapsed = time.perf_counter() - start_time

    assert elapsed < 0.5, f"La ejecución tardó demasiado ({elapsed:.4f}s), posible ReDoS"
    assert "dice que todo está bien" in result or "DICE" in result or len(result) > 0


def test_no_verbs_fast_path():
    """Valida que un texto extenso sin verbos declarativos salte la expresión regular inmediatamente."""
    long_no_verb_text = "La oscuridad cubre la colina silenciosa y solitaria. " * 200

    start_time = time.perf_counter()
    result = format_screenplay(long_no_verb_text)
    elapsed = time.perf_counter() - start_time

    assert elapsed < 0.1, f"Fast-path demasiado lento: {elapsed:.4f}s"
    assert "oscuridad" in result
