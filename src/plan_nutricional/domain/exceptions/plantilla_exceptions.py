from __future__ import annotations

from uuid import UUID

from plan_nutricional.domain.exceptions.plan_exceptions import PlanNutricionalDomainError

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plan_nutricional.domain.model.enums import TipoTiempoComida


class PlantillaNoEncontradaError(PlanNutricionalDomainError):
    def __init__(self, id: UUID):
        super().__init__(f"No se encontró una plantilla de plan con id '{id}'.")


class PlantillaDiaDuplicadoError(PlanNutricionalDomainError):
    def __init__(self, numero_dia: int):
        super().__init__(f"Ya existe un día con número '{numero_dia}' en la plantilla.")


class PlantillaDiaFueraDeDuracionError(PlanNutricionalDomainError):
    def __init__(self, numero_dia: int, duracion: int):
        super().__init__(
            f"El día '{numero_dia}' excede la duración de la plantilla ({duracion} días). "
            f"Solo se permiten días entre 1 y {duracion}."
        )


class PlantillaDiaNoEncontradoError(PlanNutricionalDomainError):
    def __init__(self, numero_dia: int):
        super().__init__(f"No existe un día con número '{numero_dia}' en la plantilla.")


class PlantillaTiempoComidaDuplicadoError(PlanNutricionalDomainError):
    def __init__(self, tipo: TipoTiempoComida):
        super().__init__(
            f"El día de la plantilla ya tiene un tiempo de comida de tipo '{tipo.value}'."
        )


class PlantillaTiempoComidaNoEncontradoError(PlanNutricionalDomainError):
    def __init__(self, tipo: TipoTiempoComida):
        super().__init__(
            f"No existe un tiempo de comida de tipo '{tipo.value}' en el día de la plantilla."
        )


class PlantillaRecetaNoEncontradaError(PlanNutricionalDomainError):
    def __init__(self, receta_id: UUID):
        super().__init__(
            f"No existe una receta con id '{receta_id}' en el tiempo de comida de la plantilla."
        )
