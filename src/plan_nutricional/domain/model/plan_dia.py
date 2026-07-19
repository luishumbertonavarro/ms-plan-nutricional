from dataclasses import dataclass, field
from uuid import UUID, uuid4

from plan_nutricional.domain.model.enums import TipoTiempoComida
from plan_nutricional.domain.model.tiempo_comida import TiempoComida
from plan_nutricional.domain.exceptions.plan_exceptions import (
    TiempoComidaDuplicadoError,
    TiempoComidaNoEncontradoError,
)


@dataclass
class PlanDia:
    """Representa un día dentro del plan nutricional, identificado por su número de día."""

    id: UUID
    plan_id: UUID
    numero_dia: int
    _tiempos_comida: list[TiempoComida] = field(default_factory=list, repr=False)

    @classmethod
    def crear(cls, plan_id: UUID, numero_dia: int) -> "PlanDia":
        return cls(id=uuid4(), plan_id=plan_id, numero_dia=numero_dia)

    @property
    def tiempos_comida(self) -> list[TiempoComida]:
        return list(self._tiempos_comida)

    def agregar_tiempo_comida(self, tipo: TipoTiempoComida) -> TiempoComida:
        if any(tc.tipo == tipo for tc in self._tiempos_comida):
            raise TiempoComidaDuplicadoError(tipo)
        tiempo = TiempoComida.crear(plan_dia_id=self.id, tipo=tipo)
        self._tiempos_comida.append(tiempo)
        return tiempo

    def eliminar_tiempo_comida(self, tipo: TipoTiempoComida) -> None:
        tiempo = self._buscar_tiempo_comida(tipo)
        self._tiempos_comida.remove(tiempo)

    def obtener_tiempo_comida(self, tipo: TipoTiempoComida) -> TiempoComida:
        return self._buscar_tiempo_comida(tipo)

    def _buscar_tiempo_comida(self, tipo: TipoTiempoComida) -> TiempoComida:
        for tc in self._tiempos_comida:
            if tc.tipo == tipo:
                return tc
        raise TiempoComidaNoEncontradoError(tipo)

    @property
    def tiene_tiempos_comida(self) -> bool:
        return len(self._tiempos_comida) > 0
