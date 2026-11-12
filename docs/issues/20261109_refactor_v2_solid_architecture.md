# [REFACTOR-v2.0] Refactorización Estructural SOLID y Modularización de Tools y Esquemas Pydantic (`jg_plugin_filmmaker`)

- **Estado:** Cerrado / Completado
- **Fecha:** 2026-11-12
- **Proyecto:** `jg_plugin_filmmaker`
- **GitLab Issue:** [jg_plugin_filmmaker#1](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/1)
- **Asignado a:** Javier Gálvez (`@cabocom`)
- **Documento Maestro:** [`docs/refactor.md`](../../../docs/refactor.md)

---

## 1. Contexto y Objetivo (Arquitectura v2.0 SOLID)

Este issue planifica y ejecuta la refactorización estructural v2.0 de `jg_plugin_filmmaker` siguiendo las reglas de programación estructurada y principios **SOLID** de `AGENTS.md` (Sección 8) y `docs/refactor.md` (máximo **300 LOC por fichero/clase** y **40 LOC por función**).

## 2. Diagnóstico Real de Ficheros Monolíticos (`>300 LOC`)

De los 10 ficheros de producción (2.710 LOC), **3 superaban el umbral de 300 líneas**:
1. `jg_plugin_filmmaker/tools.py` (**691 LOC**, 9 funciones + múltiples modelos Pydantic acoplados) -> Reducido a **174 LOC**.
2. `jg_plugin_filmmaker/characters.py` (**541 LOC**, 5 funciones extensas) -> Reducido a **299 LOC**.
3. `jg_plugin_filmmaker/formatting.py` (**369 LOC**) -> Reducido a **216 LOC**.

## 3. Implementación Estructural Realizada (Cero Roturas)

- **Fase 1 (Separación de Contratos Pydantic v2 en `schemas/`):**
  - `schemas/protocols.py` (12 LOC): `LLMClientProtocol`.
  - `schemas/context.py` (150 LOC): Submodelos de dominio (`CharacterContext`, `LocationContext`, `ManualDiffItem`, `UserLocksModel`, `ScriptBlockItem`).
  - `schemas/tools.py` (137 LOC): Argumentos tipados Pydantic v2 (`TreatmentStructuringArgs`, `ScreenplayFormatterArgs`, `ShotBreakdownDetectorArgs`, `PlotHoleDetectorArgs`, `CharacterExtractionArgs`, `CharacterAuditArgs`).
  - `schemas/__init__.py` (33 LOC): Re-exportación completa de contratos.

- **Fase 2 (Descomposición de Handlers y Heurísticas):**
  - `handlers/script_tools.py` (125 LOC): `execute_treatment_structuring` y `execute_screenplay_formatter`.
  - `handlers/visual_tools.py` (65 LOC): `execute_shot_breakdown_detector` y `execute_generate_storyboard`.
  - `handlers/continuity_tools.py` (122 LOC): `execute_plot_hole_detector`, `execute_extract_characters` y `execute_audit_character_usage`.
  - `handlers/__init__.py` (25 LOC): Registro de handlers.
  - `stopwords.py` (255 LOC): Catálogo de términos cinematográficos y acotaciones (`CINEMATIC_STOPWORDS`).
  - `character_heuristics.py` (135 LOC): `is_cinematic_stopword`, `verify_textual_grounding` y `deterministic_extract_candidates`.
  - `dialogue_refiner.py` (193 LOC): Transformación de tercera persona a interlocución directa, enlaces, verbos y `process_indirect_dialogue`.
  - Re-exportación integral en `tools.py` (174 LOC), `characters.py` (299 LOC) y `formatting.py` (216 LOC) mediante `__all__` garantizando 100% de compatibilidad hacia atrás.

## 4. Criterios de Aceptación Verificados

- [x] Ningún módulo de `jg_plugin_filmmaker` supera las 300 LOC (máximo actual: 299 LOC en `characters.py`).
- [x] 100% de tests en verde (`pytest`: 62 pasados de 62) y linters limpios (`ruff check .`, `ruff format --check .`, `mypy`).
- [x] Contenedor `jg_filmmaker` refrescado y purgado.
