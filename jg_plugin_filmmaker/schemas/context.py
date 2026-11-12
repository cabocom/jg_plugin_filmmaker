"""Submodelos de contexto dramático y gobernanza narrativa para jg_plugin_filmmaker."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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
