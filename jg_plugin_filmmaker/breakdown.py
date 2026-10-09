"""Motor de desglose técnico y detección de planos cinematográficos.

Analiza las necesidades visuales de la escena y propone la separación de planos
siguiendo estrictamente el estándar canónico delimitador:
--- shot N (tipo) ---
"""

from typing import Any


def detect_shot_type(action_text: str) -> str:
    """Determina heurísticamente el tipo de plano idóneo para una línea o acción."""
    lower = action_text.lower()

    # Plano Detalle (PD) para objetos o miradas microscópicas
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

    # Primer Plano (PP) para emociones, miradas y reacciones directas
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

    # Plano General (PG) para aperturas, localizaciones completas y multitudes
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

    # Plano Americano (PA) para posturas de cuerpo entero o acción corporal
    if any(k in lower for k in ["camina hacia", "corre", "de pie", "revólver en cinto"]):
        return "PA"

    # Por defecto, Plano Medio (PM) para interacción y diálogo
    return "PM"


def breakdown_screenplay_to_shots(screenplay_text: str) -> tuple[str, list[dict[str, Any]]]:
    """Desglosa el guión en planos técnicos con delimitadores canónicos."""
    if not screenplay_text or not screenplay_text.strip():
        return "", []

    text = screenplay_text.strip()
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    shots: list[dict[str, Any]] = []
    output_lines: list[str] = []
    shot_count = 0

    for p in paragraphs:
        # Los encabezados de escena INT/EXT se conservan como contexto previo del plano 1
        if p.startswith(("INT.", "EXT.", "INT/EXT.")):
            output_lines.append(p)
            continue

        shot_count += 1
        shot_type = detect_shot_type(p)

        # Formato canónico estricto: --- shot N (tipo) ---
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

    # Si no se generó ningún plano (ej: solo encabezado), crear al menos 1
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
