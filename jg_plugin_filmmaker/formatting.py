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


def refine_dialogue_to_direct_speech(text: str, verb: str) -> str:
    """Nodo de refinamiento dramático: convierte tercera persona narrativa a segunda/primera persona directa."""
    res = text.strip()
    res = re.sub(r"^que\s+", "", res, flags=re.IGNORECASE)
    res = re.sub(r"(?<=[.?!])\s*que\s+", " ", res, flags=re.IGNORECASE)

    # Iteración 1: Pronombres y reflexivos a interlocución directa
    replacements = [
        (r"\bse\s+ha\s+comportado\b", "te has comportado"),
        (r"\bse\s+ha\s+portado\b", "te has portado"),
        (r"\bse\s+comportó\b", "te comportaste"),
        (r"\bvolverse\s+con\s+él\b", "volverte conmigo"),
        (r"\birse\s+con\s+él\b", "irte conmigo"),
        (r"\bvenirse\s+con\s+él\b", "venirte conmigo"),
        (r"\bcon\s+él\b", "conmigo"),
        (r"\bcon\s+ella\b", "conmigo"),
        (r"\btiene\s+que\b", "tienes que"),
        (r"\bdebe\b", "debes"),
        (r"\bsu\s+castigo\b", "tu castigo"),
        (r"\bsu\s+culpa\b", "tu culpa"),
        (r"\bpara\s+recibir\s+su\b", "para recibir tu"),
        (r"\bsus\s+actos\b", "tus actos"),
        (r"\bsu\s+vida\b", "tu vida"),
    ]

    for pat, rep in replacements:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)

    # Iteración 2: Segmentar oraciones compuestas
    res = re.sub(r"\s+y\s+que\s+", ". ", res, flags=re.IGNORECASE)
    res = re.sub(r"\s+y\s+(tienes|debes|ahora|no|vas)\b", r". \1", res, flags=re.IGNORECASE)

    # Iteración 3: Mayúsculas y signos
    if "pregunta" in verb:
        m_q = re.match(r"^(?:quien|quién)\s+(.+)$", res, re.IGNORECASE)
        if m_q:
            return f"¿Quién {m_q.group(1)}?"
        elif re.match(r"^(?:está|esta|llega|vienen|es|pasa)\b", res, re.IGNORECASE):
            return f"¿Quién {res}?"
        return f"¿{res.strip('.?!')[0].upper() + res.strip('.?!')[1:]}?"

    if "grita" in verb:
        return f"¡{res.strip('.?!')[0].upper() + res.strip('.?!')[1:]}!"

    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", res) if s.strip()]
    formatted = []
    for s in sentences:
        if s:
            formatted.append(s[0].upper() + s[1:])

    clean_out = " ".join(formatted) if formatted else res
    return clean_out.rstrip(".?!") + "."


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

    verbs = (
        r"(?:dice|dijo|decir|diciendo|pregunta|preguntó|preguntar|preguntando|responde|respondió|responder|respondiendo|"
        r"contesta|contestó|contestar|contestando|susurra|susurró|susurrar|susurrando|grita|gritó|gritar|gritando|"
        r"afirma|afirmó|afirmar|afirmando|exclama|exclamó|exclamar|exclamando|pide|pidió|pedir|pidiendo|murmura|murmuró|murmurar|murmurando|advierte|advirtió|advirtiendo)"
    )
    links = (
        r"(?:que\s+quien|qué\s+quien|que\s+quién|qué\s+quién|que\s+qué|qué\s+qué|"
        r"que\s+cómo|qué\s+cómo|que\s+dónde|qué\s+dónde|que\s+cuándo|qué\s+cuándo|"
        r"que\s+por\s+qué|que\s+si|qué\s+|que\s+|si\s+|quién\s+|quien\s+|cómo\s+|dónde\s+|cuándo\s+|por\s+qué\s+)"
    )
    indirect_pattern = re.compile(
        rf"^(.*?)(?:[,\s]+y\s+|\s+y\s+|[,\s]+)?(?:(se|le|les|me|nos|te|lo|la|los|las)\s+)?{verbs}\s*(.*?)\s*{links}(.+)$",
        re.IGNORECASE,
    )
    ignore_words = {
        "se",
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "al",
        "en",
        "por",
        "tras",
        "luego",
        "mientras",
        "cuando",
        "como",
        "donde",
    }

    active_speaker = char_names[0].upper() if char_names else "PERSONAJE"

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
            active_speaker = speaker
            continue

        # Detectar diálogo por formato "Personaje dice: 'Diálogo'"
        m_quote = quote_pattern.match(clean_p)
        if m_quote:
            speaker = m_quote.group("speaker").strip().upper()
            dialogue = m_quote.group("dialogue").strip()

            screenplay_blocks.append(speaker)
            screenplay_blocks.append(dialogue)
            active_speaker = speaker
            continue

        # Detectar habla indirecta narrativa
        m_indirect = indirect_pattern.match(clean_p)
        if m_indirect:
            pre_part = (m_indirect.group(1) or "").strip()
            verb_mod = (m_indirect.group(3) or "").strip()
            dialogue_rest = re.sub(r"[.?!]+$", "", (m_indirect.group(4) or "").strip()).strip()

            m_v = re.search(verbs, clean_p, re.IGNORECASE)
            verb = (m_v.group(0) if m_v else "dice").lower()

            action_part = None
            speaker = None

            # Destinatario explícito (ej: 'a Javier', 'a Juan')
            m_rec = re.search(r"(?:a|al)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)", clean_p, re.IGNORECASE)
            recipient = m_rec.group(1).upper() if m_rec else None

            # Evaluar si pre_part empieza con nombre propio
            m_lead = re.match(r"^([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,15})\b", pre_part)
            if m_lead:
                candidate = m_lead.group(1)
                if candidate.lower() not in ignore_words:
                    speaker = candidate.upper()
                    if not re.match(rf"^{re.escape(candidate)}$", pre_part, re.IGNORECASE):
                        action_part = pre_part
                else:
                    action_part = pre_part
            elif pre_part:
                action_part = pre_part

            # Si no hay hablante explícito en la cláusula, inferir por descarte de destinatario
            if not speaker:
                if recipient:
                    for cn in char_names:
                        if cn.upper() != recipient:
                            speaker = cn.upper()
                            break
                if not speaker and active_speaker:
                    speaker = active_speaker

            if not speaker:
                speaker = char_names[0].upper() if char_names else "PERSONAJE"
            active_speaker = speaker

            # Acotaciones circunstanciales
            parenthetical = None
            if re.search(r"al\s+o[ií]do", verb_mod, re.IGNORECASE):
                parenthetical = "susurrando al oído"
            elif re.search(r"en\s+voz\s+baja", verb_mod, re.IGNORECASE):
                parenthetical = "en voz baja"
            elif re.search(r"con\s+calma|tranquil[oa]", verb_mod, re.IGNORECASE):
                parenthetical = "con calma"
            elif re.search(r"furios[oa]|enfadad[oa]", verb_mod, re.IGNORECASE):
                parenthetical = "furioso"
            elif "susurra" in verb:
                parenthetical = "susurrando"

            # Limpiar nexos anidados 'y que '
            dialogue_rest = re.sub(r"\s+y\s+que\s+", " y ", dialogue_rest, flags=re.IGNORECASE)

            # Iteración y refinamiento dramático a estilo directo (segunda persona)
            dialogue = refine_dialogue_to_direct_speech(dialogue_rest, verb)

            if action_part:
                action_clean = re.sub(r"[.?!]+$", "", action_part) + "."
                screenplay_blocks.append(action_clean)

            screenplay_blocks.append(speaker)
            if parenthetical:
                screenplay_blocks.append(f"({parenthetical})")
            screenplay_blocks.append(dialogue)
            continue

        # Párrafo de acción narrativa: poner en mayúsculas los personajes
        action_line = clean_p
        for name in char_names:
            pattern = rf"\b{re.escape(name)}\b"
            action_line = re.sub(pattern, name.upper(), action_line, flags=re.IGNORECASE)

        # Recordar último personaje que inició una acción
        m_spk_action = re.search(r"\b([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,15})\b", action_line)
        if m_spk_action and m_spk_action.group(1).lower() not in ignore_words:
            active_speaker = m_spk_action.group(1).upper()

        screenplay_blocks.append(action_line)

    screenplay_output = "\n\n".join(screenplay_blocks)
    return apply_user_locks(screenplay_output, user_locks, stage="screenplay")
