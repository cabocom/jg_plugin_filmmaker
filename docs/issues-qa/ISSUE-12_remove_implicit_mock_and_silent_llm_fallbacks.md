# [ISSUE-12] [jg_plugin_filmmaker] fix(llm): Eliminar is_mock_mode() implícito y captura silenciosa de errores/timeouts en invoke_llm_text y las 7 herramientas cognitivas

- **ID Maestro QA:** `ISSUE-12`
- **Proyecto Destino:** `javiergalvez-ia/jg_plugin_filmmaker`
- **Asignado a:** `cabocom` / Javier Gálvez (`assignee_ids: [553306]`)
- **Milestone:** `QA & Anti-Fallback Hardening (Nov-Dic 2026)`
- **Labels:** `qa-audit, priority::blocker, anti-fallback`
- **GitLab Issue Remoto:** [jg_plugin_filmmaker#2](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/2)

---

- **Severidad y Categoría:** `Blocker` | `Anti-Fallback IA`
- **Consenso de Auditores:** Detectado por: `argon`, `claude-sonnet`, `flash-3.8`, `hydrogen` (Unánime 4/4)
- **Evidencia Exacta:**
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/llm.py:23-48, 82-183`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/structuring.py:210-241`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/formatting.py:206-214`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/breakdown.py:132-182`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/plot_holes.py:89-155`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/characters.py:94-151, 216-289`
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/storyboard.py:160-173`
- **Solución Técnica Propuesta:**
  1. En `llm.py`, eliminar la activación implícita de modo mock por ausencia de API keys (`is_mock_mode()`) y hacer que `invoke_llm_text()` lance una excepción explícita (`RuntimeError` / `TimeoutError`) ante falta de credenciales, timeout o fallo HTTP del proveedor LLM.
  2. Eliminar los motores heurísticos de fallback en `structuring.py`, `formatting.py`, `breakdown.py`, `plot_holes.py`, `characters.py` y el retorno de `DUMMY_PNG_BASE64` con `success=True` cuando falta `api_key` en `storyboard.py:160-173`, devolviendo `ToolResult(success=False, error=...)`.
  3. Actualizar `tests/test_llm_resilience_and_mock.py` para exigir comportamiento *Fail-Loud* (`success=False`) cuando el LLM falla.
- **Criterios de Aceptación (Checklist verificable):**
  - [ ] Ante un timeout o excepción del LLM en cualquiera de las 7 herramientas de `jg_plugin_filmmaker`, la herramienta retorna `ToolResult(success=False, error=...)`.
  - [ ] Si falta `GOOGLE_AI_API_KEY` en modo real, `generate_storyboard` retorna `ToolResult(success=False)` y nunca `DUMMY_PNG_BASE64`.
