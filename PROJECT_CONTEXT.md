# Contexto de Proyecto: jg_plugin_filmmaker

**Versión:** 2.4.0  
**Fecha:** 18 de octubre de 2026  
**Componente:** Plugin Satélite Cognitivo de Asistencia Cinematográfica para `jg_agente`  
**Stack Tecnológico:** Python 3.12 / 3.14, Pydantic v2, `jg-agente-sdk` (^1.0.0), Pytest, Ruff  
**Estado:** Totalmente implementado. Sincronización canónica con Biblia dramática de `jg_filmmaker` (ISSUE-012) y sanitización de `pinned_terms` (ISSUE-016: sustitución segura sin backreferences con lambda en `re.sub`, lookarounds adaptativos para símbolos como `C++` o `#1` y límites de seguridad). 18 tests unitarios pasando al 100% en CI/CD.

---

## 1. Visión y Propósito en el Ecosistema

`jg_plugin_filmmaker` es un componente satélite desacoplado que dota al agente central `jg_agente` de capacidades especializadas para el análisis dramático, normalización de guiones y desglose de producción cinematográfica.

Actúa como backend de procesamiento cognitivo para la aplicación web `jg_filmmaker`:
- **Aislamiento Total:** El plugin es un repositorio Python independiente. Tiene prohibido importar módulos internos de `jg_agente.app.*`.
- **Contratos Canónicos:** Implementa estrictamente la interfaz `BasePlugin` y `AgentTool` definidas en `jg_sdk.contracts` (`jg-agente-sdk`).
- **Nivel de Riesgo:** Todas las herramientas operan bajo `RiskLevel.LOW`, dado que son transformaciones puras de texto sin efectos secundarios destructivos en el sistema.
- **Inferencia Semántica Dual:** Soporta inferencia cognitiva real conectando a la factoría de LLMs (`llm_client`) y degradación determinista offline (`is_mock_mode()`) cuando se ejecutan pruebas o no se suministra cliente LLM.

---

## 2. Catálogo de Herramientas y Esquemas Pydantic v2

### 2.1. `treatment_structuring`
- **Módulo:** `jg_plugin_filmmaker/structuring.py`
- **Propósito:** Normaliza texto libre, notas o borradores en prosa de tratamiento cinematográfico en presente continuo mediante `STRUCTURING_SYSTEM_PROMPT`.
- **Esquema de Entrada (`TreatmentStructuringArgs`):**
  - `raw_text` (str): Texto bruto inicial redactado por el cineasta.
  - `characters_context` (list[dict[str, Any]], opcional): Contexto estructurado de personajes de la Biblia (`name`, `bio`, `psychology`, `costume_notes`, `role`).
  - `location_context` (dict[str, Any], opcional): Metadatos del escenario (`name`, `type`, `art_department_notes`, `lighting_notes`, `time_of_day`).
  - `user_locks` (dict[str, Any], opcional): Estructura de bloqueos y `pinned_terms` del autor.
- **Salida (`ToolResult`):** Texto de tratamiento estructurado respetando la inmutabilidad de los términos bloqueados.

### 2.2. `screenplay_formatter`
- **Módulo:** `jg_plugin_filmmaker/formatting.py`
- **Propósito:** Transforma el tratamiento en prosa a formato literario estándar Fountain (Courier 12pt) mediante `SCREENPLAY_SYSTEM_PROMPT`. Resuelve el estilo indirecto a diálogos directos e infiere personajes intervinientes.
- **Esquema de Entrada (`ScreenplayInput`):**
  - `structured_text` (str): Tratamiento dramático previo.
  - `characters_context` (list[str], opcional): Personajes reconocidos para sangría y mayúsculas de diálogo.
  - `location_context` (str, opcional): Localización para la construcción del encabezado de escena.
  - `user_locks` (dict[str, Any], opcional): Términos canónicos fijados y campos congelados.
- **Salida (`ToolResult`):** Guión formateado con sluglines estándar (`INT. LOCALIZACION - DIA`), bloques de acción narrativa y parlamentos tipificados (`PERSONAJE\n(acotación)\nDiálogo`).

### 2.3. `shot_breakdown_detector`
- **Módulo:** `jg_plugin_filmmaker/breakdown.py`
- **Propósito:** Analiza el guión literario y propone un desglose técnico de planos de cámara para rodaje evaluando tensión dramática con `BREAKDOWN_SYSTEM_PROMPT`.
- **Esquema de Entrada (`ShotBreakdownDetectorArgs`):**
  - `screenplay_text` (str): Contenido en formato guión literario.
- **Sintaxis Canónica:** Emplea estrictamente delimitadores canónicos:
  `--- shot N (tipo) ---` (ejemplos: `--- shot 1 (PG) ---`, `--- shot 2 (PM) ---`, `--- shot 3 (PP) ---`, `--- shot 4 (PD) ---`).
- **Salida (`ToolResult`):**
  - `data["shots"]`: Lista de diccionarios con metadatos de planos (`shot_number`, `shot_type`, `description`).
  - `data["annotated_text"]`: Guión con marcadores de plano intercalados.

