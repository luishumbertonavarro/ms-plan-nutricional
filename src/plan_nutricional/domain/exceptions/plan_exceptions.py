from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from plan_nutricional.domain.model.enums import EstadoPlan, TipoTiempoComida


class PlanNutricionalDomainError(Exception):
    pass


class PlanNoModificableError(PlanNutricionalDomainError):
    def __init__(self, estado: EstadoPlan):
        super().__init__(
            f"No se puede modificar un plan en estado '{estado.value}'. "
            f"Solo los planes ACTIVO admiten cambios."
        )


class TransicionEstadoInvalidaError(PlanNutricionalDomainError):
    def __init__(self, estado_actual: EstadoPlan, estado_destino: EstadoPlan):
        super().__init__(
            f"No se puede pasar de '{estado_actual.value}' a '{estado_destino.value}'."
        )


class DiaDuplicadoError(PlanNutricionalDomainError):
    def __init__(self, numero_dia: int):
        super().__init__(f"Ya existe un día con número '{numero_dia}' en el plan.")


class DiaFueraDeDuracionError(PlanNutricionalDomainError):
    def __init__(self, numero_dia: int, duracion: int):
        super().__init__(
            f"El día '{numero_dia}' excede la duración del plan ({duracion} días). "
            f"Solo se permiten días entre 1 y {duracion}."
        )


class DiaNoEncontradoError(PlanNutricionalDomainError):
    def __init__(self, numero_dia: int):
        super().__init__(f"No existe un día con número '{numero_dia}' en el plan.")


class TiempoComidaDuplicadoError(PlanNutricionalDomainError):
    def __init__(self, tipo: TipoTiempoComida):
        super().__init__(
            f"El día ya tiene un tiempo de comida de tipo '{tipo.value}'."
        )


class TiempoComidaNoEncontradoError(PlanNutricionalDomainError):
    def __init__(self, tipo: TipoTiempoComida):
        super().__init__(
            f"No existe un tiempo de comida de tipo '{tipo.value}' en el día."
        )


class RecetaDuplicadaError(PlanNutricionalDomainError):
    def __init__(self, nombre: str):
        super().__init__(
            f"La receta '{nombre}' ya está asignada a este tiempo de comida."
        )


class RecetaNoEncontradaError(PlanNutricionalDomainError):
    def __init__(self, receta_id: UUID):
        super().__init__(f"No existe una receta con id '{receta_id}' en el tiempo de comida.")


class PlanNoEncontradoError(PlanNutricionalDomainError):
    def __init__(self, id: UUID):
        super().__init__(f"No se encontró un plan nutricional con id '{id}'.")


class PacienteNoEncontradoError(PlanNutricionalDomainError):
    """El BC de Pacientes no reconoce al paciente (respuesta 404 de ms-pacientes)."""

    def __init__(self, paciente_id: UUID):
        super().__init__(f"No se encontró un paciente con id '{paciente_id}' en ms-pacientes.")
