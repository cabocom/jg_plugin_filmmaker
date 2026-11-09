> ⚠️ **Nota:** Este repositorio es un *mirror* público sincronizado automáticamente desde [GitLab](https://gitlab.com/javiergalvez-ia). El desarrollo activo, pipelines CI/CD, *issues* y discusiones técnicas se gestionan en https://gitlab.com/javiergalvez-ia

# jg_plugin_filmmaker

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
