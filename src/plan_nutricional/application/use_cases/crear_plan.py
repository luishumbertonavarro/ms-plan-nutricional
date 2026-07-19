from plan_nutricional.application.commands.commands import CrearPlanCommand
from plan_nutricional.domain.model import (
    DuracionPlan,
    NecesidadNutricional,
    PlanNutricional,
    RecomendacionNutricional,
)
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class CrearPlanUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: CrearPlanCommand) -> PlanNutricional:
        plan = PlanNutricional.crear(
            paciente_id=cmd.paciente_id,
            fecha_inicio=cmd.fecha_inicio,
            duracion=DuracionPlan(dias=cmd.duracion_dias),
            necesidad=NecesidadNutricional(
                calorias=cmd.necesidad.calorias,
                proteinas=cmd.necesidad.proteinas,
                grasas=cmd.necesidad.grasas,
                carbohidratos=cmd.necesidad.carbohidratos,
            ),
            recomendacion=RecomendacionNutricional(texto=cmd.recomendacion_texto),
        )
        await self._repo.guardar(plan)
        return plan
