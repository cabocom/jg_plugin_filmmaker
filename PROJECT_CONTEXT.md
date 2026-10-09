# Contexto de Proyecto: jg_plugin_filmmaker

**Versión:** 2.0.0  
**Fecha:** 9 de octubre de 2026  
**Componente:** Plugin Satélite Cognitivo de Asistencia Cinematográfica para `jg_agente`  
**Stack Tecnológico:** Python 3.12 / 3.14, Pydantic v2, `jg-agente-sdk` (^1.0.0), Pytest, Ruff  
**Estado:** Totalmente implementado, verificado con 10 tests unitarios y enlazado en `jg_agente/plugins`.

---

## 1. Visión y Propósito en el Ecosistema

`jg_plugin_filmmaker` es un componente satélite desacoplado que dota al agente central `jg_agente` de capacidades especializadas para el análisis dramático, normalización de guiones y desglose de producción cinematográfica.

Actúa como backend de procesamiento cognitivo para la aplicación web `jg_filmmaker`:
- **Aislamiento Total:** El plugin es un repositorio Python independiente. Tiene prohibido importar módulos internos de `jg_agente.app.*`.
- **Contratos Canónicos:** Implementa estrictamente la interfaz `BasePlugin` y `AgentTool` definidas en `jg_sdk.contracts` (`jg-agente-sdk`).
- **Nivel de Riesgo:** Todas las herramientas operan bajo `RiskLevel.LOW`, dado que son transformaciones puras de texto sin efectos secundarios destructivos en el sistema.

---

## 2. Catálogo de Herramientas y Esquemas Pydantic v2

### 2.1. `treatment_structuring`
- **Módulo:** `src/jg_plugin_filmmaker/tools/structuring.py`
- **Propósito:** Normaliza texto libre, notas o borradores en prosa de tratamiento cinematográfico en presente indicativo.
- **Esquema de Entrada (`TreatmentInput`):**
  - `raw_text` (str): Texto bruto inicial redactado por el cineasta.
  - `characters_context` (list[str], opcional): Lista de nombres y arquetipos de personajes de la escena.
  - `location_context` (str, opcional): Slugline o nombre de la localización (e.g., `BAR CENTRAL (INT)`).
  - `user_locks` (dict[str, Any], opcional): Estructura de bloqueos y `pinned_terms` del autor.
- **Salida (`ToolResult`):** Texto de tratamiento estructurado respetando la inmutabilidad de los términos bloqueados.

### 2.2. `screenplay_formatter`
- **Módulo:** `src/jg_plugin_filmmaker/tools/formatting.py`
- **Propósito:** Transforma el tratamiento en prosa a formato literario estándar Fountain (Courier 12pt).
- **Esquema de Entrada (`ScreenplayInput`):**
  - `structured_text` (str): Tratamiento dramático previo.
  - `characters_context` (list[str], opcional): Personajes reconocidos para sangría y mayúsculas de diálogo.
  - `location_context` (str, opcional): Localización para la construcción del encabezado de escena.
  - `user_locks` (dict[str, Any], opcional): Términos canónicos fijados y campos congelados.
- **Salida (`ToolResult`):** Guión formateado con sluglines estándar (`INT. LOCALIZACION - DIA`), bloques de acción narrativa y parlamentos tipificados (`PERSONAJE\n(acotación)\nDiálogo`).

### 2.3. `shot_breakdown_detector`
- **Módulo:** `src/jg_plugin_filmmaker/tools/breakdown.py`
- **Propósito:** Analiza el guión literario y propone un desglose técnico de planos de cámara para rodaje.
- **Esquema de Entrada (`BreakdownInput`):**
  - `screenplay_text` (str): Contenido en formato guión literario.
- **Sintaxis Canónica:** Emplea estrictamente delimitadores canónicos:
  `--- shot N (tipo) ---` (ejemplos: `--- shot 1 (PG) ---`, `--- shot 2 (PM) ---`, `--- shot 3 (PP) ---`, `--- shot 4 (PD) ---`).
- **Salida (`ToolResult`):**
  - `data["shots"]`: Lista de diccionarios con metadatos de planos (`shot_number`, `shot_type`, `description`).
  - `data["annotated_text"]`: Guión con marcadores de plano intercalados.

---

## 3. Preservación de Candados de Usuario (`user_locks`)

Tanto `treatment_structuring` como `screenplay_formatter` integran lógica de resolución de bloqueos:
1. **Diferencias Manuales (`manual_diffs`):** Si un campo está marcado como modificado manualmente por el autor, la herramienta respeta el contenido preexistente como base.
2. **Términos Fijados (`pinned_terms`):** Si el autor fijó `"Javi" -> "Javier"`, cualquier variación léxica o generación propuesta por el modelo se sustituye automáticamente por el término canónico del autor antes de emitir la respuesta.

---

## 4. Pruebas y Control de Calidad

- **Pytest:** 10 pruebas unitarias en `tests/test_tools.py` cubriendo:
  - Registro de metadatos del plugin (`FilmmakerPlugin.get_metadata()`).
  - Validación de esquemas Pydantic y rechazo de payloads inválidos.
  - Estructuración de tratamiento y reemplazo de `pinned_terms`.
  - Formateo de guión literario y asignación de diálogos.
  - Desglose y numeración de planos técnicos con sintaxis canónica.
- **Ruff:** Verificación estricta de estilo y linter en todo el árbol `src/` y `tests/`.

---

## 5. Enlace con `jg_agente`

Para habilitar las herramientas dentro del agente cognitivo sin duplicar código:
```bash
# Desde la raíz del workspace
jg link jg_plugin_filmmaker -t jg_agente/plugins
```
Esto genera un enlace simbólico canónico en `jg_agente/plugins/jg_plugin_filmmaker`, permitiendo que el cargador dinámico de plugins de `jg_agente` descubra y registre automáticamente las 3 herramientas.

---

## 6. Deudas Técnicas y Evolución Futura

1. **Dependencia de Heurísticas Regex en `breakdown.py`:**
   - La implementación actual del desglose detecta cambios de acción y diálogo mediante heurísticas léxicas y expresiones regulares.
   - *Evolución futura:* Conectar la herramienta con un agente multimodal / LLM que interprete la tensión dramática del guión para proponer planos con justificación cinematográfica y parámetros de lente/óptica (e.g., 35mm, 50mm, 85mm).
2. **Soporte de Acotaciones Complejas (Parentheticals):**
   - Actualmente las acotaciones se generan mediante patrones prefijados. Se beneficiará de un parseo sintáctico completo de la especificación Fountain AST.
3. **Internacionalización de Terminología Cinematográfica:**
   - Los tipos de plano están en español (`PG`, `PM`, `PP`, `PD`, `PA`). Conviene añadir equivalencias universales (`WS`, `MS`, `CU`, `ECU`, `FS`).
