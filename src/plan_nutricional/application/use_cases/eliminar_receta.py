from plan_nutricional.application.commands.commands import EliminarRecetaCommand
from plan_nutricional.domain.exceptions import PlanNoEncontradoError
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class EliminarRecetaUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: EliminarRecetaCommand) -> None:
        plan = await self._repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        plan.eliminar_receta(cmd.numero_dia, cmd.tipo, cmd.receta_id)
        await self._repo.guardar(plan)
