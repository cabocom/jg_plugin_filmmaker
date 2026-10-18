"""Módulo de resolución e inferencia con LLM para jg_plugin_filmmaker.

Gestiona el desacoplamiento entre el plugin cinematográfico y el motor LLM:
- En testing/CI, con JG_AGENTE_MOCK=true o en ausencia de API keys: opera en modo mock fail-closed (consumo ZERO tokens).
- En ejecución real: interactúa con cualquier modelo compatible con LangChain (Groq, Gemini, Ollama, OpenAI)
  o funciones invocables respetando timeouts estrictos y aislamiento arquitectónico.
"""

import asyncio
import concurrent.futures
import logging
import os
from typing import Any

logger = logging.getLogger("jg_plugin_filmmaker.llm")

# Executor global para invocaciones acotadas por tiempo
_LLM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="filmmaker_llm"
)


def is_mock_mode() -> bool:
    """Indica si el entorno exige ejecución simulada determinista (fail-closed)."""
    # 1. Variable explícita de mock en el ecosistema
    env_mock = os.getenv("JG_AGENTE_MOCK", "").lower().strip()
    if env_mock in ("true", "1", "yes", "on"):
        return True
    if env_mock in ("false", "0", "no", "off"):
        return False

    # 2. Entorno de testing automático (pytest, CI)
    if "PYTEST_CURRENT_TEST" in os.environ or os.getenv("CI") == "true":
        return os.getenv("FORCE_REAL_LLM", "").lower().strip() != "true"

    # 3. Principio Fail-Closed: si no hay credenciales de ningún proveedor cognitivo, forzar mock
    has_api_key = any(
        os.getenv(k)
        for k in (
            "GROQ_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY",
            "MISTRAL_API_KEY",
        )
    )
    return not has_api_key


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

    # Intentar resolver la factoría de jg_agente de forma desacoplada
    try:
        import importlib

        llm_module = importlib.import_module("app.core.llm")
        factory = getattr(llm_module, "get_chat_model", None)
        if callable(factory):
            return factory()
    except Exception as e:
        logger.debug(
            "Factoría app.core.llm no disponible o falló (%s). Operando en modo desacoplado.",
            e,
        )

    return None


def invoke_llm_text(
    llm: Any,
    system_prompt: str,
    user_prompt: str,
    timeout: float = 30.0,
) -> str | None:
    """Invoca el LLM con timeout estricto tolerando múltiples interfaces.

    Args:
        llm: Modelo LangChain BaseChatModel, callable u objeto con .invoke()/.ainvoke().
        system_prompt: Instrucciones del sistema y directrices cinematográficas.
        user_prompt: Contenido del autor a procesar.
        timeout: Límite máximo en segundos antes de abortar la inferencia.

    Returns:
        Texto resultante generado por el LLM o None si hubo fallo/timeout.
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

        def _run_sync_invoke() -> str:
            response = llm.invoke(messages)
            if hasattr(response, "content"):
                return str(response.content).strip()
            return str(response).strip()

        # Caso 1: LangChain o cliente con .invoke() síncrono con timeout estricto
        if hasattr(llm, "invoke"):
            future = _LLM_EXECUTOR.submit(_run_sync_invoke)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.warning(
                    "Timeout (%ss) al invocar LLM síncrono. Conmutando a fallback.",
                    timeout,
                )
                return None

        # Caso 2: Cliente con .ainvoke() asíncrono
        if hasattr(llm, "ainvoke"):

            def _run_async_invoke() -> str:
                coro = llm.ainvoke(messages)
                res = asyncio.run(asyncio.wait_for(coro, timeout=timeout))
                if hasattr(res, "content"):
                    return str(res.content).strip()
                return str(res).strip()

            future = _LLM_EXECUTOR.submit(_run_async_invoke)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.warning(
                    "Timeout (%ss) al invocar LLM asíncrono. Conmutando a fallback.",
                    timeout,
                )
                return None

        # Caso 3: Callable simple
        if callable(llm):

            def _run_callable() -> str:
                try:
                    return str(llm(system_prompt=system_prompt, user_prompt=user_prompt)).strip()
                except TypeError:
                    return str(llm(user_prompt)).strip()

            future = _LLM_EXECUTOR.submit(_run_callable)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.warning(
                    "Timeout (%ss) en función LLM callable. Conmutando a fallback.",
                    timeout,
                )
                return None

    except Exception as e:
        logger.warning(
            "Fallo al invocar LLM cinematográfico (%s): %s. Conmutando a fallback.",
            type(e).__name__,
            e,
        )
        return None

    return None
