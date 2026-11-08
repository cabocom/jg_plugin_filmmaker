"""Motor de generación de viñetas de storyboard con Google AI Studio para jg_plugin_filmmaker.

Permite renderizar viñetas cinemáticas 16:9 con soporte multimodal:
- Condicionamiento visual de personaje (turn-around) con referencias @personaje.
- Condicionamiento visual de localización con referencias @localizacion.
- Condicionamiento visual de hasta 3 objetos de atrezzo con referencias @atrezzo1, @atrezzo2, @atrezzo3.
- Selección de estilos artísticos canónicos (Escala de grises, Animación 2D, Enki Bilal).
"""

import logging
import os
from typing import Any

import httpx
from jg_sdk.contracts import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from jg_plugin_filmmaker.llm import is_mock_mode

logger = logging.getLogger("jg_plugin_filmmaker.storyboard")

# 1x1 dummy PNG para modo mock y pruebas offline seguras (consumo 0 tokens)
DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

CANONICAL_STYLES: dict[str, dict[str, str]] = {
    "grayscale_sketch": {
        "name": "Escala de Grises",
        "badge": "Sketch B&W",
        "modifier": (
            "Cinematic production storyboard sketch, charcoal and graphite drawing, black and white tones, "
            "dynamic lighting, film noir shading, rough crosshatching, rule of thirds composition, 35mm storyboard aspect ratio 16:9."
        ),
    },
    "kids_2d_animation": {
        "name": "Animación 2D Infantil",
        "badge": "2D Infantil",
        "modifier": (
            "Vibrant 2D children's animated feature film still, clean vector linework, whimsical warm color palette, "
            "soft cel shading, expressive character design, storybook aesthetic, high quality 2D animation, 16:9."
        ),
    },
    "enki_bilal": {
        "name": "Enki Bilal",
        "badge": "Enki Bilal",
        "modifier": (
            "Graphic novel panel in the distinct art style of Enki Bilal, European bande dessinée, "
            "textured chalk and oil pastel, gritty dystopian atmosphere, desaturated muted color palette with chalky blues and ochre, "
            "weathered look, expressive melancholy gaze, cinematic sci-fi noir, 16:9."
        ),
    },
}


class StoryboardGeneratorArgs(BaseModel):
    """Esquema formal Pydantic v2 de argumentos para la generación de Storyboard."""

    model_config = ConfigDict(extra="ignore")

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Prompt cinemático descriptivo de la viñeta, con soporte para etiquetas @personaje, @localizacion y @atrezzo.",
    )
    style: str = Field(
        default="grayscale_sketch",
        description="Estilo visual canónico (grayscale_sketch, kids_2d_animation, enki_bilal).",
    )
    character_name: str | None = Field(
        default=None,
        max_length=120,
        description="Nombre del personaje principal referenciado en el prompt.",
    )
    character_image_base64: str | None = Field(
        default=None,
        description="Fotograma o turn-around del personaje en base64 para coherencia visual.",
    )
    location_name: str | None = Field(
        default=None,
        max_length=120,
        description="Nombre de la localización o escenografía referenciada en el prompt.",
    )
    location_image_base64: str | None = Field(
        default=None,
        description="Fotografía o diseño de la localización en base64.",
    )
    prop_images_base64: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Hasta 3 imágenes de objetos o atrezzo en base64.",
    )
    aspect_ratio: str = Field(
        default="16:9",
        description="Relación de aspecto cinematográfica.",
    )


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

    tag_directives = []
    if character_name and has_character_image:
        clean_char = character_name.strip().replace(" ", "_")
        tag_directives.append(
            f"Reference Image 1 corresponds to character @{clean_char} (preserve facial features, hairstyle and costume)."
        )
    if location_name and has_location_image:
        clean_loc = location_name.strip().replace(" ", "_")
        tag_directives.append(
            f"Reference Image 2 corresponds to setting @{clean_loc} (preserve architecture, lighting and atmosphere)."
        )
    for idx in range(1, prop_count + 1):
        tag_directives.append(
            f"Reference Image for key prop corresponds to @Atrezzo{idx} (accurately incorporate this object)."
        )

    parts = [raw_prompt.strip()]
    if tag_directives:
        parts.append("Visual Reference Grounding: " + " ".join(tag_directives))

    style_mod = style_data["modifier"]
    if style_mod not in raw_prompt:
        parts.append(f"Artistic Style: {style_mod}")

    return " ".join(parts)


