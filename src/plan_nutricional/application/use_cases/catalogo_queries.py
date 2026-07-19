from plan_nutricional.application.queries.queries import (
    ListarRecetasCatalogoQuery,
    ObtenerRecetaCatalogoPorIdQuery,
)
from plan_nutricional.domain.model import RecetaCatalogo
from plan_nutricional.domain.repositories import RecetaCatalogoRepository


class ObtenerRecetaCatalogoPorIdHandler:
    def __init__(self, repo: RecetaCatalogoRepository) -> None:
        self._repo = repo

    async def ejecutar(self, query: ObtenerRecetaCatalogoPorIdQuery) -> RecetaCatalogo | None:
        return await self._repo.obtener_por_id(query.receta_catalogo_id)


class ListarRecetasCatalogoHandler:
    def __init__(self, repo: RecetaCatalogoRepository) -> None:
        self._repo = repo

    async def ejecutar(self, query: ListarRecetasCatalogoQuery) -> list[RecetaCatalogo]:
        return await self._repo.listar(solo_activas=query.solo_activas)
