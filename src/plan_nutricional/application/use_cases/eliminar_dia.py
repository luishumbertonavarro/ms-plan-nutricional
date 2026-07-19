from plan_nutricional.application.commands.commands import EliminarDiaCommand
from plan_nutricional.domain.exceptions import PlanNoEncontradoError
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class EliminarDiaUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: EliminarDiaCommand) -> None:
        plan = await self._repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        plan.eliminar_dia(cmd.numero_dia)
        await self._repo.guardar(plan)
