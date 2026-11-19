> ⚠️ **Nota:** Este repositorio es un *mirror* público sincronizado automáticamente desde [GitLab](https://gitlab.com/javiergalvez-ia). El desarrollo activo, pipelines CI/CD, *issues* y discusiones técnicas se gestionan en https://gitlab.com/javiergalvez-ia

<div align="center">

# 📽️ `jg_plugin_filmmaker`

### Plugin Satélite Cognitivo de Asistencia Cinematográfica para `jg_agente`
*Desglose de Producción, Detección de Personajes, Formateo Fountain y Storyboards*

[![GitLab CI/CD](https://img.shields.io/badge/GitLab_CI-Pipeline_Passing-108548?style=flat-square&logo=gitlab&logoColor=white)](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker)
[![Mirror to GitHub](https://img.shields.io/badge/GitHub-Mirror_Active-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/cabocom/jg_plugin_filmmaker)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SDK](https://img.shields.io/badge/SDK-jg--agente--sdk-e92063?style=flat-square)](https://pypi.org/project/jg-agente-sdk/)
[![Pydantic v2](https://img.shields.io/badge/Contracts-Pydantic_v2-e92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/Tests-62_passing-success?style=flat-square&logo=pytest&logoColor=white)](#instalación-pruebas-y-enlace)

</div>

---

**jg_plugin_filmmaker** es un plugin canónico de extensión satélite para el agente cognitivo `jg_agente`, desarrollado bajo la arquitectura modular del ecosistema `javiergalvez-ia`.

Proporciona capacidades cognitivas de asistencia dramática y preproducción cinematográfica para la aplicación web `jg_filmmaker`:
1. **`treatment_structuring`**: Normalización de notas libres a tratamiento en presente indicativo, respetando candados y términos fijados del autor (`user_locks`).
2. **`screenplay_formatter`**: Transformación de tratamiento a formato canónico de guión literario (Fountain / Courier) preservando encabezados, acciones y diálogos.
3. **`shot_breakdown_detector`**: Detección y propuesta de planos técnicos de rodaje empleando estrictamente la sintaxis canónica:
   `--- shot N (tipo) ---` (ejemplos: `--- shot 1 (PG) ---`, `--- shot 2 (PM) ---`, `--- shot 3 (PP) ---`).

---

## Desacoplamiento y Contratos

- **SDK Canónico:** Utiliza exclusivamente contratos de `jg_sdk.contracts` (`AgentTool`, `BasePlugin`, `PluginMetadata`, `RiskLevel`, `ToolResult`, `ToolType`).
- **Validación Estricta:** Validación de esquemas con Pydantic v2.
- **Cero dependencias internas:** No importa nada de `jg_agente.app.*`.
- **Nivel de Riesgo:** `RiskLevel.LOW` (herramientas de análisis y formateo sin efectos secundarios destructivos).

---

## Instalación, Pruebas y Enlace

```bash
# 1. Configurar entorno y dependencias (.venv + SDK)
bash install.sh

# 2. Ejecutar suite de pruebas unitarias (10 tests)
./.venv/bin/pytest

# 3. Validar con linter Ruff
./.venv/bin/ruff check .

# 4. Vincular a jg_agente en desarrollo
jg link jg_plugin_filmmaker -t jg_agente/plugins
```

---

## Documentación Detallada

Consulta la especificación técnica completa y esquemas Pydantic en:
- [PROJECT_CONTEXT.md](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/PROJECT_CONTEXT.md)
