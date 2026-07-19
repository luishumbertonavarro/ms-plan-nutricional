from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ObtenerPlanPorIdQuery:
    plan_id: UUID


@dataclass(frozen=True)
class ObtenerPlanesPacienteQuery:
    paciente_id: UUID


@dataclass(frozen=True)
class ListarPlanesActivosQuery:
    pass


@dataclass(frozen=True)
class ObtenerRecetaCatalogoPorIdQuery:
    receta_catalogo_id: UUID


@dataclass(frozen=True)
class ListarRecetasCatalogoQuery:
    solo_activas: bool = False


@dataclass(frozen=True)
class ObtenerPlantillaPorIdQuery:
    plantilla_id: UUID


@dataclass(frozen=True)
class ListarPlantillasQuery:
    pass
