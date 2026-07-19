from plan_nutricional.application.commands.commands import AgregarPlantillaTiempoComidaCommand
from plan_nutricional.domain.exceptions import PlantillaNoEncontradaError
from plan_nutricional.domain.repositories import PlantillaPlanRepository


class AgregarPlantillaTiempoComidaUseCase:
    def __init__(self, repo: PlantillaPlanRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: AgregarPlantillaTiempoComidaCommand) -> None:
        plantilla = await self._repo.obtener_por_id(cmd.plantilla_id)
        if plantilla is None:
            raise PlantillaNoEncontradaError(cmd.plantilla_id)

        plantilla.agregar_tiempo_comida(cmd.numero_dia, cmd.tipo)
        await self._repo.guardar(plantilla)
