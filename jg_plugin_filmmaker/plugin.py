"""Implementación principal del plugin FilmmakerPlugin para jg_agente.

Proporciona capacidades cognitivas de estructuración dramática, formateo de guión literario
y desglose técnico de planos cumpliendo estrictamente con los contratos de jg_agente_sdk.
"""

import logging
from typing import Any

from jg_sdk.contracts import AgentTool, BaseEngine, BasePlugin, PluginMetadata, RiskLevel

from jg_plugin_filmmaker.tools import get_filmmaker_tools

logger = logging.getLogger("jg_plugin_filmmaker")


class FilmmakerPlugin(BasePlugin):
    """Plugin de asistencia cinematográfica y preproducción para jg_agente."""

    def __init__(self) -> None:
        self._is_started: bool = False

    def get_plugin_metadata(self) -> PluginMetadata:
        """Retorna los metadatos canónicos del plugin filmmaker."""
        return PluginMetadata(
            name="filmmaker",
            version="2.3.0",
            description="Plugin de asistencia cinematográfica para guion, rodaje y detección de agujeros",
            author="Javier Gálvez",
            dependencies=[],
            jg_agente_version_min="1.0.0",
            tags=["filmmaker", "cinema", "screenplay", "shots", "plot_holes", "preproduction"],
            extra={"risk_level": RiskLevel.LOW},
        )

    def register_tools(self) -> list[AgentTool]:
        """Declara las cuatro herramientas canónicas provistas por el plugin."""
        return get_filmmaker_tools()

    def register_engines(self) -> dict[str, BaseEngine]:
        """Declara los motores cognitivos provistos por el plugin."""
        return {}

    async def startup(self) -> None:
        """Inicialización asíncrona al cargar el plugin en jg_agente."""
        logger.info("Inicializando FilmmakerPlugin v2.3.0...")
        self._is_started = True

    async def shutdown(self) -> None:
        """Liberación de recursos al descargar el plugin."""
        logger.info("Deteniendo FilmmakerPlugin...")
        self._is_started = False

    async def health_check(self) -> dict[str, Any]:
        """Reporta el estado de salud y capacidades activas del plugin."""
        return {
            "status": "ok",
            "plugin": "filmmaker",
            "version": "2.3.0",
            "started": self._is_started,
            "tools_count": len(self.register_tools()),
        }


# Exportación canónica para autodescubrimiento dinámico
PLUGIN_CLASS = FilmmakerPlugin
