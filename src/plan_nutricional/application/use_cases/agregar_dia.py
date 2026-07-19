from plan_nutricional.application.commands.commands import AgregarDiaCommand
from plan_nutricional.domain.exceptions import PlanNoEncontradoError
from plan_nutricional.domain.model import PlanDia
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class AgregarDiaUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: AgregarDiaCommand) -> PlanDia:
        plan = await self._repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        dia = plan.agregar_dia(cmd.numero_dia)
        await self._repo.guardar(plan)
        return dia
