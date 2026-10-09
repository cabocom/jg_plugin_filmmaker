# 03. Preservación de Candados y Modificaciones (`jg_plugin_filmmaker`)

[← 02. Especificación de Herramientas](02_tools_specification.md) | [04. Calidad y Testing →](04_testing_quality_cicd.md)

---

## 1. Algoritmo de Preservación en Python

En las herramientas satélite `treatment_structuring` y `screenplay_formatter`, la lógica cognitiva incorpora un resolvedor determinista de bloqueos para asegurar que las decisiones manuales del autor sean intocables.

---

## 2. Tratamiento de `pinned_terms`

Si el payload incluye un diccionario de términos fijados:
```json
{
  "pinned_terms": {
    "Javi": "Javier",
    "Bar Pepe": "BAR CENTRAL"
  }
}
```

La herramienta aplica la sustitución forzada sobre el texto procesado mediante reemplazo insensible a mayúsculas/minúsculas (`re.sub` con flag `re.IGNORECASE`), garantizando que la salida respete los nombres canónicos de la Biblia de Proyecto.

---

## 3. Respeto de Campos Congelados (`locked_fields`)

Si el bloque posee su campo correspondiente dentro de `locked_fields`:
- La herramienta evalúa el contenido preexistente.
- Si el campo está bloqueado, se devuelve el texto original sin aplicar mutaciones no autorizadas, preservando las correcciones manuales del cineasta.
