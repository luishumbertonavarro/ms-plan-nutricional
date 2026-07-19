from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from plan_nutricional.application.commands import (
    ActualizarRecetaCatalogoCommand,
    CambiarEstadoRecetaCatalogoCommand,
    CrearRecetaCatalogoCommand,
)
from plan_nutricional.application.queries import (
    ListarRecetasCatalogoQuery,
    ObtenerRecetaCatalogoPorIdQuery,
)
from plan_nutricional.application.use_cases import (
    ActualizarRecetaCatalogoUseCase,
    CambiarEstadoRecetaCatalogoUseCase,
    CrearRecetaCatalogoUseCase,
    ListarRecetasCatalogoHandler,
    ObtenerRecetaCatalogoPorIdHandler,
)
from plan_nutricional.domain.repositories import RecetaCatalogoRepository
from plan_nutricional.infrastructure.persistence import (
    RecetaCatalogoRepositoryImpl,
    get_db_session,
)
from plan_nutricional.presentation.api.schemas import (
    ActualizarRecetaCatalogoRequest,
    CrearRecetaCatalogoRequest,
    RecetaCatalogoResponse,
    receta_catalogo_to_response,
)

router = APIRouter(prefix="/catalogo-recetas", tags=["catalogo-recetas"])


async def _get_repo(session: AsyncSession = Depends(get_db_session)) -> RecetaCatalogoRepository:
    return RecetaCatalogoRepositoryImpl(session)


@router.post("", response_model=RecetaCatalogoResponse, status_code=201)
async def crear_receta_catalogo(
    body: CrearRecetaCatalogoRequest,
    repo: RecetaCatalogoRepository = Depends(_get_repo),
):
    uc = CrearRecetaCatalogoUseCase(repo)
    receta = await uc.ejecutar(
        CrearRecetaCatalogoCommand(
            nombre=body.nombre,
            descripcion=body.descripcion,
            instrucciones=body.instrucciones,
            cantidad=body.cantidad,
            unidad=body.unidad,
        )
    )
    return receta_catalogo_to_response(receta)


@router.get("", response_model=list[RecetaCatalogoResponse])
async def listar_recetas_catalogo(
    solo_activas: bool = False,
    repo: RecetaCatalogoRepository = Depends(_get_repo),
):
    handler = ListarRecetasCatalogoHandler(repo)
    recetas = await handler.ejecutar(ListarRecetasCatalogoQuery(solo_activas=solo_activas))
    return [receta_catalogo_to_response(r) for r in recetas]


@router.get("/{receta_catalogo_id}", response_model=RecetaCatalogoResponse)
async def obtener_receta_catalogo(
    receta_catalogo_id: UUID,
    repo: RecetaCatalogoRepository = Depends(_get_repo),
):
    handler = ObtenerRecetaCatalogoPorIdHandler(repo)
    receta = await handler.ejecutar(
        ObtenerRecetaCatalogoPorIdQuery(receta_catalogo_id=receta_catalogo_id)
    )
    if receta is None:
        raise HTTPException(status_code=404, detail="Receta de catálogo no encontrada.")
    return receta_catalogo_to_response(receta)


@router.patch("/{receta_catalogo_id}", response_model=RecetaCatalogoResponse)
async def actualizar_receta_catalogo(
    receta_catalogo_id: UUID,
    body: ActualizarRecetaCatalogoRequest,
    repo: RecetaCatalogoRepository = Depends(_get_repo),
):
    uc = ActualizarRecetaCatalogoUseCase(repo)
    receta = await uc.ejecutar(
        ActualizarRecetaCatalogoCommand(
            receta_catalogo_id=receta_catalogo_id,
            nombre=body.nombre,
            descripcion=body.descripcion,
            instrucciones=body.instrucciones,
            cantidad=body.cantidad,
            unidad=body.unidad,
        )
    )
    return receta_catalogo_to_response(receta)


@router.patch("/{receta_catalogo_id}/activar", status_code=204)
async def activar_receta_catalogo(
    receta_catalogo_id: UUID,
    repo: RecetaCatalogoRepository = Depends(_get_repo),
):
    uc = CambiarEstadoRecetaCatalogoUseCase(repo)
    await uc.ejecutar(
        CambiarEstadoRecetaCatalogoCommand(receta_catalogo_id=receta_catalogo_id, activa=True)
    )


@router.patch("/{receta_catalogo_id}/desactivar", status_code=204)
async def desactivar_receta_catalogo(
    receta_catalogo_id: UUID,
    repo: RecetaCatalogoRepository = Depends(_get_repo),
):
    uc = CambiarEstadoRecetaCatalogoUseCase(repo)
    await uc.ejecutar(
        CambiarEstadoRecetaCatalogoCommand(receta_catalogo_id=receta_catalogo_id, activa=False)
    )
