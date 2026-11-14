"""Pruebas unitarias para el motor de auditoría de agujeros dramáticos (plot_holes.py)."""

import json
from unittest.mock import MagicMock

from jg_plugin_filmmaker.plot_holes import detect_plot_holes


def test_detect_plot_holes_empty_blocks():
    """Valida que una lista vacía de bloques no produzca agujeros."""
    assert detect_plot_holes([]) == []


def test_detect_plot_holes_deterministic_teleportation():
    """Valida la detección heurística de teletransportación sin LLM."""
    blocks = [
        {"id": "b1", "text": "Javier está en Madrid."},
        {"id": "b2", "text": "De repente aparece de la nada en Tokio."},
    ]
    holes = detect_plot_holes(blocks, llm_client=None)
    assert len(holes) == 1
    assert holes[0]["block_id"] == "b2"
    assert "continuidad espacial" in holes[0]["reason"]


def test_detect_plot_holes_deterministic_dead_character():
    """Valida la detección heurística de un personaje fallecido que reaparece."""
    characters = [{"name": "Carlos", "bio": "Detective"}]
    blocks = [
        {"id": "b1", "text": "Carlos muere en el tiroteo."},
        {"id": "b2", "text": "Carlos dice que no hay problema y camina hacia el coche."},
    ]
    holes = detect_plot_holes(blocks, characters=characters, llm_client=None)
    assert len(holes) == 1
    assert holes[0]["block_id"] == "b2"
    assert "Carlos" in holes[0]["reason"]


def test_detect_plot_holes_with_llm_mock():
    """Valida la detección con cliente LLM activo simulado."""
    mock_llm = MagicMock()
    fake_response = json.dumps({
        "detected_holes": [
            {"block_id": "blk_1", "reason": "Inconsistencia temporal grave entre noche y día."}
        ]
    })
    mock_llm.generate.return_value = fake_response
    mock_llm.invoke.return_value = fake_response

    blocks = [{"id": "blk_1", "raw_text": "Es mediodía pero el cielo está completamente estrellado."}]
    holes = detect_plot_holes(blocks, llm_client=mock_llm)

    assert len(holes) == 1
    assert holes[0]["block_id"] == "blk_1"
    assert "Inconsistencia temporal" in holes[0]["reason"]
