#!/bin/sh
set -e

# ==============================================================================
# Entrypoint de arranque determinista para jg_agente (jg_plugin_filmmaker)
# ==============================================================================
# ¿Qué hace este script?
# 1. Ejecución de Migraciones Troncales (Alembic):
#    Aplica 'alembic upgrade head' contra la base de datos PostgreSQL del agente.
#    Esto crea y sincroniza las tablas troncales requeridas por el Core:
#      - core_executions: Persistencia de estado del grafo y ejecuciones HITL.
#      - core_audit_records: Registro inmutable de auditoría y decisiones humanas.
#    Evita errores 'relation core_executions does not exist' al recibir peticiones.
#
# 2. Inicialización del Servidor Web (Uvicorn):
#    Lanza FastAPI con el número de workers configurados escuchando en AGENT_PORT.
# ==============================================================================

echo "🔄 [jg_agente] Aplicando migraciones de base de datos troncales (alembic upgrade head)..."
alembic upgrade head

echo "🚀 [jg_agente] Migraciones aplicadas con éxito. Iniciando Execution Plane en puerto ${AGENT_PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${AGENT_PORT:-8000}" --workers "${UVICORN_WORKERS:-2}"
