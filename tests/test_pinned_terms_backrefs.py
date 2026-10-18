"""Tests para ISSUE-016: Preservación y sanitización de backreferences y lookarounds en pinned_terms."""

from jg_plugin_filmmaker.structuring import apply_user_locks, structure_treatment


def test_apply_user_locks_safely_handles_backreferences_in_replacement():
    """Verifica que $1 y \\1 en el valor de reemplazo no se evalúen como grupos ni lancen re.error."""
    text = "El coste del equipo es de coste_original y el modelo es modelo_antiguo."
    user_locks = {
        "pinned_terms": {
            "coste_original": "$100",
            "modelo_antiguo": r"AT&T \1",
        }
    }

    result = apply_user_locks(text, user_locks, stage="structured")

    assert "$100" in result
    assert r"AT&T \1" in result
    assert result == r"El coste del equipo es de $100 y el modelo es AT&T \1."


def test_apply_user_locks_replaces_symbolic_and_non_alphanumeric_terms():
    """Verifica que términos con símbolos como C++ o #1 coincidan correctamente gracias a lookarounds adaptativos."""
    text = "Juan programa en C++ y tiene el puesto #1 del ranking."
    user_locks = {
        "pinned_terms": {
            "C++": "Rust",
            "#1": "Primer Lugar",
        }
    }

    result = apply_user_locks(text, user_locks, stage="structured")

    assert "Rust" in result
    assert "Primer Lugar" in result
    assert result == "Juan programa en Rust y tiene el puesto Primer Lugar del ranking."


def test_structure_treatment_with_backreferences_pinned_terms():
    """Verifica que structure_treatment aplique términos fijados con backreferences sin fallar."""
    raw = "Javi busca el producto modelo_x."
    user_locks = {
        "pinned_terms": {
            "Javi": "Javier",
            "modelo_x": r"Series \g<1>",
        }
    }

    result = structure_treatment(raw, user_locks=user_locks)

    assert "Javier" in result
    assert r"Series \g<1>" in result
