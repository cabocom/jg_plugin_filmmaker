# Walkthrough Técnico: Fase 3A — Plugin Canónico para jg_agente (SDK Contracts & Pytest)

**Proyecto:** `jg_plugin_filmmaker`  
**Ruta:** `docs/develop/20261009-2140-fase3a-plugin-filmmaker/walkthrough.md`  
**Fecha:** 9 de octubre de 2026, 21:40 CET  
**Versión:** 1.0.0  
**Stack:** Python 3.12/3.14, Pydantic v2, `jg-agente-sdk` (^1.0.0), Pytest 9.1, Ruff 0.16  

---

## 1. Resumen de Archivos Creados y Modificados

### 1.1. Configuración del Repositorio y Empaquetado
- [`pyproject.toml`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/pyproject.toml): Configuración con metadatos v1.0.0, entry-point formal `filmmaker = "jg_plugin_filmmaker.plugin:FilmmakerPlugin"`, dependencias y configuración para pytest y ruff.
- [`install.sh`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/install.sh): Script de aprovisionamiento de `.venv` y enlace editable hacia `../jg_agente_sdk`.
- [`.gitignore`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/.gitignore): Reglas de exclusión de entornos virtuales, caches de pruebas y `.env`.
- [`README.md`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/README.md) y [`PROJECT_CONTEXT.md`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/PROJECT_CONTEXT.md): Documentación del componente y tabla de herramientas.

### 1.2. Módulos del Plugin (`jg_plugin_filmmaker/`)
- [`jg_plugin_filmmaker/plugin.py`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/jg_plugin_filmmaker/plugin.py): Clase `FilmmakerPlugin` heredando de `BasePlugin`, implementando `get_plugin_metadata()`, `register_tools()`, `startup()`, `shutdown()` y `health_check()`.
- [`jg_plugin_filmmaker/tools.py`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/jg_plugin_filmmaker/tools.py): Definición de esquemas Pydantic v2 (`TreatmentStructuringArgs`, `ScreenplayFormatterArgs`, `ShotBreakdownDetectorArgs`), funciones de ejecución y descriptores canónicos `AgentTool` con `RiskLevel.LOW`.
- [`jg_plugin_filmmaker/structuring.py`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/jg_plugin_filmmaker/structuring.py): Lógica de normalización dramática y motor de preservación de `user_locks` (`pinned_terms` y `manual_diffs`).
- [`jg_plugin_filmmaker/formatting.py`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/jg_plugin_filmmaker/formatting.py): Conversor a formato estándar Fountain con diálogos estructurados, personajes en mayúsculas y acotaciones.
- [`jg_plugin_filmmaker/breakdown.py`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/jg_plugin_filmmaker/breakdown.py): Detección y marcado de planos técnicos con delimitador canónico `--- shot N (tipo) ---`.

### 1.3. Suite de Pruebas Unitarias (`tests/`)
- [`tests/test_filmmaker_tools.py`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/tests/test_filmmaker_tools.py): 9 pruebas exhaustivas que verifican:
  1. Metadatos y registro de 3 herramientas.
  2. Normalización básica con contexto.
  3. Respeto inmutable de `pinned_terms` en `user_locks` (ej: `Javi` ➜ `Javier`).
  4. Preservación de `manual_diffs` de etapas estructuradas.
  5. Formateo estándar Fountain.
  6. Preservación de `user_locks` en guión literario.
  7. Formato canónico delimitador `--- shot N (tipo) ---` y metadata `shots`.
  8. Invocación síncrona mediante `AgentTool.run()`.
  9. Ciclo de vida y health-check del plugin.
- [`tests/test_plugin.py`](file:///Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_plugin_filmmaker/tests/test_plugin.py): Prueba de integración con `MockPluginRunner` de `jg_sdk.testing`.

---

## 2. Resultados de Ejecución

### 2.1. Suite de Pruebas con Pytest
```bash
./.venv/bin/pytest
```
```text
..........                                                               [100%]
10 passed in 0.10s
```

### 2.2. Linter Ruff
```bash
./.venv/bin/ruff check .
```
```text
All checks passed!
```

### 2.3. Vinculación en Desarrollo (`jg link`)
```bash
./jg_agente_sdk/.venv/bin/jg link ./jg_plugin_filmmaker -t jg_agente/plugins
```
```text
✨ Plugin 'jg_plugin_filmmaker' enlazado con éxito:
   🔗 /Users/javiergalvez/Documents/Code/javiergalvez-ia/jg_agente/plugins/jg_plugin_filmmaker -> ../../jg_plugin_filmmaker/jg_plugin_filmmaker
```
Verificado symlink activo en `jg_agente/plugins/jg_plugin_filmmaker`.
