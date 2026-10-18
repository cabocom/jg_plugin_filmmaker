"""Pruebas de paridad contractual bidireccional basadas en golden fixtures compartidos."""

import json
from pathlib import Path

from jg_plugin_filmmaker.tools import (
    execute_plot_hole_detector,
    execute_screenplay_formatter,
    execute_shot_breakdown_detector,
    execute_treatment_structuring,
)


def load_golden_vectors():
    fixture_path = Path(__file__).parent / "fixtures" / "contract_golden_vectors.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def test_treatment_structuring_golden_contract_parity():
    """Valida que treatment_structuring procese el vector de contrato de Laravel con éxito."""
    vectors = load_golden_vectors()
    spec = vectors["treatment_structuring"]

    result = execute_treatment_structuring(**spec["payload"])

    assert result.success is True
    assert result.metadata["stage"] == "structured"
    assert result.metadata["applied_locks_count"] >= 1

    for sub in spec["expected_substrings"]:
        assert sub in result.output


def test_screenplay_formatter_golden_contract_parity():
    """Valida que screenplay_formatter procese el vector de contrato de Laravel."""
    vectors = load_golden_vectors()
    spec = vectors["screenplay_formatter"]

    result = execute_screenplay_formatter(**spec["payload"])

    assert result.success is True
    assert result.metadata["stage"] == "screenplay"
    assert result.metadata["format"] == "fountain"

    for sub in spec["expected_substrings"]:
        assert sub.lower() in result.output.lower()


def test_shot_breakdown_detector_golden_contract_parity():
    """Valida que shot_breakdown_detector emita la estructura esperada para el vector canónico."""
    vectors = load_golden_vectors()
    spec = vectors["shot_breakdown_detector"]

    result = execute_shot_breakdown_detector(**spec["payload"])

    assert result.success is True
    assert result.metadata["stage"] == "shots"
    assert result.metadata["total_shots"] >= 3

    for sub in spec["expected_substrings"]:
        assert sub in result.output


def test_plot_hole_detector_golden_contract_parity():
    """Valida que plot_hole_detector audite los bloques serializados por Eloquent."""
    vectors = load_golden_vectors()
    spec = vectors["plot_hole_detector"]

    result = execute_plot_hole_detector(**spec["payload"])

    assert result.success is True
    assert result.metadata["stage"] == spec["expected_stage"]
    assert "detected_holes" in result.metadata
