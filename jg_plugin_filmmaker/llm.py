"""Módulo de resolución e inferencia con LLM para jg_plugin_filmmaker.

Gestiona el desacoplamiento entre el plugin cinematográfico y el motor LLM:
- En testing/CI o con JG_AGENTE_MOCK=true: devuelve None o MockChatModel (consumo ZERO tokens).
- En ejecución real: interactúa con cualquier modelo compatible con LangChain (Groq, Gemini, Ollama, OpenAI)
  o funciones invocables sin romper el aislamiento arquitectónico del plugin.
"""

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger("jg_plugin_filmmaker.llm")


def is_mock_mode() -> bool:
    """Indica si el entorno exige ejecución determinista simulada (tests / CI)."""
    env_mock = os.getenv("JG_AGENTE_MOCK", "false").lower().strip()
    if env_mock in ("true", "1", "yes", "on"):
        return True
    # Si pytest está ejecutándose y no se forzó LLM real
    return "PYTEST_CURRENT_TEST" in os.environ and os.getenv("FORCE_REAL_LLM") != "true"


def get_active_llm(override_llm: Any = None) -> Any | None:
    """Resuelve el cliente LLM activo si no está en modo mock o testing.

    Args:
        override_llm: Cliente inyectado explícitamente (ej: MockChatModel en tests).

    Returns:
        Instancia de modelo de lenguaje o None si debe operar en fallback determinista.
    """
    if override_llm is not None:
        return override_llm

    if is_mock_mode():
        return None

    # Intentar resolver la factoría de jg_agente si está en el entorno de ejecución
    try:
        from app.core.llm import get_chat_model

        return get_chat_model()
    except ImportError:
        pass

    return None


def invoke_llm_text(
    llm: Any,
    system_prompt: str,
    user_prompt: str,
) -> str | None:
    """Invoca el LLM de forma síncrona/asíncrona tolerando múltiples interfaces.

    Args:
        llm: Modelo LangChain BaseChatModel, MockChatModel, callable u objeto con .invoke().
        system_prompt: Instrucciones del sistema y directrices cinematográficas.
        user_prompt: Contenido del autor a procesar.

    Returns:
        Texto resultante generado por el LLM o None si hubo fallo en la inferencia.
    """
    if llm is None:
        return None

    try:
        # Construir mensajes agnósticos (LangChain o dicts estándar)
        messages: list[Any]
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        except ImportError:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

        # Caso 1: LangChain o cliente con .invoke()
        if hasattr(llm, "invoke"):
            response = llm.invoke(messages)
            if hasattr(response, "content"):
                return str(response.content).strip()
            return str(response).strip()

        # Caso 2: Cliente con .ainvoke() asíncrono
        if hasattr(llm, "ainvoke"):
            try:
                asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, llm.ainvoke(messages))
                    response = future.result(timeout=30)
            except RuntimeError:
                response = asyncio.run(llm.ainvoke(messages))

            if hasattr(response, "content"):
                return str(response.content).strip()
            return str(response).strip()

        # Caso 3: Callable simple
        if callable(llm):
            try:
                return str(llm(system_prompt=system_prompt, user_prompt=user_prompt)).strip()
            except TypeError:
                return str(llm(user_prompt)).strip()

    except Exception as e:
        logger.warning("Fallo al invocar LLM cinematográfico: %s. Conmutando a fallback.", e)
        return None

    return None
