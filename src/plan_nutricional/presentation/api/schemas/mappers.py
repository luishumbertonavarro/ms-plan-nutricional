from plan_nutricional.domain.model import (
    PlanDia,
    PlanNutricional,
    PlantillaDia,
    PlantillaPlan,
    PlantillaReceta,
    PlantillaTiempoComida,
    Receta,
    RecetaCatalogo,
    TiempoComida,
)
from plan_nutricional.presentation.api.schemas.schemas import (
    NecesidadNutricionalResponse,
    PlanDiaResponse,
    PlanResponse,
    PlantillaDiaResponse,
    PlantillaRecetaResponse,
    PlantillaResponse,
    PlantillaTiempoComidaResponse,
    RecetaCatalogoResponse,
    RecetaResponse,
    TiempoComidaResponse,
)


def receta_to_response(receta: Receta) -> RecetaResponse:
    return RecetaResponse(
        id=receta.id,
        nombre=receta.nombre,
        descripcion=receta.descripcion,
        instrucciones=receta.instrucciones,
        cantidad=receta.porcion.cantidad,
        unidad=receta.porcion.unidad,
    )


def tiempo_comida_to_response(tiempo: TiempoComida) -> TiempoComidaResponse:
    return TiempoComidaResponse(
        id=tiempo.id,
        tipo=tiempo.tipo,
        recetas=[receta_to_response(r) for r in tiempo.recetas],
    )


def plan_dia_to_response(dia: PlanDia) -> PlanDiaResponse:
    return PlanDiaResponse(
        id=dia.id,
        numero_dia=dia.numero_dia,
        tiempos_comida=[tiempo_comida_to_response(t) for t in dia.tiempos_comida],
    )


def plan_to_response(plan: PlanNutricional) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        paciente_id=plan.paciente_id,
        fecha_inicio=plan.fecha_inicio,
        fecha_fin=plan.fecha_fin,
        estado=plan.estado,
        duracion_dias=plan.duracion.dias,
        necesidad=NecesidadNutricionalResponse(
            calorias=plan.necesidad.calorias,
            proteinas=plan.necesidad.proteinas,
            grasas=plan.necesidad.grasas,
            carbohidratos=plan.necesidad.carbohidratos,
        ),
        recomendacion_texto=plan.recomendacion.texto,
        dias=[plan_dia_to_response(d) for d in plan.dias],
    )


def receta_catalogo_to_response(receta: RecetaCatalogo) -> RecetaCatalogoResponse:
    return RecetaCatalogoResponse(
        id=receta.id,
        nombre=receta.nombre,
        descripcion=receta.descripcion,
        instrucciones=receta.instrucciones,
        cantidad=receta.porcion_default.cantidad,
        unidad=receta.porcion_default.unidad,
        activa=receta.activa,
    )


def plantilla_receta_to_response(receta: PlantillaReceta) -> PlantillaRecetaResponse:
    return PlantillaRecetaResponse(
        id=receta.id,
        receta_catalogo_id=receta.receta_catalogo_id,
        cantidad=receta.porcion.cantidad,
        unidad=receta.porcion.unidad,
    )


def plantilla_tiempo_comida_to_response(
    tiempo: PlantillaTiempoComida,
) -> PlantillaTiempoComidaResponse:
    return PlantillaTiempoComidaResponse(
        id=tiempo.id,
        tipo=tiempo.tipo,
        recetas=[plantilla_receta_to_response(r) for r in tiempo.recetas],
    )


def plantilla_dia_to_response(dia: PlantillaDia) -> PlantillaDiaResponse:
    return PlantillaDiaResponse(
        id=dia.id,
        numero_dia=dia.numero_dia,
        tiempos_comida=[plantilla_tiempo_comida_to_response(t) for t in dia.tiempos_comida],
    )


def plantilla_to_response(plantilla: PlantillaPlan) -> PlantillaResponse:
    return PlantillaResponse(
        id=plantilla.id,
        nombre=plantilla.nombre,
        descripcion=plantilla.descripcion,
        duracion_dias=plantilla.duracion.dias,
        dias=[plantilla_dia_to_response(d) for d in plantilla.dias],
    )
