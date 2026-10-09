# Documentación Técnica de jg_plugin_filmmaker

[← Volver al README Principal](../README.md)

Este directorio contiene la documentación técnica y arquitectónica del plugin satélite **jg_plugin_filmmaker**, estructurada por conceptos de dominio e ingeniería.

---

## Índice de Documentos Arquitectónicos

| Documento | Título | Descripción |
|---|---|---|
| **[01_plugin_architecture.md](01_plugin_architecture.md)** | Arquitectura y Contratos del SDK | Aislamiento modular en Python 3.12, implementación de contratos canónicos de `jg-agente-sdk` (`AgentTool`, `BasePlugin`) y ciclo de vida. |
| **[02_tools_specification.md](02_tools_specification.md)** | Especificación de Herramientas Canónicas | Detalle de las 3 herramientas cognitivas (`treatment_structuring`, `screenplay_formatter`, `shot_breakdown_detector`), esquemas Pydantic v2 y sintaxis canónica de planos. |
| **[03_user_locks_resolution.md](03_user_locks_resolution.md)** | Preservación de Candados y Modificaciones | Algoritmo en Python para respetar campos bloqueados y sustituir términos canónicos del autor (`pinned_terms`). |
| **[04_testing_quality_cicd.md](04_testing_quality_cicd.md)** | Calidad, Testing y Enlace Symlink | Suite de 10 tests Pytest, linter Ruff, comando `jg link` y verificación en `scripts/check.sh`. |

---

## Directorios Complementarios

- **`develop/`:** Traza histórica de desarrollo del plugin.
