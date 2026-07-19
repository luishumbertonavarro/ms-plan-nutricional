from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from plan_nutricional.application.commands import (
    AgregarDiaCommand,
    AgregarRecetaCommand,
    AgregarRecetaDesdeCatalogoCommand,
    AgregarTiempoComidaCommand,
    CambiarEstadoPlanCommand,
    CrearPlanCommand,
    CrearPlanDesdePlantillaCommand,
    EliminarDiaCommand,
    EliminarRecetaCommand,
    EliminarTiempoComidaCommand,
    ModificarRecomendacionCommand,
    NecesidadNutricionalData,
)
from plan_nutricional.application.queries import (
    ListarPlanesActivosQuery,
    ObtenerPlanesPacienteQuery,
    ObtenerPlanPorIdQuery,
)
from plan_nutricional.application.use_cases import (
    AgregarDiaUseCase,
    AgregarRecetaUseCase,
    AgregarRecetaDesdeCatalogoUseCase,
    AgregarTiempoComidaUseCase,
    CambiarEstadoPlanUseCase,
    CrearPlanDesdePlantillaUseCase,
    CrearPlanUseCase,
    EliminarDiaUseCase,
    EliminarRecetaUseCase,
    EliminarTiempoComidaUseCase,
    ListarPlanesActivosHandler,
    ModificarRecomendacionUseCase,
    ObtenerPlanesPacienteHandler,
    ObtenerPlanPorIdHandler,
)
from plan_nutricional.domain.model import TipoTiempoComida
from plan_nutricional.domain.repositories import (
    PlanNutricionalRepository,
    PlantillaPlanRepository,
    RecetaCatalogoRepository,
)
from plan_nutricional.infrastructure.persistence import (
    PlanNutricionalRepositoryImpl,
    PlantillaPlanRepositoryImpl,
    RecetaCatalogoRepositoryImpl,
    get_db_session,
)
from plan_nutricional.presentation.api.schemas import (
    AgregarDiaRequest,
    AgregarRecetaDesdeCatalogoRequest,
    AgregarRecetaRequest,
    AgregarTiempoComidaRequest,
    CambiarEstadoPlanRequest,
    CrearPlanDesdePlantillaRequest,
    CrearPlanRequest,
    ModificarRecomendacionRequest,
    PlanResponse,
    plan_to_response,
)

router = APIRouter(prefix="/planes", tags=["planes"])


async def _get_repo(session: AsyncSession = Depends(get_db_session)) -> PlanNutricionalRepository:
    return PlanNutricionalRepositoryImpl(session)


async def _get_catalogo_repo(
    session: AsyncSession = Depends(get_db_session),
) -> RecetaCatalogoRepository:
    return RecetaCatalogoRepositoryImpl(session)


async def _get_plantilla_repo(
    session: AsyncSession = Depends(get_db_session),
) -> PlantillaPlanRepository:
    return PlantillaPlanRepositoryImpl(session)


