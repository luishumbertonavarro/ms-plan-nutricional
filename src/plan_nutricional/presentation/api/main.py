import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from plan_nutricional.infrastructure.config import settings
from plan_nutricional.presentation.api.exception_handlers import register_exception_handlers

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ms-plan-nutricional iniciando (env=%s)", settings.app_env)
    yield
    logger.info("ms-plan-nutricional detenido")


app = FastAPI(
    title="ms-plan-nutricional — NUR-TRICENTER",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

# ── Routers ────────────────────────────────────────────────────────────────────

from plan_nutricional.presentation.api.routers.catalogo_recetas import (  # noqa: E402
    router as catalogo_recetas_router,
)
from plan_nutricional.presentation.api.routers.planes import router as planes_router  # noqa: E402
from plan_nutricional.presentation.api.routers.plantillas import (  # noqa: E402
    router as plantillas_router,
)

app.include_router(planes_router)
app.include_router(catalogo_recetas_router)
app.include_router(plantillas_router)
