from abc import ABC, abstractmethod
from uuid import UUID

from plan_nutricional.domain.model.plantilla_plan import PlantillaPlan


class PlantillaPlanRepository(ABC):

    @abstractmethod
    async def guardar(self, plantilla: PlantillaPlan) -> None: ...

    @abstractmethod
    async def obtener_por_id(self, id: UUID) -> PlantillaPlan | None: ...

    @abstractmethod
    async def listar(self) -> list[PlantillaPlan]: ...
