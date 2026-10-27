from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import UUID


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EventoDominio:
    """Hecho ya ocurrido en el agregado. Se publica vía outbox al guardar el agregado."""

    plan_id: UUID
    ocurrido_en: datetime = field(default_factory=_ahora, kw_only=True)


@dataclass(frozen=True)
class PlanNutricionalCreado(EventoDominio):
    pass


@dataclass(frozen=True)
class PlanNutricionalActualizado(EventoDominio):
    """Cambió la estructura del plan (días, tiempos de comida o recetas)."""


@dataclass(frozen=True)
class PlanNutricionalFinalizado(EventoDominio):
    fecha_fin: date


@dataclass(frozen=True)
class PlanNutricionalCancelado(EventoDominio):
    cancelado_el: date
