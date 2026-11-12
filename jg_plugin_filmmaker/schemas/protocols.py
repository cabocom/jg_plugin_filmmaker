"""Protocolos formales para el ecosistema jg_plugin_filmmaker."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Protocolo formal para clientes de modelos de lenguaje."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Genera una respuesta textual a partir de un prompt."""
        ...
