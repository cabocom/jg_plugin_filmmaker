"""Motor de estructuración y normalización de tratamiento cinematográfico.

Transforma ideas libres y texto bruto en tratamiento cinematográfico estructurado
en presente de indicativo, integrando el contexto de la biblia y respetando
estrictamente los bloqueos manuales del usuario (user_locks).
Soporta inferencia semántica con LLM o fallback determinista para testing y CI.
"""

import re
from typing import Any

from jg_plugin_filmmaker.llm import get_active_llm, invoke_llm_text

STRUCTURING_SYSTEM_PROMPT = """Eres un consultor y analista cinematográfico profesional.
Tu misión es transformar notas dispersas, ideas en bruto o borradores de un autor en un TRATAMIENTO CINEMATOGRÁFICO NARRATIVO formal.

DIRECTRICES Y REGLAS ESTRICTAS:
1. TIEMPO VERBAL: Redacta exclusivamente en tiempo PRESENTE DE INDICATIVO continuo (ej: "Javier camina", "el viento golpea la ventana", nunca en pretérito ni futuro).
2. ACCIONES OBSERVABLES: Describe acciones físicas visibles, dinámicas espaciales y tensión dramática sin juicios de valor abstractos.
3. CONTEXTO DE PERSONAJES:
{characters_context}
Si alguno de estos personajes interviene en la escena, integra su nombre exacto.
4. CONTEXTO DE LOCALIZACIÓN:
{location_context}
Ubica espacialmente la escena en este entorno.
5. CANDADOS Y TÉRMINOS FIJADOS (REGLA INMUTABLE):
{pinned_terms_context}
Respeta escrupulosamente los términos canónicos anteriores.
6. FORMATO DE SALIDA: Devuelve ÚNICAMENTE el texto del tratamiento en párrafos limpios, sin saludos, introducciones, conclusiones ni metacomentarios.
"""


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
    llm_client: Any = None,
) -> str:
    """Normaliza texto bruto a tratamiento dramático en presente continuo/indicativo."""
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text.strip()

    # Intentar inferencia semántica con LLM si está disponible y activo
    active_llm = get_active_llm(llm_client)
    if active_llm is not None:
        chars_desc = "Sin personajes específicos definidos."
        if characters_context and isinstance(characters_context, list):
            chars_desc = "\n".join(
                f"- {c.get('name', '')}: {c.get('bio', '')} (Rol: {c.get('role', 'personaje')})"
                for c in characters_context
                if isinstance(c, dict) and "name" in c
            )

        loc_desc = "Sin localización específica."
        if location_context and isinstance(location_context, dict):
            lname = location_context.get("name", "ESCENARIO")
            ltype = location_context.get("type", "INT")
            loc_desc = f"{lname} ({ltype})"

        locks_desc = "Ningún término fijado."
        if user_locks and isinstance(user_locks, dict):
            pinned = user_locks.get("pinned_terms", {})
            if pinned:
                locks_desc = "\n".join(
                    f"- Sustituir '{k}' siempre por '{v}'" for k, v in pinned.items()
                )

        sys_prompt = STRUCTURING_SYSTEM_PROMPT.format(
            characters_context=chars_desc,
            location_context=loc_desc,
            pinned_terms_context=locks_desc,
        )

        user_prompt = f"NOTAS / TEXTO BRUTO DEL AUTOR:\n{text}"

        llm_output = invoke_llm_text(active_llm, sys_prompt, user_prompt)
        if llm_output and llm_output.strip():
            # Aplicar estrictamente candados de usuario sobre la salida del LLM
            return apply_user_locks(llm_output.strip(), user_locks, stage="structured")

    # --- FALLBACK DETERMINISTA HEURÍSTICO (Modo Test / Offline / Cero Tokens) ---
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

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    structured_paragraphs: list[str] = []

    for i, p in enumerate(paragraphs):
        p_clean = re.sub(r"\s+", " ", p)

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
    return apply_user_locks(structured_text, user_locks, stage="structured")
