from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from plan_nutricional.domain.model.enums import TipoTiempoComida
from plan_nutricional.domain.model.receta import Receta
from plan_nutricional.domain.model.value_objects import Porcion
from plan_nutricional.domain.exceptions.plan_exceptions import (
    RecetaDuplicadaError,
    RecetaNoEncontradaError,
)


@dataclass
class TiempoComida:
    """Ingesta diaria definida en el plan (desayuno, almuerzo, etc.). Contiene múltiples Recetas."""

    id: UUID
    plan_dia_id: UUID
    tipo: TipoTiempoComida
    _recetas: list[Receta] = field(default_factory=list, repr=False)

    @classmethod
    def crear(cls, plan_dia_id: UUID, tipo: TipoTiempoComida) -> "TiempoComida":
        return cls(id=uuid4(), plan_dia_id=plan_dia_id, tipo=tipo)

    @property
    def recetas(self) -> list[Receta]:
        return list(self._recetas)

    def agregar_receta(
        self,
        nombre: str,
        descripcion: str,
        instrucciones: str,
        cantidad: Decimal,
        unidad: str,
    ) -> Receta:
        if any(r.nombre.lower() == nombre.lower() for r in self._recetas):
            raise RecetaDuplicadaError(nombre)
        porcion = Porcion(cantidad=cantidad, unidad=unidad)
        receta = Receta.crear(
            tiempo_comida_id=self.id,
            nombre=nombre,
            descripcion=descripcion,
            instrucciones=instrucciones,
            porcion=porcion,
        )
        self._recetas.append(receta)
        return receta

    def eliminar_receta(self, receta_id: UUID) -> None:
        receta = self._buscar_receta(receta_id)
        self._recetas.remove(receta)

    def _buscar_receta(self, receta_id: UUID) -> Receta:
        for r in self._recetas:
            if r.id == receta_id:
                return r
        raise RecetaNoEncontradaError(receta_id)

    @property
    def tiene_recetas(self) -> bool:
        return len(self._recetas) > 0
