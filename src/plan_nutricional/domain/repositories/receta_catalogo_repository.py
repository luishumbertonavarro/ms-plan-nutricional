from abc import ABC, abstractmethod
from uuid import UUID

from plan_nutricional.domain.model.receta_catalogo import RecetaCatalogo


class RecetaCatalogoRepository(ABC):

    @abstractmethod
    async def guardar(self, receta: RecetaCatalogo) -> None: ...

    @abstractmethod
    async def obtener_por_id(self, id: UUID) -> RecetaCatalogo | None: ...

    @abstractmethod
    async def listar(self, solo_activas: bool = False) -> list[RecetaCatalogo]: ...
