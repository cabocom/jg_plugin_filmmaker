"""Handlers ejecutores para herramientas de guión y tratamiento."""

import logging
from typing import Any

from jg_sdk.contracts import ToolResult
from pydantic import BaseModel

from jg_plugin_filmmaker.formatting import format_screenplay
from jg_plugin_filmmaker.schemas.context import (
    CharacterContext,
    LocationContext,
    UserLocksModel,
)
from jg_plugin_filmmaker.schemas.protocols import LLMClientProtocol
from jg_plugin_filmmaker.structuring import structure_treatment

logger = logging.getLogger(__name__)


def _count_applied_locks(locks_data: dict[str, Any] | None) -> int:
    """Calcula el número de términos y diffs bloqueados aplicados."""
    if not locks_data or not isinstance(locks_data, dict):
        return 0
    pinned = locks_data.get("pinned_terms", {})
    diffs = locks_data.get("manual_diffs", [])
    return (len(pinned) if isinstance(pinned, dict) else 0) + (
        len(diffs) if isinstance(diffs, list) else 0
    )


def _extract_contexts(
    characters_context: list[CharacterContext | dict[str, Any]] | None,
    location_context: LocationContext | dict[str, Any] | None,
    user_locks: UserLocksModel | dict[str, Any] | None,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Extrae diccionarios nativos desde modelos Pydantic o dicts de contexto."""
    chars = [
        c.model_dump() if isinstance(c, BaseModel) else c for c in (characters_context or [])
    ] or None
    loc = (
        location_context.model_dump()
        if isinstance(location_context, BaseModel)
        else location_context
    )
    locks = user_locks.model_dump() if isinstance(user_locks, BaseModel) else user_locks
    return chars, loc, locks


def execute_treatment_structuring(
    raw_text: str,
    characters_context: list[CharacterContext | dict[str, Any]] | None = None,
    location_context: LocationContext | dict[str, Any] | None = None,
    user_locks: UserLocksModel | dict[str, Any] | None = None,
    llm_client: LLMClientProtocol | Any = None,
    api_key: Any | None = None,
    provider: str | None = None,
    **kwargs: Any,
) -> ToolResult:
    """Ejecuta la estructuración del tratamiento respetando los candados del usuario y BYOK."""
    try:
        chars_data, loc_data, locks_data = _extract_contexts(
            characters_context, location_context, user_locks
        )
        resolved_key = api_key or kwargs.get("api_key")
        resolved_prov = provider or kwargs.get("provider")

        structured_output, step_meta = structure_treatment(
            raw_text=raw_text,
            characters_context=chars_data,
            location_context=loc_data,
            user_locks=locks_data,
            llm_client=llm_client,
            api_key=resolved_key,
            provider=resolved_prov,
            return_meta=True,
        )

        return ToolResult(
            success=True,
            output=structured_output,
            metadata={
                "stage": "structured",
                "applied_locks_count": _count_applied_locks(locks_data),
                "source": step_meta.get("source", "heuristic_fallback"),
                "degraded": step_meta.get("degraded", True),
            },
        )
    except Exception as e:
        logger.exception("Fallo al estructurar tratamiento: %s", e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al estructurar tratamiento: {type(e).__name__} en procesamiento narrativo.",
            metadata={"error_code": "STRUCTURING_PROCESSING_ERROR"},
        )


def execute_screenplay_formatter(
    structured_text: str,
    characters_context: list[CharacterContext | dict[str, Any]] | None = None,
    location_context: LocationContext | dict[str, Any] | None = None,
    user_locks: UserLocksModel | dict[str, Any] | None = None,
    llm_client: LLMClientProtocol | Any = None,
    api_key: Any | None = None,
    provider: str | None = None,
    **kwargs: Any,
) -> ToolResult:
    """Ejecuta la conversión a guión literario Fountain respetando user_locks y BYOK."""
    try:
        chars_data, loc_data, locks_data = _extract_contexts(
            characters_context, location_context, user_locks
        )
        resolved_key = api_key or kwargs.get("api_key")
        resolved_prov = provider or kwargs.get("provider")

        screenplay_output, step_meta = format_screenplay(
            structured_text=structured_text,
            characters_context=chars_data,
            location_context=loc_data,
            user_locks=locks_data,
            llm_client=llm_client,
            api_key=resolved_key,
            provider=resolved_prov,
            return_meta=True,
        )

        return ToolResult(
            success=True,
            output=screenplay_output,
            metadata={
                "stage": "screenplay",
                "format": "fountain",
                "source": step_meta.get("source", "heuristic_fallback"),
                "degraded": step_meta.get("degraded", True),
            },
        )
    except Exception as e:
        logger.exception("Fallo al formatear guión literario: %s", e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al formatear guión: {type(e).__name__} en conversión Fountain.",
            metadata={"error_code": "FORMATTER_PROCESSING_ERROR"},
        )
