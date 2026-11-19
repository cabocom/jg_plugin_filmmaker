"""Motor de generación de viñetas de storyboard con Google AI Studio para jg_plugin_filmmaker."""

import base64
import logging
import os
from typing import Any
from urllib.parse import urlparse

import httpx
from jg_sdk.contracts import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from jg_plugin_filmmaker.llm import is_mock_mode

logger = logging.getLogger("jg_plugin_filmmaker.storyboard")

# 1x1 dummy PNG para modo mock y pruebas offline seguras (consumo 0 tokens)
DUMMY_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

CANONICAL_STYLES: dict[str, dict[str, str]] = {
    "grayscale_sketch": {
        "name": "Escala de Grises",
        "badge": "Sketch B&W",
        "modifier": "Cinematic production storyboard sketch, charcoal and graphite drawing, black and white tones, dynamic lighting, film noir shading, rough crosshatching, rule of thirds composition, 35mm storyboard aspect ratio 16:9.",
    },
    "kids_2d_animation": {
        "name": "Animación 2D Infantil",
        "badge": "2D Infantil",
        "modifier": "Vibrant 2D children's animated feature film still, clean vector linework, whimsical warm color palette, soft cel shading, expressive character design, storybook aesthetic, high quality 2D animation, 16:9.",
    },
    "enki_bilal": {
        "name": "Enki Bilal",
        "badge": "Enki Bilal",
        "modifier": "Graphic novel panel in the distinct art style of Enki Bilal, European bande dessinée, textured chalk and oil pastel, gritty dystopian atmosphere, desaturated muted color palette with chalky blues and ochre, weathered look, expressive melancholy gaze, cinematic sci-fi noir, 16:9.",
    },
}


class StoryboardGeneratorArgs(BaseModel):
    """Esquema formal Pydantic v2 de argumentos para la generación de Storyboard."""

    model_config = ConfigDict(extra="ignore")

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Prompt descriptivo con @personaje, @localizacion, @atrezzo.",
    )
    style: str = Field(default="grayscale_sketch", description="Estilo visual canónico.")
    character_name: str | None = Field(
        default=None, max_length=120, description="Nombre del personaje principal."
    )
    character_image_base64: str | None = Field(
        default=None, description="Fotograma o turn-around en base64."
    )
    location_name: str | None = Field(
        default=None, max_length=120, description="Nombre de la localización."
    )
    location_image_base64: str | None = Field(
        default=None, description="Foto o diseño de localización en base64."
    )
    prop_images_base64: list[str] = Field(
        default_factory=list, max_length=3, description="Hasta 3 objetos de atrezzo en base64."
    )
    aspect_ratio: str = Field(default="16:9", description="Relación de aspecto cinematográfica.")


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
    except Exception:
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

    if not api_key:
        if is_mock_mode() and not api_key_override:
            logger.info("Modo mock offline en testing: retornando viñeta determinista.")
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
        return ToolResult(
            success=False,
            output="",
            error="Falta la credencial requerida (GOOGLE_AI_API_KEY o GEMINI_API_KEY) para generar la viñeta.",
            metadata={"error_code": "MISSING_API_KEY"},
        )

    base_url = os.getenv("GOOGLE_AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    model = os.getenv("GOOGLE_AI_MODEL", "gemini-2.5-flash-image")
    timeout = float(os.getenv("GOOGLE_AI_TIMEOUT", "60.0"))

    parsed_url = urlparse(base_url)
    hostname = (parsed_url.hostname or "").lower()
    is_valid_scheme = parsed_url.scheme in ("https", "http")
    is_trusted_host = (
        hostname in {"generativelanguage.googleapis.com"}
        or hostname in {"127.0.0.1", "localhost", "testserver"}
        or hostname.endswith(".test")
    )

    if not is_valid_scheme or not is_trusted_host:
        logger.error("URL base de Google AI no confiable detectada: %s", base_url)
        return ToolResult(
            success=False,
            output="",
            error=f"URL base no permitida para Google AI Studio: {base_url}",
            metadata={"error_code": "UNTRUSTED_BASE_URL"},
        )

    parts: list[dict[str, Any]] = []

    # 1. Imagen del personaje
    if character_image_base64:
        parts.append(
            {
                "inline_data": {
                    "mime_type": detect_image_mime(character_image_base64),
                    "data": character_image_base64,
                }
            }
        )

    # 2. Imagen de la localización
    if location_image_base64:
        parts.append(
            {
                "inline_data": {
                    "mime_type": detect_image_mime(location_image_base64),
                    "data": location_image_base64,
                }
            }
        )

    # 3. Imágenes de atrezzo (hasta 3)
    for prop_b64 in props:
        parts.append(
            {
                "inline_data": {
                    "mime_type": detect_image_mime(prop_b64),
                    "data": prop_b64,
                }
            }
        )

    # 4. Prompt de texto final
    parts.append({"text": final_prompt})

    endpoint = f"{base_url.rstrip('/')}/models/{model}:generateContent"
    payload = {"contents": [{"parts": parts}]}

    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout)

    try:
        response = http_client.post(
            endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
        )

        if response.status_code != 200:
            error_data = (
                response.json()
                if "application/json" in response.headers.get("content-type", "")
                else {}
            )
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
    finally:
        if owns_client:
            http_client.close()
