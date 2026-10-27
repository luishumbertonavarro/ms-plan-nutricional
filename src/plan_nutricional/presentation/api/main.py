import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from plan_nutricional.infrastructure.config import settings
from plan_nutricional.presentation.api.exception_handlers import register_exception_handlers
from plan_nutricional.presentation.api.security import proteger

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ms-plan-nutricional iniciando (env=%s)", settings.app_env)
    # Import diferido: la app (y sus tests) se construyen sin tocar broker ni Consul.
    from plan_nutricional.infrastructure.persistence.database import AsyncSessionFactory

    procesos = []
    registro = None
    if settings.rabbitmq_url:
        from plan_nutricional.infrastructure.messaging.consumidor import ConsumidorEventos
        from plan_nutricional.infrastructure.messaging.manejadores import MANEJADORES
        from plan_nutricional.infrastructure.messaging.outbox_relay import OutboxRelay

        procesos = [
            OutboxRelay(
                AsyncSessionFactory,
                settings.rabbitmq_url,
                settings.rabbitmq_exchange,
                settings.outbox_intervalo_segundos,
            ),
            ConsumidorEventos(
                AsyncSessionFactory,
                settings.rabbitmq_url,
                settings.rabbitmq_exchange,
                settings.rabbitmq_cola,
                MANEJADORES,
            ),
        ]
    if settings.consul_url:
        from plan_nutricional.infrastructure.discovery.consul import RegistroConsul

        registro = RegistroConsul(
            settings.consul_url, settings.servicio_nombre, settings.servicio_puerto
        )
        registro.iniciar()
    for proceso in procesos:
        proceso.iniciar()
    yield
    for proceso in procesos:
        await proceso.detener()
    if registro is not None:
        await registro.desregistrar()
    logger.info("ms-plan-nutricional detenido")


app = FastAPI(
    title="ms-plan-nutricional — NUR-TRICENTER",
    version="0.2.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

# ── Routers ────────────────────────────────────────────────────────────────────

from plan_nutricional.presentation.api.routers.catalogo_recetas import (  # noqa: E402
    router as catalogo_recetas_router,
)
from plan_nutricional.presentation.api.routers.health import router as health_router  # noqa: E402
from plan_nutricional.presentation.api.routers.planes import router as planes_router  # noqa: E402
from plan_nutricional.presentation.api.routers.plantillas import (  # noqa: E402
    router as plantillas_router,
)

# Roles (claim `rol` del JWT): el nutricionista gestiona; el paciente solo consulta sus planes.
_STAFF = ("admin", "nutricionista")

app.include_router(health_router)
app.include_router(
    planes_router,
    dependencies=[Depends(proteger(lectura=(*_STAFF, "paciente"), escritura=_STAFF))],
)
app.include_router(
    catalogo_recetas_router, dependencies=[Depends(proteger(lectura=_STAFF, escritura=_STAFF))]
)
app.include_router(
    plantillas_router, dependencies=[Depends(proteger(lectura=_STAFF, escritura=_STAFF))]
)
