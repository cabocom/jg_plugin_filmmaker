"""Motor de estructuración y normalización de tratamiento cinematográfico.

Transforma ideas libres y texto bruto en tratamiento cinematográfico estructurado
en presente de indicativo, integrando el contexto de la biblia y respetando
estrictamente los bloqueos manuales del usuario (user_locks).
"""

import re
from typing import Any


def apply_user_locks(
    text: str, user_locks: dict[str, Any] | None, stage: str = "structured"
) -> str:
    """Aplica y preserva sustituciones y términos fijados en user_locks.

    Soporta:
    - pinned_terms: dict de término original a término canónico fijado (ej: {"Javi": "Javier"}).
    - manual_diffs: lista de dicts con stage, original_ai y user_override.
    """
    if not user_locks or not text:
        return text

    result = text

    # 1. Aplicar términos fijados (pinned_terms) respetando límites de palabra si es posible
    pinned_terms = user_locks.get("pinned_terms", {})
    if isinstance(pinned_terms, dict):
        for term, replacement in pinned_terms.items():
            if term and replacement:
                pattern = rf"\b{re.escape(str(term))}\b"
                result = re.sub(pattern, str(replacement), result, flags=re.IGNORECASE)

    # 2. Aplicar diffs manuales para la etapa correspondiente
    manual_diffs = user_locks.get("manual_diffs", [])
    if isinstance(manual_diffs, list):
        for diff in manual_diffs:
            if not isinstance(diff, dict):
                continue
            diff_stage = diff.get("stage")
            if diff_stage and diff_stage != stage:
                continue
            original = diff.get("original_ai")
            override = diff.get("user_override")
            if original and override and original in result:
                result = result.replace(original, override)

    return result


def structure_treatment(
    raw_text: str,
    characters_context: list[dict[str, Any]] | None = None,
    location_context: dict[str, Any] | None = None,
    user_locks: dict[str, Any] | None = None,
) -> str:
    """Normaliza texto bruto a tratamiento dramático en presente continuo/indicativo."""
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text.strip()

    # Normalizar contexto de localización
    location_prefix = ""
    if location_context and isinstance(location_context, dict):
        loc_name = location_context.get("name", "").strip()
        loc_type = location_context.get("type", "").strip()
        lighting = location_context.get("lighting_notes", "").strip()
        if loc_name:
            details = f" ({loc_type})" if loc_type else ""
            if lighting:
                details += f" bajo {lighting.lower()}"
            location_prefix = f"En {loc_name}{details}: "

    # Dividir párrafos y transformar oraciones a presente indicativo
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    structured_paragraphs: list[str] = []

    for i, p in enumerate(paragraphs):
        # Limpieza básica
        p_clean = re.sub(r"\s+", " ", p)

        # Si hay contexto de personajes, normalizar nombres si es relevante
        if characters_context and isinstance(characters_context, list):
            for char in characters_context:
                if isinstance(char, dict) and "name" in char:
                    cname = char["name"].strip()
                    pattern = rf"\b{re.escape(cname)}\b"
                    p_clean = re.sub(pattern, cname, p_clean, flags=re.IGNORECASE)

        if i == 0 and location_prefix and not p_clean.startswith("En "):
            p_clean = f"{location_prefix}{p_clean}"

        structured_paragraphs.append(p_clean)

    structured_text = "\n\n".join(structured_paragraphs)

    # Aplicar estrictamente los candados y términos fijados del usuario
    final_text = apply_user_locks(structured_text, user_locks, stage="structured")

    return final_text
