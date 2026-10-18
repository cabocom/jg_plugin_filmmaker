"""Configuración y fixtures globales para la suite de pruebas de jg_plugin_filmmaker."""

import pytest


@pytest.fixture(autouse=True)
def enforce_mock_mode_for_tests(monkeypatch):
    """Garantiza ejecución determinista con cero consumo de tokens durante los tests."""
    monkeypatch.setenv("JG_AGENTE_MOCK", "true")
