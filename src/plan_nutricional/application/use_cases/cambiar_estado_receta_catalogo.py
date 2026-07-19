from plan_nutricional.application.commands.commands import CambiarEstadoRecetaCatalogoCommand
from plan_nutricional.domain.exceptions import RecetaCatalogoNoEncontradaError
from plan_nutricional.domain.repositories import RecetaCatalogoRepository


class CambiarEstadoRecetaCatalogoUseCase:
    def __init__(self, repo: RecetaCatalogoRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: CambiarEstadoRecetaCatalogoCommand) -> None:
        receta = await self._repo.obtener_por_id(cmd.receta_catalogo_id)
        if receta is None:
            raise RecetaCatalogoNoEncontradaError(cmd.receta_catalogo_id)

        if cmd.activa:
            receta.activar()
        else:
            receta.desactivar()
        await self._repo.guardar(receta)
