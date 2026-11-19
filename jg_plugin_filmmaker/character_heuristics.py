"""Heurísticas deterministas y grounding para detección de personajes."""

from __future__ import annotations

import re
from typing import Any

from jg_plugin_filmmaker.stopwords import CINEMATIC_STOPWORDS

__all__ = [
    "CINEMATIC_STOPWORDS",
    "is_cinematic_stopword",
    "verify_textual_grounding",
    "deterministic_extract_candidates",
]


def is_cinematic_stopword(name: str) -> bool:
    """Verifica si un nombre coincide con el catálogo de términos técnicos o acotaciones."""
    clean = re.sub(r"[^\w\s]", "", name).strip().upper()
    return clean in CINEMATIC_STOPWORDS


def verify_textual_grounding(name: str, source_text: str) -> bool:
    """Verifica deterministamente que el nombre o sus términos clave existan en el texto fuente."""
    if not name or not source_text:
        return False

    name_clean = name.strip()
    pattern = rf"\b{re.escape(name_clean)}\b"
    if re.search(pattern, source_text, re.IGNORECASE):
        return True

    tokens = [t for t in re.split(r"\s+", name_clean) if len(t) > 2]
    if tokens:
        for token in tokens:
            if not is_cinematic_stopword(token) and re.search(
                rf"\b{re.escape(token)}\b", source_text, re.IGNORECASE
            ):
                return True

    return False


def _match_fountain_headers(
    source_text: str, candidates: list[dict[str, Any]], seen: set[str]
) -> None:
    """Detecta encabezados de diálogo estilo Fountain (^NOMBRE$)."""
    matches = re.findall(
        r"^[ \t]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})(?:\s*\([^)]*\))?[ \t]*$",
        source_text,
        re.MULTILINE,
    )
    for m in matches:
        raw_name = m.strip()
        upper = raw_name.upper()
        if not is_cinematic_stopword(upper) and len(raw_name) >= 3:
            norm_name = raw_name.title()
            if norm_name.lower() not in seen:
                seen.add(norm_name.lower())
                candidates.append(
                    {
                        "name": norm_name,
                        "role": "Personaje con diálogo",
                        "is_speaking": True,
                        "bio": "Detectado en encabezado de diálogo cinematográfico.",
                        "evidence": f"{raw_name}",
                        "match_type": "deterministic_dialogue",
                        "confidence": 0.90,
                    }
                )


def _match_colon_dialogues(
    source_text: str, candidates: list[dict[str, Any]], seen: set[str]
) -> None:
    """Detecta sintaxis de diálogo con dos puntos (ej: 'Edurne: ¿Le has dado...?')."""
    matches = re.findall(r"^[ \t]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,25}):", source_text, re.MULTILINE)
    for m in matches:
        raw_name = m.strip()
        upper = raw_name.upper()
        if not is_cinematic_stopword(upper) and len(raw_name) >= 3:
            norm_name = raw_name.title()
            if norm_name.lower() not in seen:
                seen.add(norm_name.lower())
                candidates.append(
                    {
                        "name": norm_name,
                        "role": "Personaje con diálogo",
                        "is_speaking": True,
                        "bio": "Detectado en diálogo con delimitador.",
                        "evidence": f"{raw_name}:",
                        "match_type": "deterministic_dialogue_colon",
                        "confidence": 0.85,
                    }
                )


def _match_roles_with_articles(
    source_text: str, candidates: list[dict[str, Any]], seen: set[str]
) -> None:
    """Detecta roles explícitos con artículo (ej: 'el médico', 'la cajera')."""
    roles_regex = (
        r"\b(?:el|la|un|una)\s+(camarero|camarera|barman|polic[ií]a|agente|detective|inspector|"
        r"m[eé]dico|doctor|doctora|enfermero|enfermera|cirujano|cirujana|guardia|vigilante|"
        r"seguridad|portero|conserje|conductor|taxista|ch[oó]fer|cliente|cajero|cajera|"
        r"dependiente|dependienta|juez|fiscal|abogado|abogada|sacerdote|cura|monja|transe[uú]nte|viandante|chaval)\b"
    )
    for m in re.finditer(roles_regex, source_text, re.IGNORECASE):
        role_name = m.group(1).title()
        if role_name.lower() not in seen:
            seen.add(role_name.lower())
            candidates.append(
                {
                    "name": role_name,
                    "role": "Rol dramático secundario",
                    "is_speaking": False,
                    "bio": f"Oficio o rol detectado en la acción narrativa ({m.group(0)}).",
                    "evidence": m.group(0),
                    "match_type": "deterministic_role",
                    "confidence": 0.80,
                }
            )


def deterministic_extract_candidates(source_text: str) -> list[dict[str, Any]]:
    """Extrae candidatos deterministas mediante reglas sólidas para soporte offline y consenso."""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    _match_fountain_headers(source_text, candidates, seen)
    _match_colon_dialogues(source_text, candidates, seen)
    _match_roles_with_articles(source_text, candidates, seen)

    return candidates


def fallback_audit_decision(char_name: str, combined_text: str) -> dict[str, Any]:
    """Determina si el personaje está en uso según heurísticas deterministas seguras."""
    dialogue_pattern = rf"^[ \t]*{re.escape(char_name)}(?:\s*\(.*?\))?:?$"
    has_dialogue = bool(re.search(dialogue_pattern, combined_text, re.MULTILINE | re.IGNORECASE))

    words = char_name.split()
    is_common_phrase = len(words) >= 3 and any(
        w.lower() in {"a", "su", "en", "de", "con", "por", "el", "la"} for w in words
    )

    if has_dialogue:
        return {
            "in_use": True,
            "is_dramatic_entity": True,
            "confidence": 0.85,
            "reason": f"'{char_name}' aparece como interlocutor directo de diálogo en el texto.",
        }
    if is_common_phrase:
        return {
            "in_use": False,
            "is_dramatic_entity": False,
            "confidence": 0.80,
            "reason": f"'{char_name}' es una locución o frase descriptiva común, no un personaje dramático.",
        }

    return {
        "in_use": True,
        "is_dramatic_entity": True,
        "confidence": 0.70,
        "reason": f"'{char_name}' aparece mencionado en la acción narrativa.",
    }


__all__ = [
    "CINEMATIC_STOPWORDS",
    "deterministic_extract_candidates",
    "fallback_audit_decision",
    "is_cinematic_stopword",
    "verify_textual_grounding",
]
