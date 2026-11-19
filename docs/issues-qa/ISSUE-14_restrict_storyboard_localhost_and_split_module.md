# [ISSUE-14] [jg_plugin_filmmaker] refactor(quality): Restringir bypass localhost en storyboard.py a entorno de test y dividir storyboard.py (>300 líneas)

- **ID Maestro QA:** `ISSUE-14`
- **Proyecto Destino:** `javiergalvez-ia/jg_plugin_filmmaker`
- **Asignado a:** `cabocom` / Javier Gálvez (`assignee_ids: [553306]`)
- **Milestone:** `QA & Anti-Fallback Hardening (Nov-Dic 2026)`
- **Labels:** `qa-audit, priority::high, security, solid, sonar-debt`
- **GitLab Issue Remoto:** [jg_plugin_filmmaker#4](https://gitlab.com/javiergalvez-ia/jg_plugin_filmmaker/-/work_items/4)

---

- **Severidad y Categoría:** `Major` | `Seguridad` / `Complejidad-CodeSmell`
- **Consenso de Auditores:** Detectado por: `argon`, `claude-sonnet`, `hydrogen`
- **Evidencia Exacta:**
  - `jg_plugin_filmmaker/jg_plugin_filmmaker/storyboard.py:1-310` (`310` líneas; `generate_storyboard_image` con `178` líneas; bypass `localhost`/`127.0.0.1` en `:182-186`; `except Exception: pass` en `:88`).
- **Solución Técnica Propuesta:**
  1. Restringir la excepción de `http://localhost` / `127.0.0.1` en `storyboard.py:182-186` exclusivamente a cuando `is_mock_mode()` o entorno de test esté activo.
  2. Extraer la construcción del prompt visual y la validación/decodificación MIME (`detect_image_mime`, capturando `(binascii.Error, ValueError)`) a un submódulo auxiliar para dejar `storyboard.py` por debajo de 300 líneas y `generate_storyboard_image` por debajo de 40 líneas.
- **Criterios de Aceptación (Checklist verificable):**
  - [x] Ningún archivo en `jg_plugin_filmmaker/jg_plugin_filmmaker/` supera las 300 líneas.
