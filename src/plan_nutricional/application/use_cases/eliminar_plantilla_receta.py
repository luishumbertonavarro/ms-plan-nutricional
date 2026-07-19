from plan_nutricional.application.commands.commands import EliminarPlantillaRecetaCommand
from plan_nutricional.domain.exceptions import PlantillaNoEncontradaError
from plan_nutricional.domain.repositories import PlantillaPlanRepository


class EliminarPlantillaRecetaUseCase:
    def __init__(self, repo: PlantillaPlanRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: EliminarPlantillaRecetaCommand) -> None:
        plantilla = await self._repo.obtener_por_id(cmd.plantilla_id)
        if plantilla is None:
            raise PlantillaNoEncontradaError(cmd.plantilla_id)

        plantilla.eliminar_receta(cmd.numero_dia, cmd.tipo, cmd.receta_id)
        await self._repo.guardar(plantilla)
