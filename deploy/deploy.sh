#!/usr/bin/env bash
# Actualiza y levanta ms-plan-nutricional en el servidor.
# Lo invoca GitHub Actions por SSH después de publicar la imagen en Docker Hub.
#
# Uso:  bash ~/ms-plan-nutricional/deploy/deploy.sh [TAG] [IMAGEN]
#   TAG     tag de la imagen (GitHub Actions pasa el SHA del commit). Por defecto: latest
#   IMAGEN  repositorio en Docker Hub. Por defecto: betonavarro/ms-plan-nutricional
set -euo pipefail

TAG="${1:-latest}"
IMAGE="${2:-betonavarro/ms-plan-nutricional}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$BASE_DIR/.env"
COMPOSE_FILE="$BASE_DIR/deploy/docker-compose.prod.yml"
NETWORK="nurtricenter_net"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: no existe $ENV_FILE. Ejecuta primero deploy/setup-server.sh" >&2
    exit 1
fi

# El puerto publicado puede cambiarse en el .env (API_PORT); el health check lo sigue.
API_PORT="$(grep -E '^API_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
HEALTH_URL="http://localhost:${API_PORT:-8000}/health"

compose() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

echo "==> Desplegando $IMAGE:$TAG"

# La red es externa (la comparte todo NUR-TRICENTER): se crea solo si todavía no existe.
if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
    echo "==> Creando la red $NETWORK"
    docker network create "$NETWORK"
fi

export TAG IMAGE
echo "==> Descargando imágenes"
compose pull
echo "==> Levantando contenedores"
compose up -d --remove-orphans

echo "==> Esperando $HEALTH_URL"
for _ in $(seq 1 30); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
        echo "==> OK: $(curl -fsS "$HEALTH_URL")"
        compose ps
        docker image prune -f >/dev/null
        exit 0
    fi
    sleep 2
done

echo "ERROR: la API no respondió en $HEALTH_URL" >&2
compose logs --tail=50 plan_nutricional_api >&2
exit 1
