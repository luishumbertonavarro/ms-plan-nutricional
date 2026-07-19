from plan_nutricional.application.queries.queries import (
    ListarPlantillasQuery,
    ObtenerPlantillaPorIdQuery,
)
from plan_nutricional.domain.model import PlantillaPlan
from plan_nutricional.domain.repositories import PlantillaPlanRepository


class ObtenerPlantillaPorIdHandler:
    def __init__(self, repo: PlantillaPlanRepository) -> None:
        self._repo = repo

    async def ejecutar(self, query: ObtenerPlantillaPorIdQuery) -> PlantillaPlan | None:
        return await self._repo.obtener_por_id(query.plantilla_id)


class ListarPlantillasHandler:
    def __init__(self, repo: PlantillaPlanRepository) -> None:
        self._repo = repo

    async def ejecutar(self, query: ListarPlantillasQuery) -> list[PlantillaPlan]:
        return await self._repo.listar()
