"""Definición canónica de herramientas AgentTool para jg_plugin_filmmaker.

Implementa los tres contratos funcionales del plugin cinematográfico:
1. treatment_structuring: Normaliza ideas en tratamiento en presente indicativo.
2. screenplay_formatter: Convierte tratamiento a formato literario Fountain.
3. shot_breakdown_detector: Desglosa la escena en planos técnicos canónicos '--- shot N (tipo) ---'.
"""

from typing import Any

from jg_sdk.contracts import AgentTool, RiskLevel, ToolResult, ToolType
from pydantic import BaseModel, Field

from jg_plugin_filmmaker.breakdown import breakdown_screenplay_to_shots
from jg_plugin_filmmaker.formatting import format_screenplay
from jg_plugin_filmmaker.structuring import structure_treatment

# =====================================================================
# 1. Esquemas Pydantic v2 para Argumentos
# =====================================================================


class TreatmentStructuringArgs(BaseModel):
    """Argumentos de entrada para la herramienta treatment_structuring."""

    raw_text: str = Field(
        ...,
        min_length=1,
        description="Texto libre original o notas dramáticas del autor a normalizar.",
    )
    characters_context: list[dict[str, Any]] | None = Field(
        default=None,
        description="Lista de diccionarios con el contexto de personajes (nombre, psicología, etc.).",
    )
    location_context: dict[str, Any] | None = Field(
        default=None,
        description="Diccionario con datos del escenario (nombre, tipo INT/EXT, iluminación, arte).",
    )
    user_locks: dict[str, Any] | None = Field(
        default=None,
        description="Directivas, manual diffs y términos fijados por el usuario a preservar.",
    )


class ScreenplayFormatterArgs(BaseModel):
    """Argumentos de entrada para la herramienta screenplay_formatter."""

    structured_text: str = Field(
        ...,
        min_length=1,
        description="Tratamiento narrativo secuencial previamente normalizado.",
    )
    characters_context: list[dict[str, Any]] | None = Field(
        default=None,
        description="Lista de personajes para capitalización canónica y atribución de diálogos.",
    )
    location_context: dict[str, Any] | None = Field(
        default=None,
        description="Contexto del escenario para generación de slugline estándar.",
    )
    user_locks: dict[str, Any] | None = Field(
        default=None,
        description="Términos fijados y bloqueos manuales a preservar en el guión.",
    )


class ShotBreakdownDetectorArgs(BaseModel):
    """Argumentos de entrada para la herramienta shot_breakdown_detector."""

    screenplay_text: str = Field(
        ...,
        min_length=1,
        description="Texto del guión literario de la escena a desglosar técnicamente.",
    )


# =====================================================================
# 2. Funciones Ejecutoras
# =====================================================================


def execute_treatment_structuring(
    raw_text: str,
    characters_context: list[dict[str, Any]] | None = None,
    location_context: dict[str, Any] | None = None,
    user_locks: dict[str, Any] | None = None,
) -> ToolResult:
    """Ejecuta la estructuración del tratamiento respetando los candados del usuario."""
    try:
        structured_output = structure_treatment(
            raw_text=raw_text,
            characters_context=characters_context,
            location_context=location_context,
            user_locks=user_locks,
        )

        applied_locks_count = 0
        if user_locks:
            pinned = user_locks.get("pinned_terms", {})
            diffs = user_locks.get("manual_diffs", [])
            applied_locks_count = len(pinned) + len(diffs)

        return ToolResult(
            success=True,
            output=structured_output,
            metadata={
                "stage": "structured",
                "applied_locks_count": applied_locks_count,
            },
        )
    except Exception as e:
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al estructurar tratamiento: {e}",
        )


def execute_screenplay_formatter(
    structured_text: str,
    characters_context: list[dict[str, Any]] | None = None,
    location_context: dict[str, Any] | None = None,
    user_locks: dict[str, Any] | None = None,
) -> ToolResult:
    """Ejecuta la conversión a guión literario Fountain respetando user_locks."""
    try:
        screenplay_output = format_screenplay(
            structured_text=structured_text,
            characters_context=characters_context,
            location_context=location_context,
            user_locks=user_locks,
        )

        return ToolResult(
            success=True,
            output=screenplay_output,
            metadata={
                "stage": "screenplay",
                "format": "fountain",
            },
        )
    except Exception as e:
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al formatear guión: {e}",
        )


def execute_shot_breakdown_detector(
    screenplay_text: str,
) -> ToolResult:
    """Ejecuta la propuesta de planos técnicos con el delimitador canónico '--- shot N (tipo) ---'."""
    try:
        annotated_text, shots_list = breakdown_screenplay_to_shots(screenplay_text)

        return ToolResult(
            success=True,
            output=annotated_text,
            metadata={
                "stage": "shots",
                "shots": shots_list,
                "total_shots": len(shots_list),
            },
        )
    except Exception as e:
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al detectar planos: {e}",
        )


# =====================================================================
# 3. Descriptores AgentTool Canónicos
# =====================================================================

treatment_structuring_tool = AgentTool(
    name="treatment_structuring",
    description="Transforma ideas informales en tratamiento cinematográfico estructurado en presente indicativo.",
    category="filmmaker",
    version="1.0.0",
    args_schema=TreatmentStructuringArgs,
    func=execute_treatment_structuring,
    risk_level=RiskLevel.LOW,
    tool_type=ToolType.OBSERVER,
    read_only=True,
)

screenplay_formatter_tool = AgentTool(
    name="screenplay_formatter",
    description="Convierte tratamiento narrativo estructurado a formato de guión literario estándar Fountain.",
    category="filmmaker",
    version="1.0.0",
    args_schema=ScreenplayFormatterArgs,
    func=execute_screenplay_formatter,
    risk_level=RiskLevel.LOW,
    tool_type=ToolType.OBSERVER,
    read_only=True,
)

shot_breakdown_detector_tool = AgentTool(
    name="shot_breakdown_detector",
    description="Propone la separación de planos técnicos de la escena con la sintaxis canónica '--- shot N (tipo) ---'.",
    category="filmmaker",
    version="1.0.0",
    args_schema=ShotBreakdownDetectorArgs,
    func=execute_shot_breakdown_detector,
    risk_level=RiskLevel.LOW,
    tool_type=ToolType.OBSERVER,
    read_only=True,
)


def get_filmmaker_tools() -> list[AgentTool]:
    """Retorna la lista ordenada de herramientas provistas por el plugin."""
    return [
        treatment_structuring_tool,
        screenplay_formatter_tool,
        shot_breakdown_detector_tool,
    ]
