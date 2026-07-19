from plan_nutricional.application.commands.commands import ModificarRecomendacionCommand
from plan_nutricional.domain.exceptions import PlanNoEncontradoError
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class ModificarRecomendacionUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: ModificarRecomendacionCommand) -> None:
        plan = await self._repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        plan.modificar_recomendacion(cmd.texto)
        await self._repo.guardar(plan)
