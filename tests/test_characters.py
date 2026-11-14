"""Tests unitarios y de integración para el motor de inteligencia de personajes (characters.py)."""

from typing import Any

from jg_plugin_filmmaker.characters import (
    audit_character_usage,
    deterministic_extract_candidates,
    extract_characters,
    is_cinematic_stopword,
    verify_textual_grounding,
)
from jg_plugin_filmmaker.tools import (
    execute_audit_character_usage,
    execute_extract_characters,
)


class MockLLMClient:
    """Mock determinista de cliente LLM para pruebas."""

    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return self.response

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        class Msg:
            content = self.response

        return Msg()


def test_cinematic_stopwords_recognition():
    """Verifica que las acotaciones técnicas y frases verbales comunes se reconozcan como stopwords."""
    assert is_cinematic_stopword("MIRA A SU ALREDEDOR")
    assert is_cinematic_stopword("mira a su alrededor")
    assert is_cinematic_stopword("Sonido En Off")
    assert is_cinematic_stopword("SONIDO EN OFF")
    assert is_cinematic_stopword("CORTE A NEGRO")
    assert is_cinematic_stopword("PLANO DETALLE")
    assert is_cinematic_stopword("VOZ EN OFF")
    assert not is_cinematic_stopword("Edurne")
    assert not is_cinematic_stopword("Marcus")
    assert not is_cinematic_stopword("Transeúnte")


def test_textual_grounding_prevents_hallucinations():
    """Comprueba que el grounding impida la admisión de entidades no presentes en el texto."""
    text = "Edurne llega al parque y observa a un anciano comiéndose un bocadillo."

    assert verify_textual_grounding("Edurne", text)
    assert verify_textual_grounding("anciano", text)
    # Alucinación no presente en el texto
    assert not verify_textual_grounding("Terminator", text)
    assert not verify_textual_grounding("Gandalf el Gris", text)


def test_deterministic_candidate_extraction_and_filtering():
    """Verifica que el extractor determinista capture diálogos y roles pero descarte acotaciones."""
    sample_text = """
EXT. PARQUE - DÍA 1
Edurne mira a su alrededor asustada.
Sonido en off de sirenas.

EDURNE
¿Le has dado al botón?

Un viandante se acerca lentamente.
VIANDANTE:
Sí, está en verde.
"""
    candidates = deterministic_extract_candidates(sample_text)
    names = [c["name"].lower() for c in candidates]

    assert "edurne" in names
    assert "viandante" in names
    # Las acotaciones no deben figurar
    assert "mira a su alrededor" not in names
    assert "sonido en off" not in names


def test_extract_characters_with_mock_llm():
    """Verifica la extracción híbrida con LLM simulado que detecta personajes hablantes y mudos."""
    sample_text = (
        "Edurne camina por la calle. Un anciano sentado en el banco la observa en silencio."
    )
    mock_json = """{
      "characters": [
        {
          "name": "Edurne",
          "role": "Protagonista",
          "is_speaking": false,
          "bio": "Mujer joven ansiosa.",
          "evidence": "Edurne camina por la calle."
        },
        {
          "name": "Anciano",
          "role": "Personaje mudo / Silente",
          "is_speaking": false,
          "bio": "Hombre mayor en un banco.",
          "evidence": "Un anciano sentado en el banco la observa en silencio."
        },
        {
          "name": "Mira A Su Alrededor",
          "role": "Falso positivo",
          "is_speaking": false
        },
        {
          "name": "Fantasma Inexistente",
          "role": "Alucinación",
          "is_speaking": false
        }
      ]
    }"""
    mock_client = MockLLMClient(mock_json)

    res = extract_characters(sample_text, llm_client=mock_client)
    chars = res["characters"]
    names = [c["name"].lower() for c in chars]

    assert "edurne" in names
    assert "anciano" in names
    # Filtro 1: Stopword descartada
    assert "mira a su alrededor" not in names
    # Filtro 2: Alucinación descartada por falta de grounding en sample_text
    assert "fantasma inexistente" not in names


def test_audit_character_usage_disambiguates_action_phrases():
    """Verifica que la auditoría descarte 'Mira A Su Alrededor' y 'Sonido En Off' como personajes en uso."""
    scenes = [
        "EDURNE, asustada, MIRA A SU ALREDEDOR y no se ve ninguna zona iluminada por el sol.",
        "SONIDO EN OFF de agua salpicando 'CHOF'.",
        "EDURNE\n¿Le has dado al botón?",
    ]

    # 1. Stopword / locución verbal
    res_mira = audit_character_usage("Mira A Su Alrededor", scenes)
    assert res_mira["in_use"] is False
    assert res_mira["is_dramatic_entity"] is False

    # 2. Efecto de sonido técnico
    res_sonido = audit_character_usage("Sonido En Off", scenes)
    assert res_sonido["in_use"] is False
    assert res_sonido["is_dramatic_entity"] is False

    # 3. Personaje real con diálogo
    res_edurne = audit_character_usage("Edurne", scenes)
    assert res_edurne["in_use"] is True
    assert res_edurne["is_dramatic_entity"] is True


def test_tool_execution_parity():
    """Verifica la ejecución de las herramientas AgentTool canónicas a través de execute_*."""
    text = "Marcus entra en la taberna y saluda al camarero."
    tool_res = execute_extract_characters(text=text)
    assert tool_res.success is True
    assert "characters" in tool_res.metadata

    audit_res = execute_audit_character_usage(
        character_name="Mira A Su Alrededor",
        scene_texts=["Marcus mira a su alrededor."],
    )
    assert audit_res.success is True
    assert audit_res.metadata["in_use"] is False


def test_audit_character_usage_empty_name_and_mock_llm():
    """Valida casos borde de audit_character_usage: nombre vacío y mock de LLM."""
    # 1. Nombre vacío
    empty_res = audit_character_usage("   ", ["Algún texto"])
    assert empty_res["in_use"] is False
    assert "vacío" in empty_res["reason"]

    # 2. Mock LLM activo
    mock_llm = MockLLMClient(
        '{"in_use": true, "is_dramatic_entity": true, "confidence": 0.99, "reason": "Sujeto dramático confirmado por IA"}'
    )
    llm_res = audit_character_usage("Marcus", ["Marcus observa la bahía."], llm_client=mock_llm)
    assert llm_res["in_use"] is True
    assert llm_res["confidence"] == 0.99
    assert "confirmado por IA" in llm_res["reason"]


def test_extract_characters_ai_consensus_merging():
    """Valida la combinación por consenso de candidatos detectados por IA y deterministas."""
    text = "MARCUS\nDebemos zarpar hoy mismo.\n\nEL CAPITÁN asiente con firmeza."
    ai_json = (
        '{"characters": ['
        '{"name": "Marcus", "role": "Protagonista", "is_speaking": true, "bio": "Líder", "evidence": "Debemos zarpar"},'
        '{"name": "El Capitán", "role": "Secundario", "is_speaking": false, "bio": "Oficial", "evidence": "asiente"}'
        "]}"
    )
    mock_llm = MockLLMClient(ai_json)
    result = extract_characters(text, llm_client=mock_llm)
    chars = result["characters"]

    assert len(chars) >= 2
    marcus = next((c for c in chars if c["name"].lower() == "marcus"), None)
    assert marcus is not None
    assert marcus["match_type"] == "consensus_strong"
    assert marcus["confidence"] == 0.99
