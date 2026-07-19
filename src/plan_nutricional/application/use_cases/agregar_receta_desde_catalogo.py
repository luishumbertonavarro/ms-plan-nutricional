from plan_nutricional.application.commands.commands import AgregarRecetaDesdeCatalogoCommand
from plan_nutricional.domain.exceptions import (
    PlanNoEncontradoError,
    RecetaCatalogoInactivaError,
    RecetaCatalogoNoEncontradaError,
)
from plan_nutricional.domain.model import Receta
from plan_nutricional.domain.repositories import (
    PlanNutricionalRepository,
    RecetaCatalogoRepository,
)


class AgregarRecetaDesdeCatalogoUseCase:
    def __init__(
        self,
        plan_repo: PlanNutricionalRepository,
        catalogo_repo: RecetaCatalogoRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._catalogo_repo = catalogo_repo

    async def ejecutar(self, cmd: AgregarRecetaDesdeCatalogoCommand) -> Receta:
        plan = await self._plan_repo.obtener_por_id(cmd.plan_id)
        if plan is None:
            raise PlanNoEncontradoError(cmd.plan_id)

        receta_catalogo = await self._catalogo_repo.obtener_por_id(cmd.receta_catalogo_id)
        if receta_catalogo is None:
            raise RecetaCatalogoNoEncontradaError(cmd.receta_catalogo_id)
        if not receta_catalogo.activa:
            raise RecetaCatalogoInactivaError(cmd.receta_catalogo_id)

        cantidad = cmd.cantidad if cmd.cantidad is not None else receta_catalogo.porcion_default.cantidad
        unidad = cmd.unidad if cmd.unidad is not None else receta_catalogo.porcion_default.unidad

        receta = plan.agregar_receta(
            numero_dia=cmd.numero_dia,
            tipo=cmd.tipo,
            nombre=receta_catalogo.nombre,
            descripcion=receta_catalogo.descripcion,
            instrucciones=receta_catalogo.instrucciones,
            cantidad=cantidad,
            unidad=unidad,
        )
        await self._plan_repo.guardar(plan)
        return receta
