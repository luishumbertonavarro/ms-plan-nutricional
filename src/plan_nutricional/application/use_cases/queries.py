from plan_nutricional.application.queries.queries import (
    ListarPlanesActivosQuery,
    ObtenerPlanesPacienteQuery,
    ObtenerPlanPorIdQuery,
)
from plan_nutricional.domain.model import PlanNutricional
from plan_nutricional.domain.repositories import PlanNutricionalRepository


class ObtenerPlanPorIdHandler:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, query: ObtenerPlanPorIdQuery) -> PlanNutricional | None:
        return await self._repo.obtener_por_id(query.plan_id)


class ObtenerPlanesPacienteHandler:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, query: ObtenerPlanesPacienteQuery) -> list[PlanNutricional]:
        return await self._repo.obtener_por_paciente(query.paciente_id)


class ListarPlanesActivosHandler:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo

    async def ejecutar(self, query: ListarPlanesActivosQuery) -> list[PlanNutricional]:
        return await self._repo.listar_activos()
