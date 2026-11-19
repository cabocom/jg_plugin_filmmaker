"""Motor de inteligencia dramática para detección y auditoría de personajes."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from jg_plugin_filmmaker.character_heuristics import (
    CINEMATIC_STOPWORDS,
    deterministic_extract_candidates,
    fallback_audit_decision,
    is_cinematic_stopword,
    verify_textual_grounding,
)
from jg_plugin_filmmaker.llm import get_active_llm, invoke_llm_text, is_mock_mode

logger = logging.getLogger(__name__)

CHARACTER_EXTRACTION_SYSTEM_PROMPT = """Eres un Analista Dramático y Script Doctor cinematográfico profesional de primer nivel.
Tu misión es leer un texto dramático (tratamiento o guion cinematográfico) e IDENTIFICAR EXCLUSIVAMENTE A LOS PERSONAJES DRAMÁTICOS REALES.

DIRECTRICES Y REGLAS ESTRICTAS:
1. PERSONAJES VÁLIDOS:
   - Personajes con líneas de diálogo habladas (ej: EDURNE, VIANDANTE, TRANSEÚNTE).
   - Personajes SILENCIOSOS O MUDOS que intervienen activamente en la escena realizando acciones físicas o interactuando como sujetos (ej: un guardia que bloquea el paso, un chaval en un banco, un anciano comiendo).
   - Roles dramáticos u oficios definidos (ej: El Médico, La Cajera, El Conductor).

2. ESTRICTAMENTE PROHIBIDO (NO SON PERSONAJES):
   - Acciones verbales o descripciones de acotación (ej: "Mira a su alrededor", "Da un paso atrás", "Traga saliva").
   - Indicaciones técnicas de sonido o música (ej: "Sonido en off", "Voz en off", "Música relajante").
   - Transiciones y tiros de cámara (ej: "Corte a negro", "Plano detalle", "Créditos").
   - Objetos, pantallas o animales no antropomórficos (salvo que sean entidades dramáticas activas).

3. FORMATO DE SALIDA:
   Devuelve ÚNICAMENTE un objeto JSON válido sin texto adicional, sin bloques de código ni prefacios:
   {
     "characters": [
       {
         "name": "Nombre canónico en Title Case (ej: Edurne, Transeúnte)",
         "role": "Protagonista | Secundario | Figuración con acción",
         "is_speaking": true,
         "bio": "Breve descripción de su rol dramático en la escena.",
         "evidence": "Cita textual breve del texto donde aparece."
       }
     ]
   }
"""

CHARACTER_AUDIT_SYSTEM_PROMPT = """Eres un Analista Dramático y Auditor de Guion cinematográfico.
Tu misión es determinar si el NOMBRE especificado corresponde a un PERSONAJE DRAMÁTICO REAL que interviene o está presente como entidad en el fragmento de guion provisto, o si por el contrario es un FALSO POSITIVO (una acción verbal, un efecto de sonido o una coincidencia casual de palabras).

REGLA CLAVE DE DESAMBIGUACIÓN:
- Si el nombre auditado es "Mira A Su Alrededor" y en el texto aparece "Edurne mira a su alrededor", la aparición NO ES UN PERSONAJE, sino una acción en prosa de Edurne. En ese caso 'in_use' DEBE SER FALSE.
- Si el nombre auditado es "Sonido En Off" y en el texto aparece "Sonido en off de agua...", NO ES UN PERSONAJE. En ese caso 'in_use' DEBE SER FALSE.
- Solo debes marcar 'in_use': true si la entidad auditada participa o existe en la escena como sujeto vivo o dramático (sea hablando o en silencio).

