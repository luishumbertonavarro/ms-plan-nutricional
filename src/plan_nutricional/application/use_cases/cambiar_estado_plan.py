from plan_nutricional.application.commands.commands import CambiarEstadoPlanCommand
from plan_nutricional.domain.exceptions import PlanNoEncontradoError
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class CambiarEstadoPlanUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: CambiarEstadoPlanCommand) -> None:
        plan = await self._repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        plan.cambiar_estado(cmd.nuevo_estado)
        await self._repo.guardar(plan)
