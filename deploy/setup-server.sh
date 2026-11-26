#!/usr/bin/env bash
# Preparación única de un servidor Ubuntu (AWS EC2) para ms-plan-nutricional.
# Se ejecuta UNA vez, a mano, conectado por SSH:
#
#   scp -i clave.pem deploy/setup-server.sh ubuntu@<IP>:~
#   ssh -i clave.pem ubuntu@<IP> 'bash setup-server.sh'
#
# Instala Docker + Compose, agrega swap, crea ~/ms-plan-nutricional/.env y la red nurtricenter_net.
# Es idempotente: volver a ejecutarlo no rompe nada ni sobrescribe el .env.
#
# JWT_SECRET debe ser el mismo secreto que usa el api-gateway. Para usar otro:
#   JWT_SECRET='otro-secreto' bash setup-server.sh
set -euo pipefail

APP_DIR="$HOME/ms-plan-nutricional"
ENV_FILE="$APP_DIR/.env"
SHARED_JWT_SECRET="nurtricenter-secreto-compartido-2026"

echo "==> 1/4 Docker"
if ! command -v docker >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo "    ya instalado: $(docker --version)"
fi
sudo systemctl enable --now docker
# Permite usar docker sin sudo (también desde el SSH de GitHub Actions).
sudo usermod -aG docker "$USER"

echo "==> 2/4 Swap de 1 GB (t3.micro tiene 1 GB de RAM: Postgres + API lo agradecen)"
if ! swapon --show | grep -q '/swapfile'; then
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
else
    echo "    ya existe"
fi

echo "==> 3/4 Configuración en $ENV_FILE"
mkdir -p "$APP_DIR/deploy"
if [ ! -f "$ENV_FILE" ]; then
    umask 077
    cat > "$ENV_FILE" <<EOF
# Variables del despliegue de ms-plan-nutricional (las lee deploy/docker-compose.prod.yml).
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Autenticación: el token lo emite el api-gateway (o scripts/generar_token.py) con este secreto.
AUTH_HABILITADA=true
JWT_SECRET=${JWT_SECRET:-$SHARED_JWT_SECRET}

# Vacíos = standalone. Con valor = integrado con la infraestructura del grupo en nurtricenter_net.
CONSUL_URL=
RABBITMQ_URL=

API_PORT=8000
EOF
    echo "    creado (permisos 600)"
else
    echo "    ya existe, no se modifica"
fi

echo "==> 4/4 Red nurtricenter_net"
sudo docker network inspect nurtricenter_net >/dev/null 2>&1 || sudo docker network create nurtricenter_net

echo
echo "Listo. Cierra la sesión SSH y vuelve a entrar para que aplique el grupo docker."
echo "Comprueba con:  docker ps"
