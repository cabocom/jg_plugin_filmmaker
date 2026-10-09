"""Motor de formateo estándar cinematográfico (Fountain).

Convierte tratamiento narrativo a formato de guión literario estándar:
encabezados de escena, acción, personajes en mayúsculas, acotaciones y diálogos.
"""

import re
from typing import Any

from jg_plugin_filmmaker.structuring import apply_user_locks


def format_screenplay(
    structured_text: str,
    characters_context: list[dict[str, Any]] | None = None,
    location_context: dict[str, Any] | None = None,
    user_locks: dict[str, Any] | None = None,
) -> str:
    """Convierte tratamiento estructurado en guión literario en formato Fountain."""
    if not structured_text or not structured_text.strip():
        return ""

    text = structured_text.strip()

    # Recoger nombres conocidos de personajes
    char_names: list[str] = []
    if characters_context and isinstance(characters_context, list):
        for c in characters_context:
            if isinstance(c, dict) and "name" in c and c["name"]:
                char_names.append(c["name"].strip())

    # Construir encabezado de escena si procede
    slugline = ""
    if location_context and isinstance(location_context, dict):
        loc_name = location_context.get("name", "ESCENARIO").strip().upper()
        loc_type = location_context.get("type", "INT").strip().upper()
        time_day = location_context.get("time_of_day", "DÍA").strip().upper()
        slugline = f"{loc_type}. {loc_name} - {time_day} 1"

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
        # Si ya es un encabezado
        if p.startswith(("INT.", "EXT.", "INT/EXT.")):
            screenplay_blocks.append(p.upper())
            continue

        # Detectar diálogo por formato "PERSONAJE: (acotación) diálogo"
        m_dialogue = dialogue_pattern.match(p)
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
        m_quote = quote_pattern.match(p)
        if m_quote:
            speaker = m_quote.group("speaker").strip().upper()
            dialogue = m_quote.group("dialogue").strip()

            screenplay_blocks.append(speaker)
            screenplay_blocks.append(dialogue)
            continue

        # Párrafo de acción narrativa: poner en mayúsculas los personajes si aparecen
        action_line = p
        for name in char_names:
            pattern = rf"\b{re.escape(name)}\b"
            action_line = re.sub(pattern, name.upper(), action_line, flags=re.IGNORECASE)

        screenplay_blocks.append(action_line)

    screenplay_output = "\n\n".join(screenplay_blocks)

    # Aplicar user_locks para stage "screenplay"
    final_output = apply_user_locks(screenplay_output, user_locks, stage="screenplay")

    return final_output
