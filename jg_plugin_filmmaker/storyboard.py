"""Motor de generación de viñetas de storyboard con Google AI Studio para jg_plugin_filmmaker."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

import httpx
from jg_sdk.contracts import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from jg_plugin_filmmaker.llm import is_mock_mode
from jg_plugin_filmmaker.storyboard_prompt import (
    CANONICAL_STYLES,
    build_augmented_prompt,
    build_storyboard_request_parts,
    detect_image_mime,
)

logger = logging.getLogger("jg_plugin_filmmaker.storyboard")

# 1x1 dummy PNG para modo mock y pruebas offline seguras (consumo 0 tokens)
DUMMY_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


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


def _handle_missing_api_key(
    api_key_override: str | None,
    final_prompt: str,
    style: str,
    aspect_ratio: str,
) -> ToolResult:
    """Gestiona la ausencia de API key con fail-closed o mock determinista en testing."""
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


def _validate_google_ai_config() -> tuple[str, str, float] | ToolResult:
    """Valida la configuración de Google AI Studio y restringe dominios no confiables."""
    base_url = os.getenv("GOOGLE_AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    model = os.getenv("GOOGLE_AI_MODEL", "gemini-2.5-flash-image")
    timeout = float(os.getenv("GOOGLE_AI_TIMEOUT", "60.0"))

    parsed_url = urlparse(base_url)
    hostname = (parsed_url.hostname or "").lower()

    # En producción solo HTTPS y dominio oficial; en mock/testing se toleran loopback y .test
    is_valid_scheme = (
        parsed_url.scheme in ("https", "http") if is_mock_mode() else parsed_url.scheme == "https"
    )
    trusted_hosts = {"generativelanguage.googleapis.com"}
    if is_mock_mode():
        trusted_hosts.update({"127.0.0.1", "localhost", "testserver"})

    is_trusted = hostname in trusted_hosts or (is_mock_mode() and hostname.endswith(".test"))

    if not is_valid_scheme or not is_trusted:
        logger.error("URL base de Google AI no confiable detectada: %s", base_url)
        return ToolResult(
            success=False,
            output="",
            error=f"URL base no permitida para Google AI Studio: {base_url}",
            metadata={"error_code": "UNTRUSTED_BASE_URL"},
        )

    return base_url, model, timeout


def _extract_generated_image(response_data: dict[str, Any]) -> tuple[str | None, str]:
    """Extrae la imagen en base64 y tipo MIME del JSON de respuesta de Google AI Studio."""
    candidates_parts = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for p in candidates_parts:
        inline = p.get("inlineData") or p.get("inline_data")
        if inline and inline.get("data"):
            extracted_b64 = inline.get("data")
            mime_type = inline.get("mimeType") or inline.get("mime_type") or "image/png"
            return extracted_b64, mime_type
    return None, "image/png"


def _call_google_ai_studio(
    base_url: str,
    model: str,
    timeout: float,
    api_key: str,
    parts: list[dict[str, Any]],
    client: httpx.Client | None,
    final_prompt: str,
    style: str,
    aspect_ratio: str,
) -> ToolResult:
    """Despacha la petición HTTP a la API de Google AI Studio y gestiona la respuesta."""
    endpoint = f"{base_url.rstrip('/')}/models/{model}:generateContent"
    payload = {"contents": [{"parts": parts}]}
    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout)

    try:
        response = http_client.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        )
        if response.status_code != 200:
            err_data = (
                response.json()
                if "application/json" in response.headers.get("content-type", "")
                else {}
            )
            err_msg = err_data.get("error", {}).get("message") or response.text
            logger.error("Error de Google AI Studio (%d): %s", response.status_code, err_msg)
            return ToolResult(
                success=False,
                output="",
                error=f"Error en Google AI Studio ({response.status_code}): {err_msg}",
                metadata={"error_code": "GOOGLE_AI_ERROR", "status_code": response.status_code},
            )

        extracted_b64, mime_type = _extract_generated_image(response.json())
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
        prompt,
        style,
        character_name,
        bool(character_image_base64),
        location_name,
        bool(location_image_base64),
        len(props),
    )

    api_key = api_key_override or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _handle_missing_api_key(api_key_override, final_prompt, style, aspect_ratio)

    cfg = _validate_google_ai_config()
    if isinstance(cfg, ToolResult):
        return cfg
    base_url, model, timeout = cfg

    parts = build_storyboard_request_parts(
        character_image_base64, location_image_base64, props, final_prompt
    )
    return _call_google_ai_studio(
        base_url,
        model,
        timeout,
        api_key,
        parts,
        client,
        final_prompt,
        style,
        aspect_ratio,
    )


__all__ = [
    "CANONICAL_STYLES",
    "DUMMY_PNG_BASE64",
    "StoryboardGeneratorArgs",
    "build_augmented_prompt",
    "detect_image_mime",
    "generate_storyboard_image",
]
