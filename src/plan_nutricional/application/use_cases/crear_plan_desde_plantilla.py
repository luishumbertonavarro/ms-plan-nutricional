from plan_nutricional.application.commands.commands import CrearPlanDesdePlantillaCommand
from plan_nutricional.domain.exceptions import (
    PlantillaNoEncontradaError,
    RecetaCatalogoNoEncontradaError,
)
from plan_nutricional.domain.model import (
    NecesidadNutricional,
    PlanNutricional,
    RecomendacionNutricional,
)
from plan_nutricional.domain.repositories import (
    PlanNutricionalRepository,
    PlantillaPlanRepository,
    RecetaCatalogoRepository,
)


class CrearPlanDesdePlantillaUseCase:
    """Genera un PlanNutricional para un paciente a partir de una PlantillaPlan,
    copiando su estructura de días/tiempos/recetas resolviendo cada receta contra
    el catálogo. El plan resultante queda ACTIVO y por lo tanto personalizable con
    los demás casos de uso de PlanNutricional (agregar_dia, agregar_receta, etc.).
    """

    def __init__(
        self,
        plan_repo: PlanNutricionalRepository,
        plantilla_repo: PlantillaPlanRepository,
        catalogo_repo: RecetaCatalogoRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._plantilla_repo = plantilla_repo
        self._catalogo_repo = catalogo_repo

    async def ejecutar(self, cmd: CrearPlanDesdePlantillaCommand) -> PlanNutricional:
        plantilla = await self._plantilla_repo.obtener_por_id(cmd.plantilla_id)
        if plantilla is None:
            raise PlantillaNoEncontradaError(cmd.plantilla_id)

        plan = PlanNutricional.crear(
            paciente_id=cmd.paciente_id,
            fecha_inicio=cmd.fecha_inicio,
            duracion=plantilla.duracion,
            necesidad=NecesidadNutricional(
                calorias=cmd.necesidad.calorias,
                proteinas=cmd.necesidad.proteinas,
                grasas=cmd.necesidad.grasas,
                carbohidratos=cmd.necesidad.carbohidratos,
            ),
            recomendacion=RecomendacionNutricional(texto=cmd.recomendacion_texto),
        )

        for plantilla_dia in plantilla.dias:
            plan.agregar_dia(plantilla_dia.numero_dia)
            for plantilla_tiempo in plantilla_dia.tiempos_comida:
                plan.agregar_tiempo_comida(plantilla_dia.numero_dia, plantilla_tiempo.tipo)
                for plantilla_receta in plantilla_tiempo.recetas:
                    receta_catalogo = await self._catalogo_repo.obtener_por_id(
                        plantilla_receta.receta_catalogo_id
                    )
                    if receta_catalogo is None:
                        raise RecetaCatalogoNoEncontradaError(
                            plantilla_receta.receta_catalogo_id
                        )
                    plan.agregar_receta(
                        numero_dia=plantilla_dia.numero_dia,
                        tipo=plantilla_tiempo.tipo,
                        nombre=receta_catalogo.nombre,
                        descripcion=receta_catalogo.descripcion,
                        instrucciones=receta_catalogo.instrucciones,
                        cantidad=plantilla_receta.porcion.cantidad,
                        unidad=plantilla_receta.porcion.unidad,
                    )

        await self._plan_repo.guardar(plan)
        return plan
