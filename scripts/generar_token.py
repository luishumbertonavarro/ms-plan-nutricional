"""Genera un JWT válido para ms-plan-nutricional sin pasar por el api-gateway.

Firma con el mismo algoritmo, secreto, issuer y audience que valida
`presentation/api/security.py` (los toma de `settings`, así que respeta JWT_SECRET
y el resto de variables de entorno) y con los mismos claims que emite el gateway
(`EmisorDeTokens.cs`): sub, name, jti, rol, iss, aud, exp.

Uso:
    uv run python scripts/generar_token.py                 # rol admin, 60 min
    uv run python scripts/generar_token.py --rol paciente --minutos 15
"""
import argparse
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from plan_nutricional.infrastructure.config import settings

ROLES = ("admin", "nutricionista", "paciente")


def generar_token(usuario: str, rol: str, minutos: int) -> str:
    ahora = datetime.now(UTC)
    payload = {
        "sub": usuario,
        "name": usuario,
        "jti": str(uuid.uuid4()),
        "rol": rol,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=minutos),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rol", choices=ROLES, default="admin")
    parser.add_argument("--usuario", default="demo")
    parser.add_argument("--minutos", type=int, default=60)
    args = parser.parse_args()
    print(generar_token(args.usuario, args.rol, args.minutos))


if __name__ == "__main__":
    main()
