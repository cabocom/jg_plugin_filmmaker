"""Definición canónica de herramientas AgentTool para jg_plugin_filmmaker.

Implementa los contratos funcionales del plugin cinematográfico y actúa
como registro central re-exportando schemas y handlers.
"""

from __future__ import annotations

import logging

from jg_sdk.contracts import AgentTool, RiskLevel, ToolType

from jg_plugin_filmmaker.handlers import (
    execute_audit_character_usage,
    execute_extract_characters,
    execute_generate_storyboard,
    execute_plot_hole_detector,
    execute_screenplay_formatter,
    execute_shot_breakdown_detector,
    execute_treatment_structuring,
)
from jg_plugin_filmmaker.schemas import (
    CharacterAuditArgs,
    CharacterContext,
    CharacterExtractionArgs,
    LLMClientProtocol,
    LocationContext,
    ManualDiffItem,
    PlotHoleDetectorArgs,
    ScreenplayFormatterArgs,
    ScriptBlockItem,
    ShotBreakdownDetectorArgs,
    TreatmentStructuringArgs,
    UserLocksModel,
)
from jg_plugin_filmmaker.storyboard import StoryboardGeneratorArgs

logger = logging.getLogger(__name__)

# =====================================================================
# Descriptores AgentTool Canónicos
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

storyboard_generator_tool = AgentTool(
    name="generate_storyboard",
    description="Genera viñetas de storyboard cinematográficas 16:9 con Google AI Studio y acondicionamiento multimodal (@personaje, @localizacion, @atrezzo).",
    category="filmmaker",
    version="1.0.0",
    args_schema=StoryboardGeneratorArgs,
    func=execute_generate_storyboard,
    risk_level=RiskLevel.LOW,
    tool_type=ToolType.OBSERVER,
    read_only=True,
)

extract_characters_tool = AgentTool(
    name="extract_characters",
    description="Extrae personajes dramáticos reales (parlantes o mudos) con IA y validación determinista de grounding.",
    category="filmmaker",
    version="1.0.0",
    args_schema=CharacterExtractionArgs,
    func=execute_extract_characters,
    risk_level=RiskLevel.LOW,
    tool_type=ToolType.OBSERVER,
    read_only=True,
)

audit_character_usage_tool = AgentTool(
    name="audit_character_usage",
    description="Audita si un nombre corresponde a un personaje dramático real en uso o a un falso positivo léxico en acotaciones.",
    category="filmmaker",
    version="1.0.0",
    args_schema=CharacterAuditArgs,
    func=execute_audit_character_usage,
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
        storyboard_generator_tool,
        extract_characters_tool,
        audit_character_usage_tool,
    ]


__all__ = [
    # Protocols and Schemas
    "CharacterAuditArgs",
    "CharacterContext",
    "CharacterExtractionArgs",
    "LLMClientProtocol",
    "LocationContext",
    "ManualDiffItem",
    "PlotHoleDetectorArgs",
    "ScreenplayFormatterArgs",
    "ScriptBlockItem",
    "ShotBreakdownDetectorArgs",
    "StoryboardGeneratorArgs",
    "TreatmentStructuringArgs",
    "UserLocksModel",
    # Handlers
    "execute_audit_character_usage",
    "execute_extract_characters",
    "execute_generate_storyboard",
    "execute_plot_hole_detector",
    "execute_screenplay_formatter",
    "execute_shot_breakdown_detector",
    "execute_treatment_structuring",
    # Tools
    "audit_character_usage_tool",
    "extract_characters_tool",
    "get_filmmaker_tools",
    "plot_hole_detector_tool",
    "screenplay_formatter_tool",
    "shot_breakdown_detector_tool",
    "storyboard_generator_tool",
    "treatment_structuring_tool",
]
