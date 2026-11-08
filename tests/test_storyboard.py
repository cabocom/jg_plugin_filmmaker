"""Pruebas unitarias para la herramienta de generación de storyboard en jg_plugin_filmmaker."""

import httpx

from jg_plugin_filmmaker.storyboard import (
    DUMMY_PNG_BASE64,
    StoryboardGeneratorArgs,
    build_augmented_prompt,
    generate_storyboard_image,
)
from jg_plugin_filmmaker.tools import storyboard_generator_tool


def test_storyboard_generator_args_validation() -> None:
    args = StoryboardGeneratorArgs(
        prompt="Plano medio de @EDURNE sosteniendo @Atrezzo1 dentro de @CASA_ENTRADA.",
        style="enki_bilal",
        character_name="EDURNE",
        location_name="CASA ENTRADA",
        prop_images_base64=["base64_prop_1"],
    )
    assert args.style == "enki_bilal"
    assert args.character_name == "EDURNE"
    assert len(args.prop_images_base64) == 1


def test_build_augmented_prompt_with_tags() -> None:
    prompt = build_augmented_prompt(
        raw_prompt="Plano medio de @EDURNE mirando al espejo.",
        style_key="grayscale_sketch",
        character_name="EDURNE",
        has_character_image=True,
        location_name="BAÑO",
        has_location_image=True,
        prop_count=2,
    )
    assert "Plano medio de @EDURNE mirando al espejo." in prompt
    assert "@EDURNE" in prompt
    assert "@BAÑO" in prompt
    assert "@Atrezzo1" in prompt
    assert "@Atrezzo2" in prompt
    assert "charcoal and graphite drawing" in prompt


def test_generate_storyboard_image_mock_mode() -> None:
    result = generate_storyboard_image(
        prompt="Plano general de la ciudad @ALMERIA.",
        style="grayscale_sketch",
    )
    assert result.success is True
    assert result.metadata["image_base64"] == DUMMY_PNG_BASE64
    assert result.metadata["mime_type"] == "image/png"
    assert result.metadata["source"] == "deterministic_mock"


def test_generate_storyboard_image_live_mocked_http() -> None:
    fake_b64 = "fake_google_ai_generated_png_base64"

    def mock_transport(request: httpx.Request) -> httpx.Response:
        assert "models/gemini-2.5-flash-image:generateContent" in str(request.url)
        return httpx.Response(
            status_code=200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": "image/png",
                                        "data": fake_b64,
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            headers={"content-type": "application/json"},
        )

    client = httpx.Client(transport=httpx.MockTransport(mock_transport))

    # Con override de API key para saltarse el modo mock
    result = generate_storyboard_image(
        prompt="Primer plano de @MARCUS con @llaves.",
        style="kids_2d_animation",
        character_name="MARCUS",
        character_image_base64="dummy_char_b64",
        prop_images_base64=["dummy_prop_b64"],
        api_key_override="test_key_override",
        client=client,
    )

    assert result.success is True
    assert result.metadata["image_base64"] == fake_b64
    assert result.metadata["source"] == "google_ai_studio"


def test_storyboard_generator_tool_registration() -> None:
    assert storyboard_generator_tool.name == "generate_storyboard"
    assert storyboard_generator_tool.category == "filmmaker"

    res = storyboard_generator_tool.func(
        {
            "prompt": "Test prompt @EDURNE",
            "style": "grayscale_sketch",
        }
    )
    assert res.success is True
