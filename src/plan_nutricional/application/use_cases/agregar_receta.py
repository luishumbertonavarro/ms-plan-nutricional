from plan_nutricional.application.commands.commands import AgregarRecetaCommand
from plan_nutricional.domain.exceptions import PlanNoEncontradoError
from plan_nutricional.domain.model import Receta
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class AgregarRecetaUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: AgregarRecetaCommand) -> Receta:
        plan = await self._repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        receta = plan.agregar_receta(
            numero_dia=cmd.numero_dia,
            tipo=cmd.tipo,
            nombre=cmd.nombre,
            descripcion=cmd.descripcion,
            instrucciones=cmd.instrucciones,
            cantidad=cmd.cantidad,
            unidad=cmd.unidad,
        )
        await self._repo.guardar(plan)
        return receta
