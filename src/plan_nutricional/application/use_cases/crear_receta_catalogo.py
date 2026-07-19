from plan_nutricional.application.commands.commands import CrearRecetaCatalogoCommand
from plan_nutricional.domain.model import RecetaCatalogo
from plan_nutricional.domain.repositories import RecetaCatalogoRepository


class CrearRecetaCatalogoUseCase:
    def __init__(self, repo: RecetaCatalogoRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: CrearRecetaCatalogoCommand) -> RecetaCatalogo:
        receta = RecetaCatalogo.crear(
            nombre=cmd.nombre,
            descripcion=cmd.descripcion,
            instrucciones=cmd.instrucciones,
            cantidad=cmd.cantidad,
            unidad=cmd.unidad,
        )
        await self._repo.guardar(receta)
        return receta
