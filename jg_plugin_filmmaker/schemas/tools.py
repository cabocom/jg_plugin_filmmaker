"""Esquemas Pydantic v2 para argumentos de entrada de herramientas AgentTool."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jg_plugin_filmmaker.schemas.context import (
    CharacterContext,
    LocationContext,
    ScriptBlockItem,
    UserLocksModel,
)


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


class CharacterExtractionArgs(BaseModel):
    """Argumentos de entrada para la herramienta extract_characters."""

    model_config = ConfigDict(extra="ignore")

    text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Texto de tratamiento o guion cinematográfico a analizar.",
    )
    existing_characters: list[CharacterContext | dict[str, Any]] | None = Field(
        default=None,
        max_length=100,
        description="Personajes previamente registrados en la Biblia.",
    )


class CharacterAuditArgs(BaseModel):
    """Argumentos de entrada para la herramienta audit_character_usage."""

    model_config = ConfigDict(extra="ignore")

    character_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Nombre del personaje a auditar en las escenas.",
    )
    scene_texts: list[str] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Textos de las escenas o bloques donde se audita la presencia real del personaje.",
    )