def generate_storyboard_image(
    prompt: str,
    style: str = "grayscale_sketch",
    character_name: str | None = None,
    character_image_base64: str | None = None,
    location_name: str | None = None,
    location_image_base64: str | None = None,
    prop_images_base64: list[str] | None = None,
    aspect_ratio: str = "16:9",
    api_key_override: str | None = None,
    client: httpx.Client | None = None,
) -> ToolResult:
    """Ejecuta la llamada a Google AI Studio o retorna viñeta mock en entornos offline."""
    props = (prop_images_base64 or [])[:3]
    final_prompt = build_augmented_prompt(
        raw_prompt=prompt,
        style_key=style,
        character_name=character_name,
        has_character_image=bool(character_image_base64),
        location_name=location_name,
        has_location_image=bool(location_image_base64),
        prop_count=len(props),
    )

    api_key = api_key_override or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")

    # Si estamos en modo mock (sin override de API key) o sin API key, fail-closed con dummy PNG
    if (is_mock_mode() and not api_key_override) or not api_key:
        logger.info("Modo mock o sin API Key: retornando viñeta determinista offline.")
        return ToolResult(
            success=True,
            output="Viñeta de storyboard generada exitosamente en modo offline/mock.",
            metadata={
                "image_base64": DUMMY_PNG_BASE64,
                "mime_type": "image/png",
                "final_prompt": final_prompt,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "source": "deterministic_mock",
            },
        )

    base_url = os.getenv("GOOGLE_AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    model = os.getenv("GOOGLE_AI_MODEL", "gemini-2.5-flash-image")
    timeout = float(os.getenv("GOOGLE_AI_TIMEOUT", "60.0"))

    parts: list[dict[str, Any]] = []

    # 1. Imagen del personaje
    if character_image_base64:
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": character_image_base64,
            }
        })

    # 2. Imagen de la localización
    if location_image_base64:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": location_image_base64,
            }
        })

    # 3. Imágenes de atrezzo (hasta 3)
    for prop_b64 in props:
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": prop_b64,
            }
        })

    # 4. Prompt de texto final
    parts.append({"text": final_prompt})

    endpoint = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": parts}]}

    try:
        http_client = client or httpx.Client(timeout=timeout)
        response = http_client.post(endpoint, json=payload)

        if response.status_code != 200:
            error_data = response.json() if "application/json" in response.headers.get("content-type", "") else {}
            err_msg = error_data.get("error", {}).get("message") or response.text
            logger.error("Error de Google AI Studio (%d): %s", response.status_code, err_msg)
            return ToolResult(
                success=False,
                output="",
                error=f"Error en Google AI Studio ({response.status_code}): {err_msg}",
                metadata={"error_code": "GOOGLE_AI_ERROR", "status_code": response.status_code},
            )

        res_data = response.json()
        candidates_parts = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])

        extracted_b64 = None
        mime_type = "image/png"

        for p in candidates_parts:
            inline = p.get("inlineData") or p.get("inline_data")
            if inline and inline.get("data"):
                extracted_b64 = inline.get("data")
                mime_type = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                break

        if not extracted_b64:
            return ToolResult(
                success=False,
                output="",
                error="Google AI Studio no devolvió la imagen esperada en la respuesta.",
                metadata={"error_code": "NO_IMAGE_IN_RESPONSE"},
            )

        return ToolResult(
            success=True,
            output="Viñeta de storyboard generada exitosamente por Google AI Studio.",
            metadata={
                "image_base64": extracted_b64,
                "mime_type": mime_type,
                "final_prompt": final_prompt,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "source": "google_ai_studio",
            },
        )

    except Exception as e:
        logger.exception("Excepción no controlada durante la generación de viñeta: %s", e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo en generación de storyboard: {type(e).__name__} - {e}",
            metadata={"error_code": "STORYBOARD_EXCEPTION"},
        )
