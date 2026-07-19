from plan_nutricional.application.commands.commands import EliminarPlantillaTiempoComidaCommand
from plan_nutricional.domain.exceptions import PlantillaNoEncontradaError
from plan_nutricional.domain.repositories import PlantillaPlanRepository


class EliminarPlantillaTiempoComidaUseCase:
    def __init__(self, repo: PlantillaPlanRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: EliminarPlantillaTiempoComidaCommand) -> None:
        plantilla = await self._repo.obtener_por_id(cmd.plantilla_id)
        if plantilla is None:
            raise PlantillaNoEncontradaError(cmd.plantilla_id)

        plantilla.eliminar_tiempo_comida(cmd.numero_dia, cmd.tipo)
        await self._repo.guardar(plantilla)
