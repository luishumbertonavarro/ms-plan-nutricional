from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from plan_nutricional.application.commands import (
    AgregarPlantillaDiaCommand,
    AgregarPlantillaRecetaCommand,
    AgregarPlantillaTiempoComidaCommand,
    CrearPlantillaCommand,
    EliminarPlantillaDiaCommand,
    EliminarPlantillaRecetaCommand,
    EliminarPlantillaTiempoComidaCommand,
)
from plan_nutricional.application.queries import ListarPlantillasQuery, ObtenerPlantillaPorIdQuery
from plan_nutricional.application.use_cases import (
    AgregarPlantillaDiaUseCase,
    AgregarPlantillaRecetaUseCase,
    AgregarPlantillaTiempoComidaUseCase,
    CrearPlantillaUseCase,
    EliminarPlantillaDiaUseCase,
    EliminarPlantillaRecetaUseCase,
    EliminarPlantillaTiempoComidaUseCase,
    ListarPlantillasHandler,
    ObtenerPlantillaPorIdHandler,
)
from plan_nutricional.domain.model import TipoTiempoComida
from plan_nutricional.domain.repositories import PlantillaPlanRepository, RecetaCatalogoRepository
from plan_nutricional.infrastructure.persistence import (
    PlantillaPlanRepositoryImpl,
    RecetaCatalogoRepositoryImpl,
    get_db_session,
)
from plan_nutricional.presentation.api.schemas import (
    AgregarPlantillaDiaRequest,
    AgregarPlantillaRecetaRequest,
    AgregarPlantillaTiempoComidaRequest,
    CrearPlantillaRequest,
    PlantillaResponse,
    plantilla_to_response,
)

router = APIRouter(prefix="/plantillas", tags=["plantillas"])


async def _get_repo(session: AsyncSession = Depends(get_db_session)) -> PlantillaPlanRepository:
    return PlantillaPlanRepositoryImpl(session)


async def _get_catalogo_repo(
    session: AsyncSession = Depends(get_db_session),
) -> RecetaCatalogoRepository:
    return RecetaCatalogoRepositoryImpl(session)


# ── Plantillas ─────────────────────────────────────────────────────────────────

@router.post("", response_model=PlantillaResponse, status_code=201)
async def crear_plantilla(
    body: CrearPlantillaRequest,
    repo: PlantillaPlanRepository = Depends(_get_repo),
):
    uc = CrearPlantillaUseCase(repo)
    plantilla = await uc.ejecutar(
        CrearPlantillaCommand(
            nombre=body.nombre,
            descripcion=body.descripcion,
            duracion_dias=body.duracion_dias,
        )
    )
    return plantilla_to_response(plantilla)


@router.get("", response_model=list[PlantillaResponse])
async def listar_plantillas(repo: PlantillaPlanRepository = Depends(_get_repo)):
    handler = ListarPlantillasHandler(repo)
    plantillas = await handler.ejecutar(ListarPlantillasQuery())
    return [plantilla_to_response(p) for p in plantillas]


@router.get("/{plantilla_id}", response_model=PlantillaResponse)
async def obtener_plantilla(
    plantilla_id: UUID,
    repo: PlantillaPlanRepository = Depends(_get_repo),
):
    handler = ObtenerPlantillaPorIdHandler(repo)
    plantilla = await handler.ejecutar(ObtenerPlantillaPorIdQuery(plantilla_id=plantilla_id))
    if plantilla is None:
        raise HTTPException(status_code=404, detail="Plantilla de plan no encontrada.")
    return plantilla_to_response(plantilla)


# ── Días ───────────────────────────────────────────────────────────────────────

@router.post("/{plantilla_id}/dias", status_code=204)
async def agregar_plantilla_dia(
    plantilla_id: UUID,
    body: AgregarPlantillaDiaRequest,
    repo: PlantillaPlanRepository = Depends(_get_repo),
):
    uc = AgregarPlantillaDiaUseCase(repo)
    await uc.ejecutar(
        AgregarPlantillaDiaCommand(plantilla_id=plantilla_id, numero_dia=body.numero_dia)
    )


@router.delete("/{plantilla_id}/dias/{numero_dia}", status_code=204)
async def eliminar_plantilla_dia(
    plantilla_id: UUID,
    numero_dia: int,
    repo: PlantillaPlanRepository = Depends(_get_repo),
):
    uc = EliminarPlantillaDiaUseCase(repo)
    await uc.ejecutar(
        EliminarPlantillaDiaCommand(plantilla_id=plantilla_id, numero_dia=numero_dia)
    )


# ── Tiempos de comida ──────────────────────────────────────────────────────────

@router.post("/{plantilla_id}/dias/{numero_dia}/tiempos", status_code=204)
async def agregar_plantilla_tiempo_comida(
    plantilla_id: UUID,
    numero_dia: int,
    body: AgregarPlantillaTiempoComidaRequest,
    repo: PlantillaPlanRepository = Depends(_get_repo),
):
    uc = AgregarPlantillaTiempoComidaUseCase(repo)
    await uc.ejecutar(
        AgregarPlantillaTiempoComidaCommand(
            plantilla_id=plantilla_id, numero_dia=numero_dia, tipo=body.tipo
        )
    )


@router.delete("/{plantilla_id}/dias/{numero_dia}/tiempos/{tipo}", status_code=204)
async def eliminar_plantilla_tiempo_comida(
    plantilla_id: UUID,
    numero_dia: int,
    tipo: TipoTiempoComida,
    repo: PlantillaPlanRepository = Depends(_get_repo),
):
    uc = EliminarPlantillaTiempoComidaUseCase(repo)
    await uc.ejecutar(
        EliminarPlantillaTiempoComidaCommand(
            plantilla_id=plantilla_id, numero_dia=numero_dia, tipo=tipo
        )
    )


# ── Recetas (siempre desde catálogo) ─────────────────────────────────────────────

@router.post("/{plantilla_id}/dias/{numero_dia}/tiempos/{tipo}/recetas", status_code=204)
async def agregar_plantilla_receta(
    plantilla_id: UUID,
    numero_dia: int,
    tipo: TipoTiempoComida,
    body: AgregarPlantillaRecetaRequest,
    repo: PlantillaPlanRepository = Depends(_get_repo),
    catalogo_repo: RecetaCatalogoRepository = Depends(_get_catalogo_repo),
):
    uc = AgregarPlantillaRecetaUseCase(repo, catalogo_repo)
    await uc.ejecutar(
        AgregarPlantillaRecetaCommand(
            plantilla_id=plantilla_id,
            numero_dia=numero_dia,
            tipo=tipo,
            receta_catalogo_id=body.receta_catalogo_id,
            cantidad=body.cantidad,
            unidad=body.unidad,
        )
    )


@router.delete(
    "/{plantilla_id}/dias/{numero_dia}/tiempos/{tipo}/recetas/{receta_id}", status_code=204
)
async def eliminar_plantilla_receta(
    plantilla_id: UUID,
    numero_dia: int,
    tipo: TipoTiempoComida,
    receta_id: UUID,
    repo: PlantillaPlanRepository = Depends(_get_repo),
):
    uc = EliminarPlantillaRecetaUseCase(repo)
    await uc.ejecutar(
        EliminarPlantillaRecetaCommand(
            plantilla_id=plantilla_id, numero_dia=numero_dia, tipo=tipo, receta_id=receta_id
        )
    )
