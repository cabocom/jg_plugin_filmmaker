"""Motor de auditoría y detección de agujeros de guión (plot holes).

Analiza la secuencia narrativa cronológica de escenas y bloques del proyecto,
cotejando la consistencia dramática, la continuidad espacial y temporal,
y las motivaciones y presencia de los personajes de la Biblia.
Soporta inferencia semántica con LLM y motor determinista de reglas para CI/CD.
"""

import json
import re
from typing import Any

from jg_plugin_filmmaker.llm import get_active_llm, invoke_llm_text

PLOT_HOLE_SYSTEM_PROMPT = """Eres un Analista Dramático y Script Doctor cinematográfico profesional de alto nivel.
Tu misión es auditar una secuencia ordenada de bloques de un guión o tratamiento y detectar AGUJEROS ARGUMENTALES O DE CONTINUIDAD GENUINOS (plot holes).

DIRECTRICES Y REGLAS ESTRICTAS:
1. FOCO EN CONTINUIDAD Y DRAMATURGIA REAL:
   - Detecta contradicciones espaciales graves (personaje en dos sitios a la vez).
   - Detecta rupturas temporales inexplicadas.
   - Detecta acciones de personajes imposibles según su estado físico o la trama previa.
   - Ignora variaciones estilísticas, erratas tipográficas o capitalizaciones (NO son agujeros dramáticos).
2. CONTEXTO DE PERSONAJES:
{characters_context}
3. CONTEXTO DE LOCALIZACIONES:
{locations_context}
4. FORMATO DE SALIDA:
   Devuelve ÚNICAMENTE un objeto JSON válido con la siguiente estructura, sin texto adicional, prefacios ni comentarios:
   {{
     "detected_holes": [
       {{
         "block_id": "identificador_del_bloque",
         "reason": "Explicación concisa y técnica de la inconsistencia dramática."
       }}
     ]
   }}
"""


def detect_plot_holes(
    blocks: list[dict[str, Any]],
    characters: list[dict[str, Any]] | None = None,
    locations: list[dict[str, Any]] | None = None,
    llm_client: Any = None,
) -> list[dict[str, Any]]:
    """Audita la lista secuencial de bloques y devuelve los agujeros detectados."""
    if not blocks:
        return []

    active_llm = get_active_llm(llm_client)
    if active_llm is not None:
        chars_desc = "Sin personajes específicos."
        if characters:
            chars_desc = "\n".join(
                f"- {c.get('name', 'P')}: {c.get('bio', '')}"
                for c in characters
                if isinstance(c, dict)
            )

        locs_desc = "Sin localizaciones específicas."
        if locations:
            locs_desc = "\n".join(
                f"- {loc.get('name', 'L')} ({loc.get('type', 'INT')})"
                for loc in locations
                if isinstance(loc, dict)
            )

        blocks_summary = []
        for idx, b in enumerate(blocks):
            b_id = str(b.get("id", "") or f"block_{idx + 1}")
            b_text = str(
                b.get("text")
                or b.get("screenplay_content")
                or b.get("structured_text")
                or b.get("raw_text")
                or b.get("content")
                or ""
            ).strip()
            blocks_summary.append(f"[BLOQUE ID: {b_id}]\n{b_text}\n")

        user_prompt = "SECUENCIA DE BLOQUES NARRATIVOS:\n" + "\n".join(blocks_summary)

        sys_prompt = PLOT_HOLE_SYSTEM_PROMPT.format(
            characters_context=chars_desc,
            locations_context=locs_desc,
        )

        output = invoke_llm_text(active_llm, sys_prompt, user_prompt)
        if output:
            try:
                # Extraer bloque json si viene con backticks
                json_match = re.search(r"\{.*\}", output, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    holes = parsed.get("detected_holes", [])
                    if isinstance(holes, list):
                        valid_holes = []
                        valid_ids = {
                            str(b.get("id", "") or f"block_{idx + 1}")
                            for idx, b in enumerate(blocks)
                        }
                        for h in holes:
                            if isinstance(h, dict) and str(h.get("block_id", "")) in valid_ids:
                                valid_holes.append(
                                    {
                                        "block_id": str(h["block_id"]),
                                        "reason": str(h.get("reason", "Inconsistencia dramática")),
                                    }
                                )
                        return valid_holes
            except Exception:
                pass

    # --- MOTOR DETERMINISTA HEURÍSTICO (Fallback offline / test) ---
    detected: list[dict[str, Any]] = []
    seen_alive_characters: dict[str, str] = {}  # nombre -> block_id

    for idx, b in enumerate(blocks):
        b_id = str(b.get("id", "") or f"block_{idx + 1}")
        b_text = str(
            b.get("text")
            or b.get("screenplay_content")
            or b.get("structured_text")
            or b.get("raw_text")
            or b.get("content")
            or ""
        ).lower()

        # 1. Regla: Incoherencia de teletransportación o contradicción flagrante explícita
        if "teletransporta" in b_text or "aparece de la nada" in b_text:
            detected.append(
                {
                    "block_id": b_id,
                    "reason": "Ruptura de continuidad espacial: personaje aparece de la nada sin justificación de tránsito.",
                }
            )

        # 2. Regla: Personaje que muere y luego dialoga o reaparece vivo
        if "muere" in b_text or "fallece" in b_text or "cadáver" in b_text:
            for c in characters or []:
                c_name = str(c.get("name", "")).lower()
                if c_name and c_name in b_text:
                    seen_alive_characters[c_name] = "dead"

        for c_name, status in seen_alive_characters.items():
            if status == "dead" and c_name in b_text and ("camina" in b_text or "dice" in b_text):
                detected.append(
                    {
                        "block_id": b_id,
                        "reason": f"Agujero dramático crítico: el personaje '{c_name.capitalize()}' falleció en una escena anterior pero interviene activamente.",
                    }
                )

    return detected
