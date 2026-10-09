# Contexto de Proyecto: jg_plugin_filmmaker

**Versión:** 1.0.0  
**Fecha:** 9 de octubre de 2026  
**Componente:** Plugin Satélite Cognitivo de Asistencia Cinematográfica  
**Stack:** Python 3.12/3.14, Pydantic v2, `jg-agente-sdk` (^1.0.0), Pytest, Ruff  

---

## 1. Visión y Propósito

`jg_plugin_filmmaker` proporciona las herramientas de procesamiento dramático e interpretación de guiones para el runtime `jg_agente`, sirviendo como backend cognitivo para la aplicación web `jg_filmmaker`.

## 2. Herramientas Canónicas Provistas

| Herramienta | Entrada Principal | Salida | Nivel de Riesgo |
|---|---|---|---|
| `treatment_structuring` | `raw_text`, `characters_context`, `location_context`, `user_locks` | Tratamiento en presente indicativo con `user_locks` aplicados | `RiskLevel.LOW` |
| `screenplay_formatter` | `structured_text`, `characters_context`, `location_context`, `user_locks` | Guión literario estándar Fountain con diálogos tipados | `RiskLevel.LOW` |
| `shot_breakdown_detector` | `screenplay_text` | Guión anotado con `--- shot N (tipo) ---` y metadata `shots` | `RiskLevel.LOW` |

## 3. Arquitectura y Reglas

- **Aislamiento Total:** El paquete es un repositorio independiente. Nunca importa de `jg_agente.app.*`.
- **Compatibilidad con `jg_sdk.contracts`:** Todos los contratos se adhieren a `AgentTool`, `BasePlugin` y `PluginMetadata`.
- **Preservación de User Locks:** Las herramientas de transformación reconocen y preservan de forma inmutable los términos fijados (`pinned_terms`) y las diferencias manuales (`manual_diffs`) guardadas por el usuario.
