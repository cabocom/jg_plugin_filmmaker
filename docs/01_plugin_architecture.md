# 01. Arquitectura y Contratos del SDK (`jg_plugin_filmmaker`)

[← Volver al Índice de Documentación](README.md) | [02. Especificación de Herramientas →](02_tools_specification.md)

---

## 1. Visión y Rol en el Ecosistema

`jg_plugin_filmmaker` es un componente satélite desacoplado que actúa como el cerebro cognitivo de asistencia cinematográfica para el agente central `jg_agente`.

Suministra herramientas de procesamiento de lenguaje natural y formateo dramático para abastecer la aplicación web `jg_filmmaker`.

```text
┌────────────────────────────────────────────────────────┐
│               jg_filmmaker (Laravel 12)                │
│         Solicita estructuración / formateo vía HTTP    │
└───────────────────────────┬────────────────────────────┘
                            │ POST /api/v1/tools/* (HMAC)
                            ▼
┌────────────────────────────────────────────────────────┐
│              jg_agente (FastAPI / LangGraph)           │
│   PluginManager descubre jg_plugin_filmmaker           │
└───────────────────────────┬────────────────────────────┘
                            │ Ejecuta Tool (async)
                            ▼
┌────────────────────────────────────────────────────────┐
│                 jg_plugin_filmmaker                    │
│   - TreatmentStructuringTool                           │
│   - ScreenplayFormatterTool                            │
│   - ShotBreakdownDetectorTool                          │
└────────────────────────────────────────────────────────┘
```

---

## 2. Regla de Oro de Desacoplamiento

El paquete es un repositorio Python completamente independiente:
1. **Prohibición de importaciones del Core:** No importa absolutamente nada de `jg_agente.app.*`.
2. **Fuente Única de Verdad (SSOT):** Consume exclusivamente las interfaces y modelos de datos tipados provistos por el SDK canónico `jg_sdk.contracts` (`jg-agente-sdk`):
   - `AgentTool`: Interfaz base para herramientas invocables.
   - `BasePlugin`: Contrato de inicialización y registro de capacidades.
   - `PluginMetadata`: Metadatos del plugin (nombre, versión, capacidades).
   - `RiskLevel`: Nivel de riesgo (`RiskLevel.LOW` para las 3 herramientas).
   - `ToolResult`: Envoltorio estructurado de respuesta con estado `success`, `data` y `error`.

---

## 3. Clase Principal del Plugin (`FilmmakerPlugin`)

En [plugin.py](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/src/jg_plugin_filmmaker/plugin.py):
```python
class FilmmakerPlugin(BasePlugin):
    async def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="filmmaker",
            version="1.0.0",
            description="Plugin cognitivo de asistencia y desglose cinematográfico",
            author="Javier Gálvez",
            capabilities=[
                "treatment_structuring",
                "screenplay_formatter",
                "shot_breakdown_detector",
            ],
        )

    async def get_tools(self) -> list[AgentTool]:
        return [
            TreatmentStructuringTool(),
            ScreenplayFormatterTool(),
            ShotBreakdownDetectorTool(),
        ]
```
