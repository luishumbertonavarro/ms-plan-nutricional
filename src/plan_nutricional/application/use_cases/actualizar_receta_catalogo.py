from plan_nutricional.application.commands.commands import ActualizarRecetaCatalogoCommand
from plan_nutricional.domain.exceptions import RecetaCatalogoNoEncontradaError
from plan_nutricional.domain.model import RecetaCatalogo
from plan_nutricional.domain.repositories import RecetaCatalogoRepository


class ActualizarRecetaCatalogoUseCase:
    def __init__(self, repo: RecetaCatalogoRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: ActualizarRecetaCatalogoCommand) -> RecetaCatalogo:
        receta = await self._repo.obtener_por_id(cmd.receta_catalogo_id)
        if receta is None:
            raise RecetaCatalogoNoEncontradaError(cmd.receta_catalogo_id)

        receta.actualizar(
            nombre=cmd.nombre,
            descripcion=cmd.descripcion,
            instrucciones=cmd.instrucciones,
            cantidad=cmd.cantidad,
            unidad=cmd.unidad,
        )
        await self._repo.guardar(receta)
        return receta
