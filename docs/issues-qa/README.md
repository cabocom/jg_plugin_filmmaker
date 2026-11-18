# Backlog QA & Seguridad Consolidado — `jg_plugin_filmmaker`

**Repositorio GitLab:** `https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker`  
**Responsable Asignado:** `cabocom` / Javier Gálvez (`assignee_ids: [553306]`)  
**Total de Issues en `jg_plugin_filmmaker`:** **3**

## Índice de Issues de Remediación

| ID | Severidad | Categoría | Título | Consenso Modelos | Archivo Local | Issue GitLab |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `ISSUE-12` | **Blocker** | `Anti-Fallback IA` | fix(llm): Eliminar is_mock_mode() implícito y captura silenciosa de errores/timeouts en invoke_llm_text y las 7 herramientas cognitivas | Detectado por: `argon`, `claude-sonnet`, `flash-3.8`, `hydrogen` (Unánime 4/4) | [ISSUE-12_remove_implicit_mock_and_silent_llm_fallbacks.md](./ISSUE-12_remove_implicit_mock_and_silent_llm_fallbacks.md) | [#2](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/2) |
| `ISSUE-13` | **Critical** | `Fiabilidad-Bug` | fix(tools): Conectar parámetros BYOK (api_key, provider) ignorados en handlers/script_tools.py y corregir saturación de _LLM_EXECUTOR | Detectado por: `argon` (`BYOK` y `_LLM_EXECUTOR`), `claude-sonnet` (`_LLM_EXECUTOR` y rama `ainvoke` muerta) | [ISSUE-13_wire_byok_credentials_and_llm_executor_timeout.md](./ISSUE-13_wire_byok_credentials_and_llm_executor_timeout.md) | [#3](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/3) |
| `ISSUE-14` | **Major** | `Seguridad / Complejidad-CodeSmell` | refactor(quality): Restringir bypass localhost en storyboard.py a entorno de test y dividir storyboard.py (>300 líneas) | Detectado por: `argon`, `claude-sonnet`, `hydrogen` | [ISSUE-14_restrict_storyboard_localhost_and_split_module.md](./ISSUE-14_restrict_storyboard_localhost_and_split_module.md) | [#4](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/4) |
