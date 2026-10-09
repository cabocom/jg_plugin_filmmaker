"""Motor de formateo estándar cinematográfico (Fountain).

Convierte tratamiento narrativo a formato de guión literario estándar:
encabezados de escena, acción, personajes en mayúsculas, acotaciones y diálogos.
Resuelve semánticamente el estilo indirecto mediante LLM o mediante fallback heurístico.
"""

import re
from typing import Any

from jg_plugin_filmmaker.llm import get_active_llm, invoke_llm_text
from jg_plugin_filmmaker.structuring import apply_user_locks

SCREENPLAY_SYSTEM_PROMPT = """Eres un guionista cinematográfico profesional especializado en formato estándar de guión (Fountain / Final Draft estándar de la industria).
Tu cometido es convertir un tratamiento dramático en un GUIÓN LITERARIO con estructura cinematográfica impecable.

DIRECTRICES Y REGLAS ESTRICTAS:
1. ENCABEZADO DE ESCENA (Slugline): Comienza siempre con el encabezado canónico en mayúsculas:
{slugline}
(ejemplo: INT. BAR CENTRAL - NOCHE 1).
2. ACCIÓN NARRATIVA: Párrafos concisos en presente de indicativo describiendo lo que se ve y se escucha. Nombres de personajes en mayúsculas en su primera aparición o acción relevante.
3. RESOLUCIÓN DE ESTILO INDIRECTO Y DIÁLOGOS:
   - Si la narración contiene oraciones donde un personaje habla, pregunta o dice algo (ej: "Javier mira a Juan con miedo y le dice que ya están llegando" o "Juan le pregunta qué quién está llegando"), TRANSFÓRMALO OBLIGATORIAMENTE en diálogo dramático hablado directo:
     JAVIER
     (con miedo)
     Ya están llegando.

     JUAN
     ¿Quién está llegando?
   - NOMBRE DEL PERSONAJE: Siempre en una línea independiente en MAYÚSCULAS antes de su diálogo.
   - ACOTACIONES: Breves, en minúsculas y entre paréntesis (ej: "(asustado)", "(pausa)").
   - INFERENCIA DE PERSONAJES: Si en la acción interviene un personaje que dialoga (incluso si no estaba previamente dado de alta en la biblia, como "Juan"), infiere su nombre canónico, colócalo en mayúsculas y dale su bloque de diálogo correspondiente.
4. PURGA DE PREFIJOS: Elimina prefijos redundantes propios del tratamiento (ej: "En BAR CENTRAL:").
5. CANDADOS Y TÉRMINOS FIJADOS (REGLA INMUTABLE):
{pinned_terms_context}
6. FORMATO DE SALIDA: Devuelve ÚNICAMENTE el guión literario formateado en Fountain, sin notas explicativas, prefacios ni comentarios.
"""


def format_screenplay(
    structured_text: str,
    characters_context: list[dict[str, Any]] | None = None,
    location_context: dict[str, Any] | None = None,
    user_locks: dict[str, Any] | None = None,
    llm_client: Any = None,
) -> str:
    """Convierte tratamiento estructurado en guión literario en formato Fountain."""
    if not structured_text or not structured_text.strip():
        return ""

    text = structured_text.strip()

    # Construir slugline previsto
    slugline = "INT. LOCALIZACION - DIA 1"
    if location_context and isinstance(location_context, dict):
        loc_name = location_context.get("name", "LOCALIZACION").strip().upper()
        loc_type = location_context.get("type", "INT").strip().upper()
        time_day = location_context.get("time_of_day", "DIA").strip().upper()
        slugline = f"{loc_type}. {loc_name} - {time_day} 1"

    # Intentar inferencia semántica con LLM si está disponible y activo
    active_llm = get_active_llm(llm_client)
    if active_llm is not None:
        locks_desc = "Ningún término fijado."
        if user_locks and isinstance(user_locks, dict):
            pinned = user_locks.get("pinned_terms", {})
            if pinned:
                locks_desc = "\n".join(
                    f"- Sustituir '{k}' siempre por '{v}'" for k, v in pinned.items()
                )

        sys_prompt = SCREENPLAY_SYSTEM_PROMPT.format(
            slugline=slugline,
            pinned_terms_context=locks_desc,
        )

        user_prompt = f"TRATAMIENTO A CONVERTIR EN GUIÓN:\n{text}"

        llm_output = invoke_llm_text(active_llm, sys_prompt, user_prompt)
        if llm_output and llm_output.strip():
            return apply_user_locks(llm_output.strip(), user_locks, stage="screenplay")

    # --- FALLBACK DETERMINISTA HEURÍSTICO (Modo Test / Offline / Cero Tokens) ---
    char_names: list[str] = []
    if characters_context and isinstance(characters_context, list):
        for c in characters_context:
            if isinstance(c, dict) and "name" in c and c["name"]:
                char_names.append(c["name"].strip())

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    screenplay_blocks: list[str] = []

    if slugline and not any(p.startswith(("INT.", "EXT.", "INT/EXT.")) for p in paragraphs):
        screenplay_blocks.append(slugline)

    dialogue_pattern = re.compile(
        r"^(?P<speaker>[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?):\s*(?:(?:\((?P<parenthetical>[^\)]+)\)\s*)?)(?P<dialogue>.+)$"
    )

    quote_pattern = re.compile(
        r'^(?P<speaker>[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s+(?:dice|responde|susurra|grita|afirma)\s*:\s*["«](?P<dialogue>[^"»]+)["»]$',
        re.IGNORECASE,
    )

    for p in paragraphs:
        if p.startswith(("INT.", "EXT.", "INT/EXT.")):
            screenplay_blocks.append(p.upper())
            continue

        # Limpiar prefijos de tratamiento "En LOCALIZACION:"
        clean_p = re.sub(r"^En\s+[^:]+:\s*", "", p)

        # Detectar diálogo por formato "PERSONAJE: (acotación) diálogo"
        m_dialogue = dialogue_pattern.match(clean_p)
        if m_dialogue:
            speaker = m_dialogue.group("speaker").strip().upper()
            parenthetical = m_dialogue.group("parenthetical")
            dialogue = m_dialogue.group("dialogue").strip()

            screenplay_blocks.append(speaker)
            if parenthetical:
                screenplay_blocks.append(f"({parenthetical.strip().lower()})")
            screenplay_blocks.append(dialogue)
            continue

        # Detectar diálogo por formato "Personaje dice: 'Diálogo'"
        m_quote = quote_pattern.match(clean_p)
        if m_quote:
            speaker = m_quote.group("speaker").strip().upper()
            dialogue = m_quote.group("dialogue").strip()

            screenplay_blocks.append(speaker)
            screenplay_blocks.append(dialogue)
            continue

        # Párrafo de acción narrativa: poner en mayúsculas los personajes
        action_line = clean_p
        for name in char_names:
            pattern = rf"\b{re.escape(name)}\b"
            action_line = re.sub(pattern, name.upper(), action_line, flags=re.IGNORECASE)

        screenplay_blocks.append(action_line)

    screenplay_output = "\n\n".join(screenplay_blocks)
    return apply_user_locks(screenplay_output, user_locks, stage="screenplay")
