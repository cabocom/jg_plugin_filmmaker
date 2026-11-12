"""Módulo de refinamiento dramático de estilo indirecto a habla directa."""

from __future__ import annotations

import re

PRONOUN_REPLACEMENTS = [
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

IGNORE_WORDS = {
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

VERBS = (
    r"(?:dice|dijo|decir|diciendo|pregunta|preguntó|preguntar|preguntando|responde|respondió|responder|respondiendo|"
    r"contesta|contestó|contestar|contestando|susurra|susurró|susurrar|susurrando|grita|gritó|gritar|gritando|"
    r"afirma|afirmó|afirmar|afirmando|exclama|exclamó|exclamar|exclamando|pide|pidió|pedir|pidiendo|murmura|murmuró|murmurar|murmurando|advierte|advirtió|advirtiendo)"
)

LINKS = (
    r"(?:que\s+quien|qué\s+quien|que\s+quién|qué\s+quién|que\s+qué|qué\s+qué|"
    r"que\s+cómo|qué\s+cómo|que\s+dónde|qué\s+dónde|que\s+cuándo|qué\s+cuándo|"
    r"que\s+por\s+qué|que\s+si|qué\s+|que\s+|si\s+|quién\s+|quien\s+|cómo\s+|dónde\s+|cuándo\s+|por\s+qué\s+)"
)


def _apply_pronoun_replacements(text: str) -> str:
    """Aplica transformaciones de tercera persona a interlocución directa."""
    res = text
    for pat, rep in PRONOUN_REPLACEMENTS:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    res = re.sub(r"\s+y\s+que\s+", ". ", res, flags=re.IGNORECASE)
    return re.sub(r"\s+y\s+(tienes|debes|ahora|no|vas)\b", r". \1", res, flags=re.IGNORECASE)


def _format_question_dialogue(res: str, core: str) -> str:
    """Aplica formato interrogativo según la consulta."""
    m_q = re.match(r"^(?:quien|quién)\s+(.+)$", res, re.IGNORECASE)
    if m_q:
        return f"¿Quién {m_q.group(1)}?"
    if re.match(r"^(?:está|esta|llega|vienen|es|pasa)\b", res, re.IGNORECASE):
        return f"¿Quién {res}?"
    if not core:
        return "¿...?"
    return f"¿{core[0].upper() + core[1:]}?"


def _format_sentences(res: str, core: str) -> str:
    """Formatea la lista de oraciones en mayúsculas iniciales."""
    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", res) if s.strip()]
    formatted = []
    for s in sentences:
        s_core = s.strip(".?!¿¡ ")
        if s_core:
            formatted.append(s_core[0].upper() + s_core[1:])
        elif s:
            formatted.append(s)

    clean_out = " ".join(formatted) if formatted else core
    return clean_out.rstrip(".?!") + "."


def refine_dialogue_to_direct_speech(text: str, verb: str) -> str:
    """Nodo de refinamiento dramático: convierte tercera persona narrativa a segunda/primera persona directa."""
    res = text.strip()
    res = re.sub(r"^que\s+", "", res, flags=re.IGNORECASE)
    res = re.sub(r"(?<=[.?!])\s*que\s+", " ", res, flags=re.IGNORECASE)

    res = _apply_pronoun_replacements(res)
    core = res.strip(".?!¿¡ ")

    if "pregunta" in verb:
        return _format_question_dialogue(res, core)
    if "grita" in verb:
        if not core:
            return "¡...!"
        return f"¡{core[0].upper() + core[1:]}!"
    if not core:
        return "..."

    return _format_sentences(res, core)


def resolve_parenthetical(verb_mod: str, verb: str) -> str | None:
    """Infiere la acotación dramática circunstancial."""
    if re.search(r"al\s+o[ií]do", verb_mod, re.IGNORECASE):
        return "susurrando al oído"
    if re.search(r"en\s+voz\s+baja", verb_mod, re.IGNORECASE):
        return "en voz baja"
    if re.search(r"con\s+calma|tranquil[oa]", verb_mod, re.IGNORECASE):
        return "con calma"
    if re.search(r"furios[oa]|enfadad[oa]", verb_mod, re.IGNORECASE):
        return "furioso"
    if "susurra" in verb:
        return "susurrando"
    return None


def resolve_speaker(
    clean_p: str, pre_part: str, char_names: list[str], active_speaker: str
) -> tuple[str, str | None]:
    """Resuelve el hablante y posible acción previa de una oración indirecta."""
    m_rec = re.search(r"(?:a|al)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)", clean_p, re.IGNORECASE)
    recipient = m_rec.group(1).upper() if m_rec else None

    speaker = None
    action_part = None

    m_lead = re.match(r"^([A-Za-zÁÉÍÓÚáéíóúñÑ]{2,15})\b", pre_part)
    if m_lead:
        candidate = m_lead.group(1)
        if candidate.lower() not in IGNORE_WORDS:
            speaker = candidate.upper()
            if not re.match(rf"^{re.escape(candidate)}$", pre_part, re.IGNORECASE):
                action_part = pre_part
        else:
            action_part = pre_part
    elif pre_part:
        action_part = pre_part

    if not speaker:
        if recipient:
            for cn in char_names:
                if cn.upper() != recipient:
                    speaker = cn.upper()
                    break
        speaker = (
            speaker or active_speaker or (char_names[0].upper() if char_names else "PERSONAJE")
        )

    return speaker, action_part


def process_indirect_dialogue(
    clean_p: str,
    m_indirect: re.Match[str],
    char_names: list[str],
    active_speaker: str,
    blocks: list[str],
) -> str:
    """Procesa una oración en estilo indirecto y la añade como diálogo Fountain."""
    pre_part = (m_indirect.group(1) or "").strip()
    verb_mod = (m_indirect.group(3) or "").strip()
    dialogue_rest = re.sub(r"[.?!]+$", "", (m_indirect.group(4) or "").strip()).strip()

    m_v = re.search(VERBS, clean_p, re.IGNORECASE)
    verb = (m_v.group(0) if m_v else "dice").lower()

    speaker, action_part = resolve_speaker(clean_p, pre_part, char_names, active_speaker)
    parenthetical = resolve_parenthetical(verb_mod, verb)

    dialogue_rest = re.sub(r"\s+y\s+que\s+", " y ", dialogue_rest, flags=re.IGNORECASE)
    dialogue = refine_dialogue_to_direct_speech(dialogue_rest, verb)

    if action_part:
        blocks.append(re.sub(r"[.?!]+$", "", action_part) + ".")

    blocks.append(speaker)
    if parenthetical:
        blocks.append(f"({parenthetical})")
    blocks.append(dialogue)

    return speaker
