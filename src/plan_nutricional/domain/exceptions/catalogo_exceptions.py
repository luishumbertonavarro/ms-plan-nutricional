from __future__ import annotations

from uuid import UUID

from plan_nutricional.domain.exceptions.plan_exceptions import PlanNutricionalDomainError


class RecetaCatalogoNoEncontradaError(PlanNutricionalDomainError):
    def __init__(self, id: UUID):
        super().__init__(f"No se encontró una receta de catálogo con id '{id}'.")


class RecetaCatalogoInactivaError(PlanNutricionalDomainError):
    def __init__(self, id: UUID):
        super().__init__(
            f"La receta de catálogo con id '{id}' está inactiva y no puede utilizarse."
        )
