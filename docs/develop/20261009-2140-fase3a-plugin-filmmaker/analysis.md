# Análisis Técnico: Fase 3A — Plugin Canónico para jg_agente (SDK Contracts & Pytest)

**Proyecto:** `jg_plugin_filmmaker`  
**Ruta:** `docs/develop/20261009-2140-fase3a-plugin-filmmaker/analysis.md`  
**Fecha:** 9 de octubre de 2026, 21:40 CET  
**Componente:** Plugin Python Satélite para `jg_agente`  
**Autor:** Antigravity (Ingeniero de Software Senior)  

---

## 1. Prompt Recibido

```markdown
[PROJECT: jg_plugin_filmmaker] - Fase 3A: Plugin Canónico para jg_agente (SDK contracts & Pytest)

Actúa como Ingeniero de Software Senior especializado en Python 3.12 y en la arquitectura desacoplada de jg_ia y LangGraph.

Vamos a implementar el plugin Python satélite jg_plugin_filmmaker en el workspace javiergalvez-ia. Este plugin proporcionará a jg_agente las capacidades cognitivas de estructuración dramática, formateo de guion y desglose técnico de planos para abastecer a la aplicación web jg_filmmaker.

### CONTEXTO Y DOCUMENTACIÓN TÉCNICA:
- Contratos canónicos: jg_agente_sdk (jg_sdk.contracts)
- Especificación del contrato: jg_filmmaker/docs/specs/03_jg_plugin_filmmaker_contract.md
- Especificación de bloqueos y pipeline: jg_filmmaker/docs/specs/02_pipeline_stages_and_locks.md
- Nomenclatura canónica de planos: jg_filmmaker/docs/specs/04_shots_takes_media_management.md
- Regla de Oro jg_ia: Un plugin es un repositorio desacoplado. Queda terminantemente PROHIBIDO importar nada de `jg_agente.app.*`. Solo se importan contratos de `jg_sdk.contracts` (AgentTool, BasePlugin, PluginMetadata, RiskLevel, ToolResult, etc.).

### DIRECTRICES DE IMPLEMENTACIÓN:
1. Inicialización del Repositorio:
   - Crear el directorio `jg_plugin_filmmaker` (o inicializar mediante `jg plugin init jg_plugin_filmmaker` si está disponible en el entorno virtual activo).
   - Configurar `pyproject.toml` con metadatos del plugin, dependencias (`pydantic>=2.0`, `jg-agente-sdk` o path editable a `../jg_agente_sdk`), y el entry-point formal:
     `[project.entry-points."jg_agente.plugins"]`
     `filmmaker = "jg_plugin_filmmaker.plugin:FilmmakerPlugin"`

2. Clase Principal del Plugin (`FilmmakerPlugin`):
   - Hereda de `BasePlugin`.
   - `get_metadata()` devuelve `PluginMetadata(name="filmmaker", version="1.0.0", description="Plugin de asistencia cinematográfica para guion y rodaje", risk_level=RiskLevel.LOW, ...)`.
   - Registra 3 herramientas (`AgentTool`).

3. Las 3 Herramientas Canónicas (`AgentTool` con `RiskLevel.LOW`):
   A. `treatment_structuring`
   B. `screenplay_formatter`
   C. `shot_breakdown_detector`

4. Suite de Pruebas con Pytest (`tests/`):
   - Crear tests unitarios exhaustivos para cada una de las 3 herramientas.
   - Test específico que verifique que un `pinned_terms` en `user_locks` (ej: "Javi" -> "Javier") se respeta en la salida de `treatment_structuring`.
   - Test que verifique que `shot_breakdown_detector` devuelve la sintaxis exacta `--- shot N (tipo) ---`.

5. Vinculación en Desarrollo:
   - Enlazar el plugin con `jg link jg_plugin_filmmaker -t jg_agente/plugins`.
```

---

## 2. Análisis Técnico y Arquitectura de Solución

### 2.1. Regla de Oro del Ecosistema y Desacoplamiento
- Se mantiene independencia estricta entre el plugin y el núcleo de `jg_agente`.
- No se realiza ninguna importación hacia `jg_agente.app.*`.
- El plugin se apoya al 100% en los contratos tipados de `jg_sdk.contracts` (`AgentTool`, `BasePlugin`, `PluginMetadata`, `RiskLevel`, `ToolResult`, `ToolType`).

### 2.2. Diseño de las 3 Herramientas Canónicas
1. **`treatment_structuring`**:
   - Transforma texto libre en tratamiento cinematográfico estructurado en presente continuo.
   - Aplica contexto de personajes y localizaciones si se proveen.
   - **Mecanismo de Respeto a `user_locks`**:
     * Mapeo `pinned_terms`: Sustitución forzada y respetuosa de límites de palabra de términos fijados por el usuario (ej: `{"Javi": "Javier"}`).
     * `manual_diffs`: Sustitución de frases originalmente propuestas por la IA por los overrides fijados por el usuario.
2. **`screenplay_formatter`**:
   - Transforma el tratamiento en sintaxis estándar de guión cinematográfico Fountain.
   - Encabezados en mayúsculas (`INT.` / `EXT.`), párrafos de acción concisos, personajes en mayúsculas centrados sobre acotaciones y diálogos.
   - Aplica preservación de candados en etapa `screenplay`.
3. **`shot_breakdown_detector`**:
   - Clasificación heurística de encuadres (`PG`, `PM`, `PP`, `PD`, `PA`).
   - Salida estructurada delimitada estrictamente por el formato canónico `--- shot N (tipo) ---`.
   - Generación de metadata con el desglose tipado `shots` para persistencia directa en el modelo `Shot` de Laravel.

### 2.3. Vinculación en Desarrollo con `jg link`
- El SDK CLI proporciona la utilidad `jg link` que crea un symlink relativo seguro en `jg_agente/plugins/` apuntando hacia `jg_plugin_filmmaker/jg_plugin_filmmaker`.
