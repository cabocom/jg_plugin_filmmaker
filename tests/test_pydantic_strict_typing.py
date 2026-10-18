"""Pruebas de tipado estricto Pydantic v2 y robustez de esquemas en jg_plugin_filmmaker."""

import pytest
from pydantic import ValidationError

from jg_plugin_filmmaker.tools import (
    CharacterContext,
    LocationContext,
    PlotHoleDetectorArgs,
    ScriptBlockItem,
    TreatmentStructuringArgs,
    UserLocksModel,
    execute_screenplay_formatter,
    execute_treatment_structuring,
)


def test_character_context_validation_and_eloquent_metadata_tolerance():
    """Valida CharacterContext y su tolerancia ante campos extra de Eloquent."""
    # Entrada con metadatos de base de datos de Laravel (id, uuid, timestamps)
    eloquent_payload = {
        "id": 42,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Javier Gálvez",
        "bio": "Director y guionista.",
        "psychology": "Obsesivo con los detalles.",
        "costume_notes": "Chaqueta de cuero oscura.",
        "created_at": "2026-10-18T12:00:00Z",
    }

    char = CharacterContext.model_validate(eloquent_payload)
    assert char.name == "Javier Gálvez"
    assert char.bio == "Director y guionista."

    # Nombre vacío debe ser rechazado
    with pytest.raises(ValidationError):
        CharacterContext(name="")


def test_user_locks_model_strict_typing():
    """Valida que UserLocksModel valide los tipos de pinned_terms y manual_diffs."""
    valid_locks = {
        "pinned_terms": {"Javi": "Javier"},
        "manual_diffs": [
            {
                "stage": "structured",
                "original_ai": "Texto original",
                "user_override": "Texto corregido",
            }
        ],
        "locked_fields": ["structured", "screenplay"],
        "extra_laravel_field": "ignored_safely",
    }

    locks = UserLocksModel.model_validate(valid_locks)
    assert locks.pinned_terms["Javi"] == "Javier"
    assert len(locks.manual_diffs) == 1
    assert locks.manual_diffs[0].stage == "structured"

    # pinned_terms con valor que no sea dict o strings debe fallar
    with pytest.raises(ValidationError):
        UserLocksModel.model_validate({"pinned_terms": "cadena_invalida"})

    # manual_diffs con stage inválido debe fallar
    with pytest.raises(ValidationError):
        UserLocksModel.model_validate({"manual_diffs": [{"stage": "invalid_stage_name"}]})


def test_treatment_structuring_args_validation():
    """Valida TreatmentStructuringArgs con modelos anidados y rechazo de tipos erróneos."""
    payload = {
        "raw_text": "El protagonista llega al muelle.",
        "characters_context": [{"name": "Lucas", "role": "protagonista"}],
        "location_context": {
            "name": "MUELLE VIEJO",
            "type": "EXT",
            "time_of_day": "NOCHE",
        },
        "user_locks": {
            "pinned_terms": {"Lucas": "LUCAS"},
        },
    }

    args = TreatmentStructuringArgs.model_validate(payload)
    assert args.raw_text == "El protagonista llega al muelle."
    assert len(args.characters_context) == 1
    assert args.characters_context[0].name == "Lucas"
    assert args.location_context.name == "MUELLE VIEJO"
    assert args.user_locks.pinned_terms["Lucas"] == "LUCAS"


def test_execute_treatment_structuring_with_pydantic_instances():
    """Comprueba que execute_treatment_structuring acepta tanto dicts como instancias Pydantic."""
    char = CharacterContext(name="Javier")
    loc = LocationContext(name="DESPACHO", type="INT")
    locks = UserLocksModel(pinned_terms={"Javi": "Javier"})

    result = execute_treatment_structuring(
        raw_text="Javi entra en el despacho con determinación.",
        characters_context=[char],
        location_context=loc,
        user_locks=locks,
    )

    assert result.success is True
    assert "Javier entra en el despacho" in result.output
    assert result.metadata["applied_locks_count"] >= 1


def test_execute_screenplay_formatter_with_pydantic_instances():
    """Comprueba que execute_screenplay_formatter funciona con modelos de Pydantic."""
    locks = UserLocksModel(pinned_terms={"Javi": "Javier"})

    result = execute_screenplay_formatter(
        structured_text="Javi toma un vaso de agua.",
        user_locks=locks,
    )

    assert result.success is True
    assert "Javier toma un vaso de agua." in result.output


def test_plot_hole_detector_args_validation():
    """Valida los esquemas estrictos de PlotHoleDetectorArgs."""
    valid_blocks = [
        {"type": "slugline", "content": "INT. SALON - DIA"},
        {"type": "action", "content": "Un cuadro cae de la pared."},
    ]

    args = PlotHoleDetectorArgs.model_validate({"blocks": valid_blocks})
    assert len(args.blocks) == 2
    assert isinstance(args.blocks[0], ScriptBlockItem)
    assert args.blocks[0].type == "slugline"

    # Bloques vacíos deben fallar por min_length=1
    with pytest.raises(ValidationError):
        PlotHoleDetectorArgs.model_validate({"blocks": []})
