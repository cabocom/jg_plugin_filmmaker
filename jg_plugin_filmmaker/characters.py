"""Motor de inteligencia dramática para detección y auditoría de personajes.

Combina análisis semántico mediante LLM (capaz de detectar personajes mudos,
parlantes y contextuales, y de descartar acotaciones de acción y efectos)
con una capa de grounding determinista (anti-alucinación, verificación de
presencia física en texto y catálogo de stopwords técnicas de rodaje).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from jg_plugin_filmmaker.llm import get_active_llm, invoke_llm_text

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. Catálogo Determinista de Stopwords Técnicas y Falsos Positivos Cinematográficos
# ==============================================================================

CINEMATIC_STOPWORDS = {
    # Encabezados, sluglines y estructura
    "INT",
    "EXT",
    "INT/EXT",
    "I/E",
    "EST",
    "ESCENA",
    "BLOQUE",
    "SECUENCIA",
    "DÍA",
    "DIA",
    "NOCHE",
    "TARDE",
    "MAÑANA",
    "CONTINUA",
    "CONTINUO",
    "MOMENTOS DESPUÉS",
    "MOMENTOS DESPUES",
    # Transiciones y montaje
    "CORTE",
    "CORTE A",
    "CORTE A NEGRO",
    "FUNDIDO",
    "FUNDIDO A",
    "FUNDIDO EN NEGRO",
    "DISUELVE A",
    "FADE",
    "FADE IN",
    "FADE OUT",
    "SMASH CUT",
    "MATCH CUT",
    "TRANSICIÓN",
    "TRANSICION",
    "CRÉDITOS",
    "CREDITOS",
    "FIN",
    "FINAL",
    "INICIO",
    # Planos de cámara
    "PLANO",
    "PLANOS",
    "PLANO DETALLE",
    "PRIMER PLANO",
    "PLANO MEDIO",
    "PLANO GENERAL",
    "PLANO AMERICANO",
    "GRAN PLANO GENERAL",
    "CONTRA-PLANO",
    "CAMARA",
    "CÁMARA",
    "PANORÁMICA",
    "TRAVELLING",
    "ZOOM",
    # Sonido y voz técnica
    "SONIDO EN OFF",
    "SONIDO OFF",
    "SONIDO",
    "SONIDOS",
    "VOZ EN OFF",
    "VOZ OFF",
    "VOZ",
    "V.O.",
    "VO",
    "O.S.",
    "OS",
    "OFF",
    "EFECTO",
    "EFECTOS",
    "EFECTO DE SONIDO",
    "MÚSICA",
    "MUSICA",
    "BANDA SONORA",
    "SILENCIO",
    "SILENCIO ABSOLUTO",
    "CHOF",
    "CRASH",
    "BEEP",
    "TIC TAC",
    # Acciones físicas verbales comunes frecuentemente confundidas con personajes
    "MIRA A SU ALREDEDOR",
    "MIRANDO A SU ALREDEDOR",
    "MIRA ALREDEDOR",
    "MIRA A",
    "SE GIRA",
    "SE LEVANTA",
    "DA UN PASO",
    "DA UN PASO ATRÁS",
    "SONRÍE",
    "LLORA",
    "TRAGA SALIVA",
    "SUSPIRA",
    "CIERRA LOS OJOS",
    "ABRE LOS OJOS",
    # Conectores y artículos aislados
    "EL",
    "LA",
    "LOS",
    "LAS",
    "UN",
    "UNA",
    "UNOS",
    "UNAS",
    "DE",
    "DEL",
    "AL",
    "EN",
    "POR",
    "PARA",
    "CON",
    "SIN",
    "SOBRE",
    "TRAS",
    "DURANTE",
    "MIENTRAS",
    "CUANDO",
    "DONDE",
    "COMO",
    "PERO",
    "AUNQUE",
    "TODO",
    "TODOS",
    "NADA",
    "NADIE",
}


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


# ==============================================================================
# 2. Funciones de Grounding Determinista
# ==============================================================================


def is_cinematic_stopword(name: str) -> bool:
    """Verifica si un nombre coincide con el catálogo de términos técnicos o acotaciones."""
    clean = re.sub(r"[^\w\s]", "", name).strip().upper()
    return clean in CINEMATIC_STOPWORDS


def verify_textual_grounding(name: str, source_text: str) -> bool:
    """Verifica deterministamente que el nombre o sus términos clave existan en el texto fuente.

    Previene alucinaciones completas del LLM.
    """
    if not name or not source_text:
        return False

    name_clean = name.strip()
    # Búsqueda exacta de palabra completa con case-insensitive
    pattern = rf"\b{re.escape(name_clean)}\b"
    if re.search(pattern, source_text, re.IGNORECASE):
        return True

    # Para nombres compuestos, verificar si al menos el término principal está presente
    tokens = [t for t in re.split(r"\s+", name_clean) if len(t) > 2]
    if tokens:
        for token in tokens:
            if not is_cinematic_stopword(token) and re.search(
                rf"\b{re.escape(token)}\b", source_text, re.IGNORECASE
            ):
                return True

    return False


def deterministic_extract_candidates(source_text: str) -> list[dict[str, Any]]:
    """Extrae candidatos deterministas mediante reglas sólidas para soporte offline y consenso."""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    # 1. Encabezados de diálogo estilo Fountain (^NOMBRE$)
    fountain_matches = re.findall(
        r"^[ \t]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})(?:\s*\([^)]*\))?[ \t]*$",
        source_text,
        re.MULTILINE,
    )
    for m in fountain_matches:
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

    # 2. Sintaxis de diálogo con dos puntos (ej: "Edurne: ¿Le has dado...?")
    colon_matches = re.findall(r"^[ \t]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,25}):", source_text, re.MULTILINE)
    for m in colon_matches:
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

    # 3. Roles explícitos con artículo (ej: "el médico", "la cajera", "un guardia")
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

    return candidates


# ==============================================================================
# 3. Métodos Principales de Inferencia y Consenso Híbrido
# ==============================================================================


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

    # 1. Candidatos deterministas (línea base)
    deterministic_candidates = deterministic_extract_candidates(text)
    det_map = {c["name"].lower(): c for c in deterministic_candidates}

    active_llm = get_active_llm(llm_client)
    ai_candidates: list[dict[str, Any]] = []

    # 2. Inferencia Semántica con LLM si está disponible
    if active_llm is not None:
        user_prompt = f"FRAGMENTO NARRATIVO / GUION:\n{text.strip()}"
        output = invoke_llm_text(
            active_llm,
            CHARACTER_EXTRACTION_SYSTEM_PROMPT,
            user_prompt,
        )
        if output:
            try:
                json_match = re.search(r"\{.*\}", output, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    raw_chars = parsed.get("characters", [])
                    if isinstance(raw_chars, list):
                        for c in raw_chars:
                            if not isinstance(c, dict):
                                continue
                            name = str(c.get("name", "")).strip()
                            if not name or len(name) < 2:
                                continue

                            # Filtro 1: Stopwords cinematográficas
                            if is_cinematic_stopword(name):
                                logger.info(
                                    "Personaje descartado por stopword cinematográfica: '%s'",
                                    name,
                                )
                                continue

                            # Filtro 2: Grounding en texto original (anti-alucinación)
                            if not verify_textual_grounding(name, text):
                                logger.warning(
                                    "Personaje descartado por falta de grounding en texto: '%s'",
                                    name,
                                )
                                continue

                            norm_name = name.title()
                            ai_candidates.append(
                                {
                                    "name": norm_name,
                                    "role": str(c.get("role", "Personaje detectado")),
                                    "is_speaking": bool(c.get("is_speaking", False)),
                                    "bio": str(c.get("bio", "Personaje detectado por IA.")),
                                    "evidence": str(c.get("evidence", "")),
                                    "confidence": 0.95,
                                    "match_type": "ai_semantic",
                                }
                            )
            except Exception as e:
                logger.error("Error parseando respuesta JSON de IA en extract_characters: %s", e)

    # 3. Matriz de Consenso e Integración
    final_characters: list[dict[str, Any]] = []
    seen_final: set[str] = set()

    # Si la IA obtuvo resultados con grounding, priorizamos el consenso
    if ai_candidates:
        for ai_c in ai_candidates:
            key = ai_c["name"].lower()
            if key in seen_final:
                continue
            seen_final.add(key)

            if key in det_map:
                # Match IA + Determinismo: Máxima confianza
                merged = {**det_map[key], **ai_c}
                merged["match_type"] = "consensus_strong"
                merged["confidence"] = 0.99
                final_characters.append(merged)
            else:
                # Detectado por IA (ej. personaje silente o descriptivo) con grounding
                ai_c["match_type"] = "ai_grounded"
                final_characters.append(ai_c)

        # Añadir candidatos deterministas de alta confianza que la IA pudiera haber omitido
        for det_k, det_c in det_map.items():
            if det_k not in seen_final and not is_cinematic_stopword(det_c["name"]):
                seen_final.add(det_k)
                final_characters.append(det_c)
        strategy = "hybrid_consensus"
    else:
        # Modo Fallback Determinista seguro
        for det_c in deterministic_candidates:
            if not is_cinematic_stopword(det_c["name"]):
                final_characters.append(det_c)
        strategy = "deterministic_fallback"

    # Marcar si ya existen en la biblia
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

    # 1. Filtro inmediato por Stopwords técnicas
    if is_cinematic_stopword(char_name):
        return {
            "in_use": False,
            "is_dramatic_entity": False,
            "confidence": 1.0,
            "reason": f"'{char_name}' es un término o acotación técnica reservada, no un personaje.",
        }

    texts = [scene_texts] if isinstance(scene_texts, str) else scene_texts
    combined_text = "\n---\n".join([t for t in texts if t and t.strip()])

    # 2. Filtro determinista rápido de presencia física
    if not verify_textual_grounding(char_name, combined_text):
        return {
            "in_use": False,
            "is_dramatic_entity": False,
            "confidence": 1.0,
            "reason": f"El nombre '{char_name}' no aparece físicamente en ningún bloque.",
        }

    active_llm = get_active_llm(llm_client)

    # 3. Disambiguación Semántica con LLM
    if active_llm is not None:
        user_prompt = (
            f"PERSONAJE A AUDITAR: {char_name}\n\n"
            f"TEXTO DEL GUION / ESCENAS:\n{combined_text[:4000]}"
        )
        output = invoke_llm_text(
            active_llm,
            CHARACTER_AUDIT_SYSTEM_PROMPT,
            user_prompt,
        )
        if output:
            try:
                json_match = re.search(r"\{.*\}", output, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    return {
                        "in_use": bool(parsed.get("in_use", False)),
                        "is_dramatic_entity": bool(parsed.get("is_dramatic_entity", False)),
                        "confidence": float(parsed.get("confidence", 0.90)),
                        "reason": str(parsed.get("reason", "Auditoría semántica completada.")),
                    }
            except Exception as e:
                logger.error("Error parseando respuesta JSON de IA en audit_character_usage: %s", e)

    # 4. Fallback Determinista Inteligente
    # Comprobar si aparece como encabezado de diálogo o si solo está en minúsculas en medio de una frase
    dialogue_pattern = rf"^[ \t]*{re.escape(char_name)}(?:\s*\(.*?\))?:?$"
    has_dialogue = bool(re.search(dialogue_pattern, combined_text, re.MULTILINE | re.IGNORECASE))

    # Comprobar si parece una frase verbal común (más de 2 palabras que no sea un nombre con rol)
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

    # Si no es frase común y aparece en el texto, asumimos en uso conservadoramente
    return {
        "in_use": True,
        "is_dramatic_entity": True,
        "confidence": 0.70,
        "reason": f"'{char_name}' aparece mencionado en la acción narrativa.",
    }
