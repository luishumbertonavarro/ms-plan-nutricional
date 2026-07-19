from plan_nutricional.application.commands.commands import AgregarTiempoComidaCommand
from plan_nutricional.domain.exceptions import PlanNoEncontradoError
from plan_nutricional.domain.model import TiempoComida
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class AgregarTiempoComidaUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: AgregarTiempoComidaCommand) -> TiempoComida:
        plan = await self._repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        tiempo = plan.agregar_tiempo_comida(cmd.numero_dia, cmd.tipo)
        await self._repo.guardar(plan)
        return tiempo
