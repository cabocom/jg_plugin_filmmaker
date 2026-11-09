# [REFACTOR-v2.0] Refactorización Estructural SOLID y Modularización de Tools y Esquemas Pydantic (`jg_plugin_filmmaker`)

- **Estado:** Abierto / Planificado
- **Fecha:** 2026-11-09
- **Proyecto:** `jg_plugin_filmmaker`
- **GitLab Issue:** [jg_plugin_filmmaker#1](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/1)
- **Asignado a:** Javier Gálvez (`@cabocom`)
- **Documento Maestro:** [`docs/refactor.md`](../../../docs/refactor.md)

---

## 1. Contexto y Objetivo (Arquitectura v2.0 SOLID)

Este issue planifica la refactorización estructural v2.0 de `jg_plugin_filmmaker` siguiendo las reglas de programación estructurada y principios **SOLID** de `AGENTS.md` (Sección 8) y `docs/refactor.md` (máximo **300 LOC por fichero/clase** y **40 LOC por función**).

## 2. Diagnóstico Real de Ficheros Monolíticos (`>300 LOC`)

De los 10 ficheros de producción (2.710 LOC), **3 superan el umbral de 300 líneas**:
1. `jg_plugin_filmmaker/tools.py` (**691 LOC**, 9 funciones + múltiples modelos Pydantic acoplados)
2. `jg_plugin_filmmaker/characters.py` (**541 LOC**, 5 funciones extensas)
3. `jg_plugin_filmmaker/formatting.py` (**369 LOC**)

## 3. Plan de Refactorización Estructural (Cero Roturas)

- **Fase 1 (Separación de Contratos Pydantic v2):**
  - Extraer todos los modelos `Input`/`Output` de `tools.py` a un subpaquete `jg_plugin_filmmaker/schemas/` aplicando límites estrictos `Field(..., max_length=...)` y `conlist`.
- **Fase 2 (Descomposición de `tools.py`, `characters.py` y `formatting.py`):**
  - Dividir `tools.py` en módulos de handlers por capacidad (`handlers/script_tools.py`, `handlers/visual_tools.py`, `handlers/continuity_tools.py`) y un registro limpio.
  - Modularizar `characters.py` separando extracción heurística, enriquecimiento LLM y construcción de perfiles de voz TTS.
  - Re-exportar símbolos públicos en `tools.py` y `__init__.py` (`__all__`) para mantener 100% de compatibilidad con los tests existentes.

## 4. Estimación con Gemini Flash y Criterios de Aceptación

- **Esfuerzo estimado:** 1 – 2 sesiones (~600k – 900k tokens Gemini Flash, ~30 – 45 min).
- **Criterios de cierre:**
  - [ ] Ningún módulo de `jg_plugin_filmmaker` supera las 300 LOC.
  - [ ] 100% de tests en verde (`pytest`) y linter limpio (`ruff check .`).
