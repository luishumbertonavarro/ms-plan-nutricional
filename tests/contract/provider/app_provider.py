"""App de verificación del provider `ms-plan-nutricional`.

Envuelve la app **real** (`presentation/api/main.app`, sin tocarla) y le añade dos
cosas que solo existen durante la verificación de Pact:

1. **Una transacción externa que se revierte al apagar el servidor.** Se abre una
   única conexión; las sesiones de la app se crean sobre ella con
   `join_transaction_mode="create_savepoint"`, igual que la fixture `cliente` de
   `tests/integration/conftest.py`. Al terminar, `rollback()`: la base de
   desarrollo queda intacta.

2. **La ruta `POST /_pact/provider-states`.** El verificador de Pact la llama antes
   (`setup`) y después (`teardown`) de cada interacción. En el `setup` se abre un
   SAVEPOINT y se preparan los datos del estado; en el `teardown` se revierte ese
   SAVEPOINT. Así cada interacción empieza desde cero, aunque dos de ellas usen el
   mismo `plan_id`.

La ruta de estados corre en el mismo event loop que las peticiones de la app. Por
eso ambas pueden compartir la conexión de asyncpg sin problemas de hilos.
"""
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from plan_nutricional.domain.model import (
    DuracionPlan,
    EstadoPlan,
    NecesidadNutricional,
    PlanNutricional,
    RecomendacionNutricional,
    TipoTiempoComida,
)
from plan_nutricional.infrastructure.persistence import PlanNutricionalRepositoryImpl, get_db_session
from plan_nutricional.presentation.api.main import app as app_real

RUTA_ESTADOS = "/_pact/provider-states"


class CambioDeEstado(BaseModel):
    """Cuerpo que envía el verificador de Pact a la ruta de estados."""

    state: str
    action: str = "setup"
    params: dict = {}


# ---------------------------------------------------------------------------
# Handlers de provider states — uno por cada `given(...)` de los pacts
# ---------------------------------------------------------------------------

async def _existe_un_plan_activo(session: AsyncSession, params: dict) -> None:
    """Crea un plan ACTIVO de 15 días con un día, un desayuno y una receta."""
    plan = PlanNutricional(
        id=UUID(params["plan_id"]),
        paciente_id=UUID(params["paciente_id"]),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 15),
        estado=EstadoPlan.ACTIVO,
        duracion=DuracionPlan(15),
        necesidad=NecesidadNutricional(
            calorias=Decimal("2000.00"),
            proteinas=Decimal("120.00"),
            grasas=Decimal("60.00"),
            carbohidratos=Decimal("250.00"),
        ),
        recomendacion=RecomendacionNutricional("Evitar azúcares refinados"),
        dias=[],
    )
    plan.agregar_dia(1)
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan.agregar_receta(
        1,
        TipoTiempoComida.DESAYUNO,
        nombre="Avena con frutas",
        descripcion="Desayuno alto en fibra",
        instrucciones="Cocer la avena 5 minutos",
        cantidad=Decimal("200.00"),
        unidad="gr",
    )
    await PlanNutricionalRepositoryImpl(session).guardar(plan)


async def _no_existe_el_plan(session: AsyncSession, params: dict) -> None:
    """Garantiza la precondición en vez de suponerla."""
    if await PlanNutricionalRepositoryImpl(session).obtener_por_id(UUID(params["plan_id"])):
        raise RuntimeError(f"El plan {params['plan_id']} existe y el estado exige que no exista.")


HANDLERS: dict[str, Callable[[AsyncSession, dict], Awaitable[None]]] = {
    "existe un plan activo": _existe_un_plan_activo,
    "no existe el plan": _no_existe_el_plan,
}


# ---------------------------------------------------------------------------
# Composición de la app de verificación
# ---------------------------------------------------------------------------

def crear_app_provider(url_bd: str) -> FastAPI:
    contexto: dict = {}
    savepoints: list = []

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        motor = create_async_engine(url_bd, poolclass=NullPool)
        conexion: AsyncConnection = await motor.connect()
        transaccion = await conexion.begin()
        fabrica = async_sessionmaker(
            bind=conexion,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async def _sesion_de_verificacion() -> AsyncGenerator[AsyncSession, None]:
            async with fabrica() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        contexto.update(conexion=conexion, fabrica=fabrica)
        app_real.dependency_overrides[get_db_session] = _sesion_de_verificacion
        try:
            yield
        finally:
            app_real.dependency_overrides.clear()
            await transaccion.rollback()
            await conexion.close()
            await motor.dispose()

    provider = FastAPI(lifespan=lifespan)

    @provider.post(RUTA_ESTADOS)
    async def cambiar_estado(cambio: CambioDeEstado) -> dict:
        if cambio.action == "teardown":
            if savepoints:
                await savepoints.pop().rollback()
            return {}

        handler = HANDLERS.get(cambio.state)
        if handler is None:
            raise HTTPException(status_code=400, detail=f"Provider state sin handler: '{cambio.state}'")

        savepoints.append(await contexto["conexion"].begin_nested())
        async with contexto["fabrica"]() as session:
            await handler(session, cambio.params)
            await session.commit()
        return {}

    # La ruta de estados se registra antes del mount para que tenga prioridad.
    provider.mount("/", app_real)
    return provider
