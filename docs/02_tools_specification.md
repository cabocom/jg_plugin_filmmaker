# 02. Especificación de Herramientas Canónicas (`jg_plugin_filmmaker`)

[← 01. Arquitectura del Plugin](01_plugin_architecture.md) | [03. Preservación de Candados →](03_user_locks_resolution.md)

---

## 1. Catálogo de Herramientas Cognitivas

El plugin implementa tres herramientas canónicas validadas con **Pydantic v2**:

---

## 2. Herramienta 1: `treatment_structuring`

- **Módulo:** `src/jg_plugin_filmmaker/tools/structuring.py`
- **Descripción:** Convierte el texto bruto e informal del autor a prosa dramática estructurada en presente de indicativo.
- **Riesgo:** `RiskLevel.LOW`
- **Esquema de Entrada (`TreatmentInput`):**
  ```python
  class TreatmentInput(BaseModel):
      raw_text: str = Field(..., description="Texto bruto del autor")
      characters_context: list[str] = Field(
          default_factory=list, description="Lista de nombres de personajes"
      )
      location_context: str | None = Field(default=None, description="Localización de la escena")
      user_locks: dict[str, Any] = Field(
          default_factory=dict, description="Candados y términos fijados"
      )
  ```
- **Salida:** `ToolResult(success=True, data={"structured_text": ...})`.

---

## 3. Herramienta 2: `screenplay_formatter`

- **Módulo:** `src/jg_plugin_filmmaker/tools/formatting.py`
- **Descripción:** Formatea el tratamiento a guión cinematográfico estándar Fountain / Courier 12pt.
- **Riesgo:** `RiskLevel.LOW`
- **Esquema de Entrada (`ScreenplayInput`):**
  ```python
  class ScreenplayInput(BaseModel):
      structured_text: str = Field(..., description="Texto de tratamiento")
      characters_context: list[str] = Field(
          default_factory=list, description="Personajes para formateo de diálogos"
      )
      location_context: str | None = Field(default=None, description="Localización para el slugline")
      user_locks: dict[str, Any] = Field(
          default_factory=dict, description="Candados y términos fijados"
      )
  ```
- **Salida:** `ToolResult(success=True, data={"screenplay_text": ...})`.

---

## 4. Herramienta 3: `shot_breakdown_detector`

- **Módulo:** `src/jg_plugin_filmmaker/tools/breakdown.py`
- **Descripción:** Analiza el guión literario y propone un desglose técnico de planos de cámara para rodaje.
- **Riesgo:** `RiskLevel.LOW`
- **Esquema de Entrada (`BreakdownInput`):**
  ```python
  class BreakdownInput(BaseModel):
      screenplay_text: str = Field(..., description="Texto en formato guión literario")
  ```
- **Sintaxis Canónica:** Emplea estrictamente delimitadores:
  ```text
  --- shot N (tipo) ---
  ```
  Donde `tipo` corresponde a tipos cinematográficos estándar (`PG`, `PM`, `PP`, `PD`, `PA`).
- **Salida:**
  ```python
  ToolResult(
      success=True,
      data={
          "shots": [
              {"shot_number": 1, "shot_type": "PG", "description": "..."},
              {"shot_number": 2, "shot_type": "PM", "description": "..."},
          ],
          "annotated_text": "...",
      },
  )
  ```
