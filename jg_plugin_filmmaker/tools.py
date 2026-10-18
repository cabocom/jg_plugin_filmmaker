"""Definición canónica de herramientas AgentTool para jg_plugin_filmmaker.

Implementa los tres contratos funcionales del plugin cinematográfico:
1. treatment_structuring: Normaliza ideas en tratamiento en presente indicativo.
2. screenplay_formatter: Convierte tratamiento a formato literario Fountain.
3. shot_breakdown_detector: Desglosa la escena en planos técnicos canónicos '--- shot N (tipo) ---'.
4. plot_hole_detector: Audita la coherencia narrativa y detecta huecos de guion.
"""

import logging
from typing import Any, Literal, Protocol, runtime_checkable

from jg_sdk.contracts import AgentTool, RiskLevel, ToolResult, ToolType
from pydantic import BaseModel, ConfigDict, Field

from jg_plugin_filmmaker.breakdown import breakdown_screenplay_to_shots
from jg_plugin_filmmaker.formatting import format_screenplay
from jg_plugin_filmmaker.plot_holes import detect_plot_holes
from jg_plugin_filmmaker.structuring import structure_treatment

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Protocolo para Clientes LLM
# =====================================================================


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Protocolo formal para clientes de modelos de lenguaje."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Genera una respuesta textual a partir de un prompt."""
        ...


# =====================================================================
# 2. Submodelos de Dominio Pydantic v2
# =====================================================================


class CharacterContext(BaseModel):
    """Contexto formal de un personaje de la biblia dramática."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Nombre canónico del personaje.",
    )
    bio: str | None = Field(
        default=None,
        max_length=5000,
        description="Biografía o trasfondo del personaje.",
    )
    psychology: str | None = Field(
        default=None,
        max_length=5000,
        description="Rasgos psicológicos o motivaciones del personaje.",
    )
    costume_notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Notas de apariencia física o vestuario.",
    )
    role: str | None = Field(
        default=None,
        max_length=100,
        description="Rol dramático (protagonista, antagonista, secundario).",
    )


class LocationContext(BaseModel):
    """Contexto formal del escenario dramático."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Nombre o designación del escenario.",
    )
    type: str | None = Field(
        default="INT",
        max_length=20,
        description="Tipo de escenario (INT, EXT, INT/EXT).",
    )
    time_of_day: str | None = Field(
        default="DIA",
        max_length=30,
        description="Momento del día (DIA, NOCHE, CONTINUO).",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Descripción física del entorno.",
    )
    lighting_notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Atmósfera lumínica de la escena.",
    )
    sound_notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Ambiente o efectos sonoros sugeridos.",
    )


class ManualDiffItem(BaseModel):
    """Registro de intervención manual previa del autor en una etapa."""

    model_config = ConfigDict(extra="ignore")

    stage: Literal["raw", "structured", "screenplay", "shots"] = Field(
        default="structured",
        description="Etapa donde ocurrió la edición manual.",
    )
    original_ai: str = Field(
        default="",
        max_length=10000,
        description="Texto previo propuesto por la IA.",
    )
    user_override: str = Field(
        default="",
        max_length=10000,
        description="Texto modificado manualmente por el autor.",
    )
    applied_at: str | None = Field(
        default=None,
        max_length=50,
        description="Marca temporal ISO de la modificación.",
    )


class UserLocksModel(BaseModel):
    """Estructura estricta para el control de candados, términos fijos y preservación."""

    model_config = ConfigDict(extra="ignore")

    pinned_terms: dict[str, str] = Field(
        default_factory=dict,
        description="Mapeo de términos literales a sustituir o fijar invariables.",
    )
    manual_diffs: list[ManualDiffItem] = Field(
        default_factory=list,
        max_length=200,
        description="Lista de intervenciones manuales que no deben revertirse.",
    )
    archived_diffs: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=500,
        description="Historial no destructivo de diffs anteriores archivados.",
    )
    locked_fields: list[Literal["raw", "structured", "screenplay", "shots"]] = Field(
        default_factory=list,
        max_length=10,
        description="Etapas completamente bloqueadas ante regeneración.",
    )


class ScriptBlockItem(BaseModel):
    """Representación de un bloque de guion para análisis dramático."""

    model_config = ConfigDict(extra="ignore")

    type: str = Field(
        default="action",
        max_length=50,
        description="Tipo de bloque (action, dialogue, slugline, transition).",
    )
    content: str = Field(
        default="",
        max_length=10000,
        description="Contenido textual del bloque dramático.",
    )
    character: str | None = Field(
        default=None,
        max_length=120,
        description="Nombre del personaje si es bloque de diálogo.",
    )


# =====================================================================
# 3. Esquemas Pydantic v2 para Argumentos de Herramientas
# =====================================================================


class TreatmentStructuringArgs(BaseModel):
    """Argumentos de entrada para la herramienta treatment_structuring."""

    model_config = ConfigDict(extra="ignore")

    raw_text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Texto libre original o notas dramáticas del autor a normalizar.",
    )
    characters_context: list[CharacterContext] | None = Field(
        default=None,
        max_length=100,
        description="Lista de diccionarios con el contexto de personajes (nombre, psicología, etc.).",
    )
    location_context: LocationContext | None = Field(
        default=None,
        description="Diccionario con datos del escenario (nombre, tipo INT/EXT, iluminación, arte).",
    )
    user_locks: UserLocksModel | None = Field(
        default=None,
        description="Directivas, manual diffs y términos fijados por el usuario a preservar.",
    )