### 2.4. `plot_hole_detector`
- **Módulo:** `jg_plugin_filmmaker/plot_holes.py`
- **Propósito:** Audita la secuencia narrativa y cronológica de bloques del proyecto, cotejando la consistencia dramática, la continuidad espacial/temporal y la presencia de personajes de la Biblia mediante `PLOT_HOLE_SYSTEM_PROMPT` o motor determinista.
- **Esquema de Entrada (`PlotHoleDetectorArgs`):**
  - `blocks` (list[dict[str, Any]]): Bloques narrativos con identificador y texto.
  - `characters` (list[dict[str, Any]], opcional): Contexto de personajes de la Biblia.
  - `locations` (list[dict[str, Any]], opcional): Contexto de localizaciones.
- **Salida (`ToolResult`):**
  - `metadata["detected_holes"]`: Lista de dicts `{"block_id": str, "reason": str}`.
  - `metadata["total_holes"]`: Entero con la cantidad de inconsistencias detectadas.

---

## 3. Preservación de Candados de Usuario (`user_locks`)

Tanto `treatment_structuring` como `screenplay_formatter` integran lógica de resolución de bloqueos:
1. **Diferencias Manuales (`manual_diffs`):** Si un campo está marcado como modificado manualmente por el autor, la herramienta respeta el contenido preexistente como base.
2. **Términos Fijados (`pinned_terms`):** Si el autor fijó `"Javi" -> "Javier"`, cualquier variación léxica o generación propuesta por el modelo se sustituye automáticamente por el término canónico del autor antes de emitir la respuesta.

---

## 4. Pruebas y Control de Calidad

- **Pytest:** 15 pruebas unitarias en `tests/test_filmmaker_tools.py` y `tests/test_plugin.py` cubriendo:
  - Registro de metadatos del plugin (`FilmmakerPlugin.get_metadata()`) y catálogo de 4 herramientas.
  - Validación de esquemas Pydantic y rechazo de payloads inválidos.
  - Inferencia con LLM real/mock inyectado y fallback determinista offline.
  - Estructuración de tratamiento y reemplazo de `pinned_terms`.
  - Formateo de guión literario y resolución de estilo indirecto a parlamentos.
  - Desglose y numeración de planos técnicos con sintaxis canónica `--- shot N (tipo) ---`.
  - Detección de inconsistencias y agujeros dramáticos con `plot_hole_detector`.
- **Ruff:** Verificación estricta de estilo y linter en todo el árbol `jg_plugin_filmmaker/` y `tests/`.

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

1. **Parámetros de Óptica e Iluminación en Breakdown:**
   - La inferencia actual propone tamaño de plano y descripción dramática.
   - *Evolución futura:* Proponer distancia focal recomendada (e.g. 35mm, 50mm, 85mm) y tipo de iluminación técnica.
2. **Internacionalización de Terminología Cinematográfica:**
   - Los tipos de plano están en español (`PG`, `PM`, `PP`, `PD`, `PA`). Conviene admitir equivalencias universales (`WS`, `MS`, `CU`, `ECU`, `FS`).

---

## 7. Despliegue en Producción (VM OVH)

- **Instalación:** Desplegado en `/cabocom/web/apps/films.javiergalvez.com/plugins/jg_plugin_filmmaker` y montado como volumen en modo solo lectura (`/app/plugins/jg_plugin_filmmaker:ro`) en el contenedor `jg_agente_filmmaker`.
- **Descubrimiento Dinámico:** Cargado automáticamente mediante `ENABLED_PLUGINS=filmmaker,jg_plugin_filmmaker` por el `PluginManager` de `jg_agente`, verificando 3 tools en boot sin necesidad de Dashboard (`DASHBOARD_URL=""`, `ENABLE_HEARTBEAT=false`).

---

## 8. Seguridad y Robustez de Entrada (Auditoría 2026-10-18)

- **Sanitización de Backreferences (ISSUE-016):** Reemplazo literal de `pinned_terms` previniendo inyección de subpatrones regex o escapes octales.
- **Mitigación ReDoS y Límites de Payload (ISSUE-035):**
  - Esquemas Pydantic acotan `raw_text`, `structured_text` y `screenplay_text` a 50.000 caracteres, y listas de contexto a límites estrictos (máx 100-200 elementos).
  - Fast-path en `formatting.py` mediante búsqueda de límites de palabra `\b<verbos>\b` y cuantificadores finitos acotados (`[^.?!]{0,250}?`, `.{1,5000}`) impidiendo backtracking catastrófico en habla indirecta.
- **Submodelos de Dominio y Tipado Estricto Pydantic v2 (ISSUE-036):**
  - Tipado de contratos con `CharacterContext`, `LocationContext`, `ManualDiffItem`, `UserLocksModel` y `ScriptBlockItem`.
  - Configuración `extra="ignore"` para asimilar metadatos de Eloquent/Laravel sin divergir del esquema.
  - Protocolo `LLMClientProtocol` para desacoplar y tipar clientes cognitivos.
  - Logging estructurado (`logger.exception`) y ofuscación de excepciones internas hacia el cliente.
- **Protección contra IndexError en Diálogos Residuales (ISSUE-038):**
  - Validación de núcleo de diálogo en `refine_dialogue_to_direct_speech` con fallback canónico a elipsis (`¿...?`, `¡...!`, `...`) ante oraciones vacías o compuestas exclusivamente por signos ortográficos.