# ── Planes ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=PlanResponse, status_code=201)
async def crear_plan(
    body: CrearPlanRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = CrearPlanUseCase(repo)
    cmd = CrearPlanCommand(
        paciente_id=body.paciente_id,
        fecha_inicio=body.fecha_inicio,
        duracion_dias=body.duracion_dias,
        necesidad=NecesidadNutricionalData(
            calorias=body.necesidad.calorias,
            proteinas=body.necesidad.proteinas,
            grasas=body.necesidad.grasas,
            carbohidratos=body.necesidad.carbohidratos,
        ),
        recomendacion_texto=body.recomendacion_texto,
    )
    plan = await uc.ejecutar(cmd)
    return plan_to_response(plan)


@router.post("/desde-plantilla", response_model=PlanResponse, status_code=201)
async def crear_plan_desde_plantilla(
    body: CrearPlanDesdePlantillaRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
    plantilla_repo: PlantillaPlanRepository = Depends(_get_plantilla_repo),
    catalogo_repo: RecetaCatalogoRepository = Depends(_get_catalogo_repo),
):
    uc = CrearPlanDesdePlantillaUseCase(repo, plantilla_repo, catalogo_repo)
    cmd = CrearPlanDesdePlantillaCommand(
        plantilla_id=body.plantilla_id,
        paciente_id=body.paciente_id,
        fecha_inicio=body.fecha_inicio,
        necesidad=NecesidadNutricionalData(
            calorias=body.necesidad.calorias,
            proteinas=body.necesidad.proteinas,
            grasas=body.necesidad.grasas,
            carbohidratos=body.necesidad.carbohidratos,
        ),
        recomendacion_texto=body.recomendacion_texto,
    )
    plan = await uc.ejecutar(cmd)
    return plan_to_response(plan)


@router.get("", response_model=list[PlanResponse])
async def listar_planes_activos(repo: PlanNutricionalRepository = Depends(_get_repo)):
    handler = ListarPlanesActivosHandler(repo)
    planes = await handler.ejecutar(ListarPlanesActivosQuery())
    return [plan_to_response(p) for p in planes]


@router.get("/paciente/{paciente_id}", response_model=list[PlanResponse])
async def obtener_planes_paciente(
    paciente_id: UUID,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    handler = ObtenerPlanesPacienteHandler(repo)
    planes = await handler.ejecutar(ObtenerPlanesPacienteQuery(paciente_id=paciente_id))
    return [plan_to_response(p) for p in planes]


@router.get("/{plan_id}", response_model=PlanResponse)
async def obtener_plan(
    plan_id: UUID,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    handler = ObtenerPlanPorIdHandler(repo)
    plan = await handler.ejecutar(ObtenerPlanPorIdQuery(plan_id=plan_id))
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan nutricional no encontrado.")
    return plan_to_response(plan)


@router.patch("/{plan_id}/recomendacion", status_code=204)
async def modificar_recomendacion(
    plan_id: UUID,
    body: ModificarRecomendacionRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = ModificarRecomendacionUseCase(repo)
    await uc.ejecutar(ModificarRecomendacionCommand(plan_id=plan_id, texto=body.texto))


@router.patch("/{plan_id}/estado", status_code=204)
async def cambiar_estado_plan(
    plan_id: UUID,
    body: CambiarEstadoPlanRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = CambiarEstadoPlanUseCase(repo)
    await uc.ejecutar(CambiarEstadoPlanCommand(plan_id=plan_id, nuevo_estado=body.nuevo_estado))


# ── Días ───────────────────────────────────────────────────────────────────────

@router.post("/{plan_id}/dias", status_code=204)
async def agregar_dia(
    plan_id: UUID,
    body: AgregarDiaRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = AgregarDiaUseCase(repo)
    await uc.ejecutar(AgregarDiaCommand(plan_id=plan_id, numero_dia=body.numero_dia))


@router.delete("/{plan_id}/dias/{numero_dia}", status_code=204)
async def eliminar_dia(
    plan_id: UUID,
    numero_dia: int,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = EliminarDiaUseCase(repo)
    await uc.ejecutar(EliminarDiaCommand(plan_id=plan_id, numero_dia=numero_dia))


# ── Tiempos de comida ──────────────────────────────────────────────────────────

@router.post("/{plan_id}/dias/{numero_dia}/tiempos", status_code=204)
async def agregar_tiempo_comida(
    plan_id: UUID,
    numero_dia: int,
    body: AgregarTiempoComidaRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = AgregarTiempoComidaUseCase(repo)
    await uc.ejecutar(
        AgregarTiempoComidaCommand(plan_id=plan_id, numero_dia=numero_dia, tipo=body.tipo)
    )


@router.delete("/{plan_id}/dias/{numero_dia}/tiempos/{tipo}", status_code=204)
async def eliminar_tiempo_comida(
    plan_id: UUID,
    numero_dia: int,
    tipo: TipoTiempoComida,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = EliminarTiempoComidaUseCase(repo)
    await uc.ejecutar(
        EliminarTiempoComidaCommand(plan_id=plan_id, numero_dia=numero_dia, tipo=tipo)
    )


# ── Recetas ────────────────────────────────────────────────────────────────────

@router.post("/{plan_id}/dias/{numero_dia}/tiempos/{tipo}/recetas", status_code=204)
async def agregar_receta(
    plan_id: UUID,
    numero_dia: int,
    tipo: TipoTiempoComida,
    body: AgregarRecetaRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = AgregarRecetaUseCase(repo)
    await uc.ejecutar(
        AgregarRecetaCommand(
            plan_id=plan_id,
            numero_dia=numero_dia,
            tipo=tipo,
            nombre=body.nombre,
            descripcion=body.descripcion,
            instrucciones=body.instrucciones,
            cantidad=body.cantidad,
            unidad=body.unidad,
        )
    )


@router.delete("/{plan_id}/dias/{numero_dia}/tiempos/{tipo}/recetas/{receta_id}", status_code=204)
async def eliminar_receta(
    plan_id: UUID,
    numero_dia: int,
    tipo: TipoTiempoComida,
    receta_id: UUID,
    repo: PlanNutricionalRepository = Depends(_get_repo),
):
    uc = EliminarRecetaUseCase(repo)
    await uc.ejecutar(
        EliminarRecetaCommand(
            plan_id=plan_id, numero_dia=numero_dia, tipo=tipo, receta_id=receta_id
        )
    )


@router.post(
    "/{plan_id}/dias/{numero_dia}/tiempos/{tipo}/recetas/desde-catalogo", status_code=204
)
async def agregar_receta_desde_catalogo(
    plan_id: UUID,
    numero_dia: int,
    tipo: TipoTiempoComida,
    body: AgregarRecetaDesdeCatalogoRequest,
    repo: PlanNutricionalRepository = Depends(_get_repo),
    catalogo_repo: RecetaCatalogoRepository = Depends(_get_catalogo_repo),
):
    uc = AgregarRecetaDesdeCatalogoUseCase(repo, catalogo_repo)
    await uc.ejecutar(
        AgregarRecetaDesdeCatalogoCommand(
            plan_id=plan_id,
            numero_dia=numero_dia,
            tipo=tipo,
            receta_catalogo_id=body.receta_catalogo_id,
            cantidad=body.cantidad,
            unidad=body.unidad,
        )
    )