class ScreenplayFormatterArgs(BaseModel):
    """Argumentos de entrada para la herramienta screenplay_formatter."""

    model_config = ConfigDict(extra="ignore")

    structured_text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Tratamiento narrativo secuencial previamente normalizado.",
    )
    characters_context: list[CharacterContext] | None = Field(
        default=None,
        max_length=100,
        description="Lista de personajes para capitalización canónica y atribución de diálogos.",
    )
    location_context: LocationContext | None = Field(
        default=None,
        description="Contexto del escenario para generación de slugline estándar.",
    )
    user_locks: UserLocksModel | None = Field(
        default=None,
        description="Términos fijados y bloqueos manuales a preservar en el guión.",
    )


class ShotBreakdownDetectorArgs(BaseModel):
    """Argumentos de entrada para la herramienta shot_breakdown_detector."""

    model_config = ConfigDict(extra="ignore")

    screenplay_text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Texto del guión literario de la escena a desglosar técnicamente.",
    )


class PlotHoleDetectorArgs(BaseModel):
    """Argumentos de entrada para la herramienta plot_hole_detector."""

    model_config = ConfigDict(extra="ignore")

    blocks: list[ScriptBlockItem] = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Lista de bloques narrativos ordenados del guión a auditar.",
    )
    characters: list[CharacterContext] | None = Field(
        default=None,
        max_length=100,
        description="Contexto opcional de personajes de la Biblia dramática.",
    )
    locations: list[LocationContext] | None = Field(
        default=None,
        max_length=100,
        description="Contexto opcional de localizaciones de la Biblia.",
    )


# =====================================================================
# 4. Funciones Ejecutoras
# =====================================================================


def execute_treatment_structuring(
    raw_text: str,
    characters_context: list[CharacterContext | dict[str, Any]] | None = None,
    location_context: LocationContext | dict[str, Any] | None = None,
    user_locks: UserLocksModel | dict[str, Any] | None = None,
    llm_client: LLMClientProtocol | Any = None,
) -> ToolResult:
    """Ejecuta la estructuración del tratamiento respetando los candados del usuario."""
    try:
        chars_data = [
            c.model_dump() if isinstance(c, BaseModel) else c for c in (characters_context or [])
        ] or None

        loc_data = (
            location_context.model_dump()
            if isinstance(location_context, BaseModel)
            else location_context
        )

        locks_data = user_locks.model_dump() if isinstance(user_locks, BaseModel) else user_locks

        structured_output, step_meta = structure_treatment(
            raw_text=raw_text,
            characters_context=chars_data,
            location_context=loc_data,
            user_locks=locks_data,
            llm_client=llm_client,
            return_meta=True,
        )

        applied_locks_count = 0
        if locks_data and isinstance(locks_data, dict):
            pinned = locks_data.get("pinned_terms", {})
            diffs = locks_data.get("manual_diffs", [])
            applied_locks_count = (len(pinned) if isinstance(pinned, dict) else 0) + (
                len(diffs) if isinstance(diffs, list) else 0
            )

        return ToolResult(
            success=True,
            output=structured_output,
            metadata={
                "stage": "structured",
                "applied_locks_count": applied_locks_count,
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
) -> ToolResult:
    """Ejecuta la conversión a guión literario Fountain respetando user_locks."""
    try:
        chars_data = [
            c.model_dump() if isinstance(c, BaseModel) else c for c in (characters_context or [])
        ] or None

        loc_data = (
            location_context.model_dump()
            if isinstance(location_context, BaseModel)
            else location_context
        )

        locks_data = user_locks.model_dump() if isinstance(user_locks, BaseModel) else user_locks

        screenplay_output, step_meta = format_screenplay(
            structured_text=structured_text,
            characters_context=chars_data,
            location_context=loc_data,
            user_locks=locks_data,
            llm_client=llm_client,
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


def execute_shot_breakdown_detector(
    screenplay_text: str,
    llm_client: LLMClientProtocol | Any = None,
) -> ToolResult:
    """Ejecuta la propuesta de planos técnicos con el delimitador canónico '--- shot N (tipo) ---'."""
    try:
        annotated_text, shots_list = breakdown_screenplay_to_shots(
            screenplay_text=screenplay_text,
            llm_client=llm_client,
        )

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
        logger.exception("Fallo al desglosar planos técnicos: %s", e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al detectar planos: {type(e).__name__} en desglose técnico.",
            metadata={"error_code": "SHOT_BREAKDOWN_ERROR"},
        )


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


# =====================================================================
# 5. Descriptores AgentTool Canónicos
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

plot_hole_detector_tool = AgentTool(
    name="plot_hole_detector",
    description="Audita la secuencia narrativa y detecta inconsistencias dramáticas y de continuidad.",
    category="filmmaker",
    version="1.0.0",
    args_schema=PlotHoleDetectorArgs,
    func=execute_plot_hole_detector,
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
        plot_hole_detector_tool,
    ]
