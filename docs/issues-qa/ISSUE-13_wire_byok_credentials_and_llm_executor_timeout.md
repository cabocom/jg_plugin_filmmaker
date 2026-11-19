# [ISSUE-13] [jg_plugin_filmmaker] fix(tools): Conectar parámetros BYOK (api_key, provider) ignorados en handlers/script_tools.py y corregir saturación de _LLM_EXECUTOR

- **ID Maestro QA:** `ISSUE-13`
- **Proyecto Destino:** `javiergalvez-ia/jg_plugin_filmmaker`
- **Asignado a:** `cabocom` / Javier Gálvez (`assignee_ids: [553306]`)
- **Milestone:** `QA & Anti-Fallback Hardening (Nov-Dic 2026)`
- **Labels:** `qa-audit, priority::critical, bug`
- **GitLab Issue Remoto:** [jg_plugin_filmmaker#3](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/3)

---

- **Severidad y Categoría:** `Critical` | `Fiabilidad-Bug`
- **Consenso de Auditores:** Detectado por: `argon` (`BYOK` y `_LLM_EXECUTOR`), `claude-sonnet` (`_LLM_EXECUTOR` y rama `ainvoke` muerta)
- **Evidencia Exacta:**
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/schemas/tools.py:40-47, 74-81`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/handlers/script_tools.py:32-78, 81-127`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/llm.py:18-20, 125-173`
- **Solución Técnica Propuesta:**
  1. En `execute_treatment_structuring` y `execute_screenplay_formatter` (`handlers/script_tools.py`), extraer `api_key` y `provider` y pasarlos a `structure_treatment()` / `format_screenplay()` -> `invoke_llm_text()` para instanciar o invocar el cliente LLM con las credenciales BYOK suministradas.
  2. En `llm.py:125-173`, eliminar la rama muerta `if hasattr(llm, "ainvoke"):` (`:137-155`), unificar la ejecución en un único helper con timeout de socket HTTP configurado en el cliente subyacente (`timeout=timeout`) para que los workers de `_LLM_EXECUTOR` no queden bloqueados indefinidamente.
- **Criterios de Aceptación (Checklist verificable):**
  - [x] Test unitario verificando que `api_key` y `provider` pasados a `treatment_structuring` y `screenplay_formatter` se utilizan efectivamente en la llamada al proveedor LLM.
