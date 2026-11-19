"""Construcción de prompts visuales y detección de tipos MIME para storyboard."""

from __future__ import annotations

import base64
import binascii
from typing import Any

CANONICAL_STYLES: dict[str, dict[str, str]] = {
    "grayscale_sketch": {
        "name": "Escala de Grises",
        "badge": "Sketch B&W",
        "modifier": (
            "Cinematic production storyboard sketch, charcoal and graphite drawing, "
            "black and white tones, dynamic lighting, film noir shading, rough crosshatching, "
            "rule of thirds composition, 35mm storyboard aspect ratio 16:9."
        ),
    },
    "kids_2d_animation": {
        "name": "Animación 2D Infantil",
        "badge": "2D Infantil",
        "modifier": (
            "Vibrant 2D children's animated feature film still, clean vector linework, "
            "whimsical warm color palette, soft cel shading, expressive character design, "
            "storybook aesthetic, high quality 2D animation, 16:9."
        ),
    },
    "enki_bilal": {
        "name": "Enki Bilal",
        "badge": "Enki Bilal",
        "modifier": (
            "Graphic novel panel in the distinct art style of Enki Bilal, European bande dessinée, "
            "textured chalk and oil pastel, gritty dystopian atmosphere, desaturated muted color "
            "palette with chalky blues and ochre, weathered look, expressive melancholy gaze, "
            "cinematic sci-fi noir, 16:9."
        ),
    },
}


def detect_image_mime(base64_data: str) -> str:
    """Detecta el tipo MIME de una imagen en base64 inspeccionando encabezado o magic bytes."""
    if not base64_data:
        return "image/png"

    if base64_data.startswith("data:image/"):
        header = base64_data.split(";")[0]
        mime = header.replace("data:", "").strip()
        if mime in ("image/jpeg", "image/png", "image/webp"):
            return mime

    try:
        sample = base64.b64decode(base64_data[:64])
        if sample.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if sample.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if sample.startswith(b"RIFF") and b"WEBP" in sample[:16]:
            return "image/webp"
    except (binascii.Error, ValueError):
        pass

    return "image/png"


def build_augmented_prompt(
    raw_prompt: str,
    style_key: str,
    character_name: str | None = None,
    has_character_image: bool = False,
    location_name: str | None = None,
    has_location_image: bool = False,
    prop_count: int = 0,
) -> str:
    """Construye las directrices multimodales mapeando las etiquetas @ del prompt."""
    style_data = CANONICAL_STYLES.get(style_key, CANONICAL_STYLES["grayscale_sketch"])

    tag_directives: list[str] = []
    if character_name and has_character_image:
        clean_char = character_name.strip().replace(" ", "_")
        tag_directives.append(
            f"Reference Image 1 corresponds to character @{clean_char} "
            "(preserve facial features, hairstyle and costume)."
        )
    if location_name and has_location_image:
        clean_loc = location_name.strip().replace(" ", "_")
        tag_directives.append(
            f"Reference Image 2 corresponds to setting @{clean_loc} "
            "(preserve architecture, lighting and atmosphere)."
        )
    for idx in range(1, prop_count + 1):
        tag_directives.append(
            f"Reference Image for key prop corresponds to @Atrezzo{idx} "
            "(accurately incorporate this object)."
        )

    parts = [raw_prompt.strip()]
    if tag_directives:
        parts.append("Visual Reference Grounding: " + " ".join(tag_directives))

    style_mod = style_data["modifier"]
    if style_mod not in raw_prompt:
        parts.append(f"Artistic Style: {style_mod}")

    return " ".join(parts)


def build_storyboard_request_parts(
    character_image_base64: str | None,
    location_image_base64: str | None,
    props: list[str],
    final_prompt: str,
) -> list[dict[str, Any]]:
    """Construye las partes del payload multipart para Google AI Studio."""
    parts: list[dict[str, Any]] = []

    if character_image_base64:
        parts.append(
            {
                "inline_data": {
                    "mime_type": detect_image_mime(character_image_base64),
                    "data": character_image_base64,
                }
            }
        )

    if location_image_base64:
        parts.append(
            {
                "inline_data": {
                    "mime_type": detect_image_mime(location_image_base64),
                    "data": location_image_base64,
                }
            }
        )

    for prop_b64 in props:
        parts.append(
            {
                "inline_data": {
                    "mime_type": detect_image_mime(prop_b64),
                    "data": prop_b64,
                }
            }
        )

    parts.append({"text": final_prompt})
    return parts


__all__ = [
    "CANONICAL_STYLES",
    "build_augmented_prompt",
    "build_storyboard_request_parts",
    "detect_image_mime",
]
