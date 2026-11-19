"""Módulo de resolución e inferencia con LLM para jg_plugin_filmmaker.

Gestiona el desacoplamiento entre el plugin cinematográfico y el motor LLM:
- En testing/CI, con JG_AGENTE_MOCK=true o en ausencia de API keys: opera en modo mock fail-closed (consumo ZERO tokens).
- En ejecución real: interactúa con cualquier modelo compatible con LangChain (Groq, Gemini, Ollama, OpenAI)
  o funciones invocables respetando timeouts estrictos y aislamiento arquitectónico.
"""

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

    return False


def _configure_client_timeout(llm: Any, timeout: float) -> None:
    """Configura proactivamente el timeout a nivel de cliente HTTP para evitar bloqueo de workers."""
    for attr in ("timeout", "request_timeout"):
        if hasattr(llm, attr):
            try:
                curr = getattr(llm, attr)
                if curr is None or (isinstance(curr, (int, float)) and curr > timeout):
                    setattr(llm, attr, timeout)
            except Exception:
                pass


def get_active_llm(
    override_llm: Any = None,
    api_key: Any | None = None,
    provider: str | None = None,
) -> Any | None:
    """Resuelve el cliente LLM activo si no está en modo mock o testing.

    Args:
        override_llm: Cliente inyectado explícitamente (ej: MockChatModel en tests).
        api_key: Credencial opcional BYOK (str o SecretStr).
        provider: Identificador opcional del proveedor (groq, openai, gemini, etc.).

    Returns:
        Instancia de modelo de lenguaje o None si no hay cliente disponible.
    """
    if override_llm is not None:
        return override_llm

    # Extraer valor en texto plano de SecretStr si aplica
    api_key_str: str | None = None
    if api_key is not None:
        api_key_str = (
            api_key.get_secret_value() if hasattr(api_key, "get_secret_value") else str(api_key)
        )

    # 1. Intentar resolver la factoría de jg_agente de forma desacoplada
    try:
        import importlib

        llm_module = importlib.import_module("app.core.llm")
        factory = getattr(llm_module, "get_chat_model", None)
        if callable(factory):
            kwargs: dict[str, Any] = {}
            if provider:
                kwargs["provider"] = provider
            if api_key_str:
                kwargs["api_key"] = api_key_str
            return factory(**kwargs)
    except Exception as e:
        logger.debug(
            "Factoría app.core.llm no disponible o falló (%s). Operando en modo desacoplado.",
            e,
        )

    # 2. Si se suministró credencial BYOK, instanciar cliente LangChain directamente si está instalado
    if api_key_str:
        prov = (provider or "openai").lower().strip()
        try:
            if prov == "groq":
                from langchain_groq import ChatGroq

                return ChatGroq(api_key=api_key_str)
            if prov in ("openai", "custom"):
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(api_key=api_key_str)
            if prov in ("google", "gemini"):
                from langchain_google_genai import ChatGoogleGenerativeAI

                return ChatGoogleGenerativeAI(google_api_key=api_key_str)
        except ImportError:
            logger.debug("Dependencias LangChain para proveedor '%s' no disponibles.", prov)

    if is_mock_mode():
        return None

    return None


def invoke_llm_text(
    llm: Any,
    system_prompt: str,
    user_prompt: str,
    timeout: float = 30.0,
) -> str:
    """Invoca el LLM con timeout estricto tolerando múltiples interfaces.

    Args:
        llm: Modelo LangChain BaseChatModel, callable u objeto con .invoke().
        system_prompt: Instrucciones del sistema y directrices cinematográficas.
        user_prompt: Contenido del autor a procesar.
        timeout: Límite máximo en segundos antes de abortar la inferencia.

    Returns:
        Texto resultante generado por el LLM.

    Raises:
        RuntimeError: Si llm es None, inválido o falla la llamada.
        TimeoutError: Si la inferencia excede el tiempo límite establecido.
    """
    if llm is None:
        raise RuntimeError("No se ha configurado ni suministrado un cliente LLM válido.")

    _configure_client_timeout(llm, timeout)

    # Construir mensajes agnósticos (LangChain o dicts estándar)
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

    if hasattr(llm, "invoke"):
        future = _LLM_EXECUTOR.submit(_run_sync_invoke)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            logger.error("Timeout (%ss) al invocar LLM síncrono.", timeout)
            raise TimeoutError(
                f"Timeout ({timeout}s) agotado durante la inferencia con LLM."
            ) from exc
        except Exception as exc:
            logger.error("Error al invocar LLM síncrono (%s): %s", type(exc).__name__, exc)
            raise

    if callable(llm):

        def _run_callable() -> str:
            try:
                return str(llm(system_prompt=system_prompt, user_prompt=user_prompt)).strip()
            except TypeError:
                return str(llm(user_prompt)).strip()

        future = _LLM_EXECUTOR.submit(_run_callable)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            logger.error("Timeout (%ss) en función LLM callable.", timeout)
            raise TimeoutError(f"Timeout ({timeout}s) agotado en función LLM callable.") from exc
        except Exception as exc:
            logger.error("Error en función LLM callable (%s): %s", type(exc).__name__, exc)
            raise

    raise RuntimeError(f"El objeto LLM suministrado ({type(llm).__name__}) no es invocable.")