FORMATO DE SALIDA (ÚNICAMENTE JSON):
{
  "in_use": false,
  "is_dramatic_entity": false,
  "confidence": 0.98,
  "reason": "Explicación concisa y técnica de por qué no es un personaje dramático en esta escena."
}
"""


def _parse_ai_character_candidate(c: dict[str, Any], text: str) -> dict[str, Any] | None:
    """Valida y estructura un candidato de personaje propuesto por IA."""
    name = str(c.get("name", "")).strip()
    if not name or len(name) < 2:
        return None
    if is_cinematic_stopword(name):
        logger.info("Personaje descartado por stopword cinematográfica: '%s'", name)
        return None
    if not verify_textual_grounding(name, text):
        logger.warning("Personaje descartado por falta de grounding en texto: '%s'", name)
        return None

    return {
        "name": name.title(),
        "role": str(c.get("role", "Personaje detectado")),
        "is_speaking": bool(c.get("is_speaking", False)),
        "bio": str(c.get("bio", "Personaje detectado por IA.")),
        "evidence": str(c.get("evidence", "")),
        "confidence": 0.95,
        "match_type": "ai_semantic",
    }


def _query_llm_characters(active_llm: Any, text: str) -> list[dict[str, Any]]:
    """Consulta al LLM e interpreta candidatos a personajes."""
    user_prompt = f"FRAGMENTO NARRATIVO / GUION:\n{text.strip()}"
    output = invoke_llm_text(active_llm, CHARACTER_EXTRACTION_SYSTEM_PROMPT, user_prompt)
    if not output or not output.strip():
        raise RuntimeError("El modelo LLM retornó una respuesta vacía en extracción de personajes.")

    json_match = re.search(r"\{.*\}", output, re.DOTALL)
    if not json_match:
        raise RuntimeError("La salida del LLM no contiene un objeto JSON válido.")
    try:
        parsed = json.loads(json_match.group(0))
    except Exception as e:
        raise RuntimeError(f"Error parseando JSON de personajes del LLM: {e}") from e

    raw_chars = parsed.get("characters", [])
    if not isinstance(raw_chars, list):
        raise RuntimeError("Formato inválido de characters en respuesta del LLM.")

    candidates: list[dict[str, Any]] = []
    for c in raw_chars:
        if isinstance(c, dict):
            cand = _parse_ai_character_candidate(c, text)
            if cand:
                candidates.append(cand)
    return candidates


def _merge_consensus_characters(
    ai_candidates: list[dict[str, Any]],
    deterministic_candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    """Combina candidatos de IA y deterministas en una lista consolidada."""
    final_characters: list[dict[str, Any]] = []
    seen: set[str] = set()
    det_map = {c["name"].lower(): c for c in deterministic_candidates}

    if ai_candidates:
        for ai_c in ai_candidates:
            key = ai_c["name"].lower()
            if key in seen:
                continue
            seen.add(key)
            if key in det_map:
                merged = {
                    **det_map[key],
                    **ai_c,
                    "match_type": "consensus_strong",
                    "confidence": 0.99,
                }
                final_characters.append(merged)
            else:
                final_characters.append({**ai_c, "match_type": "ai_grounded"})

        for det_k, det_c in det_map.items():
            if det_k not in seen and not is_cinematic_stopword(det_c["name"]):
                seen.add(det_k)
                final_characters.append(det_c)
        return final_characters, "hybrid_consensus"

    for det_c in deterministic_candidates:
        if not is_cinematic_stopword(det_c["name"]):
            final_characters.append(det_c)
    return final_characters, "deterministic_fallback"


def extract_characters(
    text: str,
    existing_characters: list[dict[str, Any]] | None = None,
    llm_client: Any = None,
) -> dict[str, Any]:
    """Extrae personajes mediante ensamble híbrido (IA semántica + grounding determinista)."""
    if not text or not text.strip():
        return {"characters": [], "consensus_summary": {"total": 0, "strategy": "empty"}}

    existing_names = {
        c.get("name", "").strip().lower()
        for c in (existing_characters or [])
        if isinstance(c, dict) and c.get("name")
    }

    deterministic_candidates = deterministic_extract_candidates(text)
    active_llm = get_active_llm(llm_client)
    if active_llm is not None:
        ai_candidates = _query_llm_characters(active_llm, text)
    elif is_mock_mode():
        ai_candidates = []
    else:
        raise RuntimeError("No hay cliente LLM disponible ni entorno mock habilitado.")

    final_characters, strategy = _merge_consensus_characters(
        ai_candidates, deterministic_candidates
    )

    for char in final_characters:
        char["already_in_bible"] = char["name"].lower() in existing_names

    return {
        "characters": final_characters,
        "consensus_summary": {
            "total": len(final_characters),
            "strategy": strategy,
            "ai_detected": len(ai_candidates),
            "deterministic_anchors": len(deterministic_candidates),
        },
    }


def _query_llm_audit(active_llm: Any, char_name: str, combined_text: str) -> dict[str, Any]:
    """Ejecuta la desambiguación semántica del personaje mediante el LLM."""
    user_prompt = (
        f"PERSONAJE A AUDITAR: {char_name}\n\nTEXTO DEL GUION / ESCENAS:\n{combined_text[:4000]}"
    )
    output = invoke_llm_text(active_llm, CHARACTER_AUDIT_SYSTEM_PROMPT, user_prompt)
    if not output or not output.strip():
        raise RuntimeError("El modelo LLM retornó una respuesta vacía en auditoría de personaje.")

    json_match = re.search(r"\{.*\}", output, re.DOTALL)
    if not json_match:
        raise RuntimeError("La respuesta del LLM no contiene un JSON válido.")
    try:
        parsed = json.loads(json_match.group(0))
    except Exception as e:
        raise RuntimeError(f"Error parseando JSON de auditoría de personajes del LLM: {e}") from e

    return {
        "in_use": bool(parsed.get("in_use", False)),
        "is_dramatic_entity": bool(parsed.get("is_dramatic_entity", False)),
        "confidence": float(parsed.get("confidence", 0.90)),
        "reason": str(parsed.get("reason", "Auditoría semántica completada.")),
    }


def audit_character_usage(
    character_name: str,
    scene_texts: list[str] | str,
    llm_client: Any = None,
) -> dict[str, Any]:
    """Audita si un personaje interviene realmente como entidad dramática o si es un falso positivo."""
    char_name = character_name.strip()
    if not char_name:
        return {
            "in_use": False,
            "is_dramatic_entity": False,
            "confidence": 1.0,
            "reason": "Nombre de personaje vacío.",
        }

    if is_cinematic_stopword(char_name):
        return {
            "in_use": False,
            "is_dramatic_entity": False,
            "confidence": 1.0,
            "reason": f"'{char_name}' es un término o acotación técnica reservada, no un personaje.",
        }

    texts = [scene_texts] if isinstance(scene_texts, str) else scene_texts
    combined_text = "\n---\n".join([t for t in texts if t and t.strip()])

    if not verify_textual_grounding(char_name, combined_text):
        return {
            "in_use": False,
            "is_dramatic_entity": False,
            "confidence": 1.0,
            "reason": f"El nombre '{char_name}' no aparece físicamente en ningún bloque.",
        }

    active_llm = get_active_llm(llm_client)
    if active_llm is not None:
        return _query_llm_audit(active_llm, char_name, combined_text)

    if is_mock_mode():
        return fallback_audit_decision(char_name, combined_text)

    raise RuntimeError("No hay cliente LLM disponible ni entorno mock habilitado.")


__all__ = [
    "CINEMATIC_STOPWORDS",
    "audit_character_usage",
    "deterministic_extract_candidates",
    "extract_characters",
    "is_cinematic_stopword",
    "verify_textual_grounding",
]
