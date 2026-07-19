from abc import ABC, abstractmethod
from uuid import UUID

from plan_nutricional.domain.model.plan_nutricional import PlanNutricional


class PlanNutricionalRepository(ABC):

    @abstractmethod
    async def guardar(self, plan: PlanNutricional) -> None: ...

    @abstractmethod
    async def obtener_por_id(self, id: UUID) -> PlanNutricional | None: ...

    @abstractmethod
    async def obtener_por_paciente(self, paciente_id: UUID) -> list[PlanNutricional]: ...

    @abstractmethod
    async def listar_activos(self) -> list[PlanNutricional]: ...