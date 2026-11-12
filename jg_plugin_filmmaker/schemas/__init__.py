"""Subpaquete de esquemas Pydantic v2 y protocolos para jg_plugin_filmmaker."""

from jg_plugin_filmmaker.schemas.context import (
    CharacterContext,
    LocationContext,
    ManualDiffItem,
    ScriptBlockItem,
    UserLocksModel,
)
from jg_plugin_filmmaker.schemas.protocols import LLMClientProtocol
from jg_plugin_filmmaker.schemas.tools import (
    CharacterAuditArgs,
    CharacterExtractionArgs,
    PlotHoleDetectorArgs,
    ScreenplayFormatterArgs,
    ShotBreakdownDetectorArgs,
    TreatmentStructuringArgs,
)

__all__ = [
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
    "TreatmentStructuringArgs",
    "UserLocksModel",
]
