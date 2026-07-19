from plan_nutricional.application.commands.commands import EliminarPlantillaDiaCommand
from plan_nutricional.domain.exceptions import PlantillaNoEncontradaError
from plan_nutricional.domain.repositories import PlantillaPlanRepository


class EliminarPlantillaDiaUseCase:
    def __init__(self, repo: PlantillaPlanRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: EliminarPlantillaDiaCommand) -> None:
        plantilla = await self._repo.obtener_por_id(cmd.plantilla_id)
        if plantilla is None:
            raise PlantillaNoEncontradaError(cmd.plantilla_id)

        plantilla.eliminar_dia(cmd.numero_dia)
        await self._repo.guardar(plantilla)
