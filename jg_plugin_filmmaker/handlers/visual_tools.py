"""Handlers ejecutores para herramientas visuales y de storyboard."""

import logging
from typing import Any

from jg_sdk.contracts import ToolResult

from jg_plugin_filmmaker.breakdown import breakdown_screenplay_to_shots
from jg_plugin_filmmaker.schemas.protocols import LLMClientProtocol
from jg_plugin_filmmaker.storyboard import (
    StoryboardGeneratorArgs,
    generate_storyboard_image,
)

logger = logging.getLogger(__name__)


def execute_shot_breakdown_detector(
    screenplay_text: str,
    llm_client: LLMClientProtocol | Any = None,
) -> ToolResult:
    """Ejecuta la propuesta de planos técnicos con el delimitador canónico '--- shot N (tipo) ---'."""
    try:
        annotated_text, shots_list = breakdown_screenplay_to_shots(
            screenplay_text=screenplay_text,
            llm_client=llm_client,
        )

        return ToolResult(
            success=True,
            output=annotated_text,
            metadata={
                "stage": "shots",
                "shots": shots_list,
                "total_shots": len(shots_list),
            },
        )
    except Exception as e:
        logger.exception("Fallo al desglosar planos técnicos: %s", e)
        return ToolResult(
            success=False,
            output="",
            error=f"Fallo al detectar planos: {type(e).__name__} en desglose técnico.",
            metadata={"error_code": "SHOT_BREAKDOWN_ERROR"},
        )


def execute_generate_storyboard(
    args: StoryboardGeneratorArgs | dict[str, Any], **kwargs: Any
) -> ToolResult:
    """Ejecuta la generación de viñeta de storyboard con validación Pydantic v2."""
    validated_args = (
        StoryboardGeneratorArgs.model_validate(args) if isinstance(args, dict) else args
    )

    return generate_storyboard_image(
        prompt=validated_args.prompt,
        style=validated_args.style,
        character_name=validated_args.character_name,
        character_image_base64=validated_args.character_image_base64,
        location_name=validated_args.location_name,
        location_image_base64=validated_args.location_image_base64,
        prop_images_base64=validated_args.prop_images_base64,
        aspect_ratio=validated_args.aspect_ratio,
    )
