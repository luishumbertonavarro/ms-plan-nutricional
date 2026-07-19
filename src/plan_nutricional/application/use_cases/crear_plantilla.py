from plan_nutricional.application.commands.commands import CrearPlantillaCommand
from plan_nutricional.domain.model import DuracionPlan, PlantillaPlan
from plan_nutricional.domain.repositories import PlantillaPlanRepository


class CrearPlantillaUseCase:
    def __init__(self, repo: PlantillaPlanRepository) -> None:
        self._repo = repo

    async def ejecutar(self, cmd: CrearPlantillaCommand) -> PlantillaPlan:
        plantilla = PlantillaPlan.crear(
            nombre=cmd.nombre,
            descripcion=cmd.descripcion,
            duracion=DuracionPlan(dias=cmd.duracion_dias),
        )
        await self._repo.guardar(plantilla)
        return plantilla
