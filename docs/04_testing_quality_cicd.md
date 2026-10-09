# 04. Calidad, Testing y Enlace Symlink (`jg_plugin_filmmaker`)

[← 03. Preservación de Candados](03_user_locks_resolution.md) | [Volver al Índice de Documentación](README.md)

---

## 1. Suite de Pruebas Automatizadas con Pytest

El plugin cuenta con una suite completa de 10 pruebas unitarias en `tests/test_filmmaker_tools.py` y `tests/test_plugin.py`:
- Registro y metadatos de las 3 herramientas.
- Validación de esquemas Pydantic y rechazo de tipos inválidos.
- Normalización de tratamiento respetando `pinned_terms`.
- Formateo de guión con mayúsculas y detección de diálogos.
- Desglose y numeración de planos técnicos con sintaxis canónica `--- shot N (tipo) ---`.

---

## 2. Linter y Verificación de Estilo

- Se emplea **Ruff** configurado en `pyproject.toml` (compatible con Python 3.12 y 3.14).
- Validación de código:
  ```bash
  ruff check .
  ruff format --check .
  ```

---

## 3. Enlace Dinámico con `jg_agente`

Para que el runtime de ejecución descubra el plugin sin necesidad de publicar en PyPI durante el desarrollo:
```bash
# Desde la raíz del workspace
jg link jg_plugin_filmmaker -t jg_agente/plugins
```
Esto genera un enlace simbólico en `jg_agente/plugins/jg_plugin_filmmaker`, permitiendo la recarga en caliente y el descubrimiento automático mediante `PluginManager`.

---

## 4. Integración en `scripts/check.sh`

El plugin está plenamente integrado en el pipeline CI/CD unificado del ecosistema:
- **Stage 1 (Lint):** `ruff check .`
- **Stage 3 (Test):** `pytest`
- **Stage 4 (Build):** Compilación de artefactos de distribución `sdist` y `wheel` (`python -m build`).
