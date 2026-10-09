"""Motor de desglose técnico y detección de planos cinematográficos.

Analiza las necesidades visuales de la escena y propone la separación de planos
siguiendo estrictamente el estándar canónico delimitador:
--- shot N (tipo) ---
Soporta inferencia semántica de tensión dramática mediante LLM o fallback heurístico.
"""

import re
from typing import Any

from jg_plugin_filmmaker.llm import get_active_llm, invoke_llm_text

BREAKDOWN_SYSTEM_PROMPT = """Eres un Director de Fotografía y Script supervisor cinematográfico profesional.
Tu misión es analizar el guión literario de una escena y proponer una cobertura técnica de cámara (desglose de planos) que maximice la tensión dramática y la narrativa visual.

DIRECTRICES Y REGLAS ESTRICTAS:
1. DELIMITADOR CANÓNICO OBLIGATORIO:
   Antes de cada plano propuesto, debes insertar estrictamente la línea delimitadora:
   --- shot N (tipo) ---
   Donde N es el número secuencial correlativo (1, 2, 3...) y 'tipo' es una de las abreviaturas técnicas:
   - PG (Plano General): Para establecer la localización, entorno o dinámicas espaciales de grupo.
   - PM (Plano Medio): Para interacción entre personajes, diálogo corporal y movimientos.
   - PP (Primer Plano): Para tensión psicológica, miradas, rostros y reacciones emocionales.
   - PD (Plano Detalle): Para elementos u objetos críticos (llaves, cartas, ojos, vasos, armas, pantallas).
   - PA (Plano Americano): Para figura humana hasta las rodillas o acción física.
2. CONTINUIDAD: Detrás de cada encabezado canónico '--- shot N (tipo) ---', incluye el fragmento de acción o diálogo que cubre dicho plano.
3. FORMATO DE SALIDA: Devuelve ÚNICAMENTE el guión desglosado con los delimitadores canónicos, sin introducciones, notas técnicas al pie ni metacomentarios.
"""


def detect_shot_type(action_text: str) -> str:
    """Determina heurísticamente el tipo de plano idóneo para una línea o acción."""
    lower = action_text.lower()

    # Plano Detalle (PD)
    if any(
        k in lower
        for k in [
            "vaso",
            "llave",
            "carta",
            "ojo",
            "mano",
            "pantalla",
            "teléfono",
            "reloj",
            "pistola",
            "detalle",
        ]
    ):
        return "PD"

    # Primer Plano (PP)
    if any(
        k in lower
        for k in [
            "mira fijamente",
            "rostro",
            "lágrima",
            "expresión",
            "susurra",
            "ojos",
            "sonríe",
            "palidece",
        ]
    ):
        return "PP"

    # Plano General (PG)
    if any(
        k in lower
        for k in [
            "int.",
            "ext.",
            "entra al",
            "sala",
            "bar",
            "calle",
            "habitación",
            "paisaje",
            "panorama",
            "edificio",
        ]
    ):
        return "PG"

    # Plano Americano (PA)
    if any(k in lower for k in ["camina hacia", "corre", "de pie", "revólver en cinto"]):
        return "PA"

    # Por defecto, Plano Medio (PM)
    return "PM"


def parse_shots_from_annotated_text(annotated_text: str) -> list[dict[str, Any]]:
    """Extrae la lista estructurada de planos a partir del texto con delimitadores canónicos."""
    pattern = re.compile(r"^---\s*shot\s+(\d+)\s*\(([A-Za-z]+)\)\s*---", re.MULTILINE)
    matches = list(pattern.finditer(annotated_text))
    if not matches:
        return []

    shots: list[dict[str, Any]] = []
    for i, match in enumerate(matches):
        shot_num = int(match.group(1))
        shot_type = match.group(2).upper()
        start_desc = match.end()
        end_desc = matches[i + 1].start() if i + 1 < len(matches) else len(annotated_text)
        description = annotated_text[start_desc:end_desc].strip()

        shots.append(
            {
                "shot_number": shot_num,
                "shot_type": shot_type,
                "description": description or f"Plano {shot_num} ({shot_type})",
            }
        )
    return shots


def breakdown_screenplay_to_shots(
    screenplay_text: str,
    llm_client: Any = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Desglosa el guión en planos técnicos con delimitadores canónicos."""
    if not screenplay_text or not screenplay_text.strip():
        return "", []

    text = screenplay_text.strip()

    # Intentar inferencia semántica con LLM si está disponible y activo
    active_llm = get_active_llm(llm_client)
    if active_llm is not None:
        user_prompt = f"GUIÓN LITERARIO DE LA ESCENA A DESGLOSAR:\n{text}"
        llm_output = invoke_llm_text(active_llm, BREAKDOWN_SYSTEM_PROMPT, user_prompt)
        if llm_output and llm_output.strip():
            parsed_shots = parse_shots_from_annotated_text(llm_output)
            if parsed_shots:
                return llm_output.strip(), parsed_shots

    # --- FALLBACK DETERMINISTA HEURÍSTICO (Modo Test / Offline / Cero Tokens) ---
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    shots: list[dict[str, Any]] = []
    output_lines: list[str] = []
    shot_count = 0

    for p in paragraphs:
        if p.startswith(("INT.", "EXT.", "INT/EXT.")):
            output_lines.append(p)
            continue

        shot_count += 1
        shot_type = detect_shot_type(p)
        header = f"--- shot {shot_count} ({shot_type}) ---"

        output_lines.append(header)
        output_lines.append(p)

        shots.append(
            {
                "shot_number": shot_count,
                "shot_type": shot_type,
                "description": p,
            }
        )

    if not shots and paragraphs:
        shot_count = 1
        header = "--- shot 1 (PG) ---"
        desc = " ".join(paragraphs)
        output_lines = [header, desc]
        shots.append(
            {
                "shot_number": 1,
                "shot_type": "PG",
                "description": desc,
            }
        )

    annotated_output = "\n\n".join(output_lines)
    return annotated_output, shots
