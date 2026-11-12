"""Handlers ejecutores para herramientas de continuidad y personajes."""

import logging
from typing import Any

from jg_sdk.contracts import ToolResult
from pydantic import BaseModel

from jg_plugin_filmmaker.characters import (
    audit_character_usage,
    extract_characters,
)
from jg_plugin_filmmaker.plot_holes import detect_plot_holes
from jg_plugin_filmmaker.schemas.context import (
    CharacterContext,
    LocationContext,
    ScriptBlockItem,
)
from jg_plugin_filmmaker.schemas.protocols import LLMClientProtocol

logger = logging.getLogger(__name__)


def execute_plot_hole_detector(
    blocks: list[ScriptBlockItem | dict[str, Any]],
    characters: list[CharacterContext | dict[str, Any]] | None = None,
    locations: list[LocationContext | dict[str, Any]] | None = None,
    llm_client: LLMClientProtocol | Any = None,
) -> ToolResult:
    """Ejecuta la auditoría dramática de agujeros de guión."""
    try:
        blocks_data = [b.model_dump() if isinstance(b, BaseModel) else b for b in blocks]
        chars_data = [
            c.model_dump() if isinstance(c, BaseModel) else c for c in (characters or [])
        ] or None
        locs_data = [
            loc.model_dump() if isinstance(loc, BaseModel) else loc for loc in (locations or [])
        ] or None

        holes = detect_plot_holes(
            blocks=blocks_data,
            characters=chars_data,
            locations=locs_data,
            llm_client=llm_client,
        )

        return ToolResult(
            success=True,
            output=f"Auditoría dramática completada: {len(holes)} agujero(s) detectado(s).",
            metadata={
                "stage": "plot_holes",
                "detected_holes": holes,
                "total_holes": len(holes),
            },
        )
    except Exception as e:
        logger.exception("Fallo al auditar agujeros de guión: %s", e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al auditar agujeros de guión: {type(e).__name__} en análisis dramático.",
            metadata={"error_code": "PLOT_HOLE_DETECTION_ERROR"},
        )


def execute_extract_characters(
    text: str,
    existing_characters: list[CharacterContext | dict[str, Any]] | None = None,
    llm_client: LLMClientProtocol | Any = None,
    **kwargs: Any,
) -> ToolResult:
    """Extrae personajes dramáticos con análisis semántico y validación de grounding."""
    try:
        existing_data = [
            c.model_dump() if isinstance(c, BaseModel) else c for c in (existing_characters or [])
        ]
        res = extract_characters(
            text=text,
            existing_characters=existing_data,
            llm_client=llm_client,
        )
        return ToolResult(
            success=True,
            output=f"Extracción completada: {len(res['characters'])} personaje(s) identificado(s).",
            metadata=res,
        )
    except Exception as e:
        logger.exception("Fallo al extraer personajes con IA: %s", e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo en extracción de personajes: {type(e).__name__}",
            metadata={"error_code": "CHARACTER_EXTRACTION_ERROR"},
        )


def execute_audit_character_usage(
    character_name: str,
    scene_texts: list[str],
    llm_client: LLMClientProtocol | Any = None,
    **kwargs: Any,
) -> ToolResult:
    """Audita si un personaje interviene realmente como entidad dramática o si es un falso positivo léxico."""
    try:
        res = audit_character_usage(
            character_name=character_name,
            scene_texts=scene_texts,
            llm_client=llm_client,
        )
        return ToolResult(
            success=True,
            output=f"Auditoría de '{character_name}': in_use={res.get('in_use', False)}",
            metadata=res,
        )
    except Exception as e:
        logger.exception("Fallo al auditar uso de personaje '%s': %s", character_name, e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo en auditoría de personaje: {type(e).__name__}",
            metadata={"error_code": "CHARACTER_AUDIT_ERROR"},
        )
