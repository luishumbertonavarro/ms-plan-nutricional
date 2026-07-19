from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from plan_nutricional.domain.model.enums import TipoTiempoComida
from plan_nutricional.domain.model.value_objects import DuracionPlan, Porcion
from plan_nutricional.domain.exceptions.plantilla_exceptions import (
    PlantillaDiaDuplicadoError,
    PlantillaDiaFueraDeDuracionError,
    PlantillaDiaNoEncontradoError,
    PlantillaRecetaNoEncontradaError,
    PlantillaTiempoComidaDuplicadoError,
    PlantillaTiempoComidaNoEncontradoError,
)


# ---------------------------------------------------------------------------
# Entidades hijas
# ---------------------------------------------------------------------------

@dataclass
class PlantillaReceta:
    """Referencia a una receta del catálogo dentro de una plantilla, con su porción."""

    id: UUID
    tiempo_comida_id: UUID
    receta_catalogo_id: UUID
    porcion: Porcion

    @classmethod
    def crear(
        cls, tiempo_comida_id: UUID, receta_catalogo_id: UUID, porcion: Porcion
    ) -> "PlantillaReceta":
        return cls(
            id=uuid4(),
            tiempo_comida_id=tiempo_comida_id,
            receta_catalogo_id=receta_catalogo_id,
            porcion=porcion,
        )


@dataclass
class PlantillaTiempoComida:
    """Tiempo de comida dentro de un día de la plantilla. Contiene referencias a recetas del catálogo."""

    id: UUID
    plantilla_dia_id: UUID
    tipo: TipoTiempoComida
    _recetas: list[PlantillaReceta] = field(default_factory=list, repr=False)

    @classmethod
    def crear(cls, plantilla_dia_id: UUID, tipo: TipoTiempoComida) -> "PlantillaTiempoComida":
        return cls(id=uuid4(), plantilla_dia_id=plantilla_dia_id, tipo=tipo)

    @property
    def recetas(self) -> list[PlantillaReceta]:
        return list(self._recetas)

    def agregar_receta(
        self, receta_catalogo_id: UUID, cantidad: Decimal, unidad: str
    ) -> PlantillaReceta:
        porcion = Porcion(cantidad=cantidad, unidad=unidad)
        receta = PlantillaReceta.crear(
            tiempo_comida_id=self.id, receta_catalogo_id=receta_catalogo_id, porcion=porcion
        )
        self._recetas.append(receta)
        return receta

    def eliminar_receta(self, receta_id: UUID) -> None:
        receta = self._buscar_receta(receta_id)
        self._recetas.remove(receta)

    def _buscar_receta(self, receta_id: UUID) -> PlantillaReceta:
        for r in self._recetas:
            if r.id == receta_id:
                return r
        raise PlantillaRecetaNoEncontradaError(receta_id)


@dataclass
class PlantillaDia:
    """Día numerado dentro de la plantilla."""

    id: UUID
    plantilla_id: UUID
    numero_dia: int
    _tiempos_comida: list[PlantillaTiempoComida] = field(default_factory=list, repr=False)

    @classmethod
    def crear(cls, plantilla_id: UUID, numero_dia: int) -> "PlantillaDia":
        return cls(id=uuid4(), plantilla_id=plantilla_id, numero_dia=numero_dia)

    @property
    def tiempos_comida(self) -> list[PlantillaTiempoComida]:
        return list(self._tiempos_comida)

    def agregar_tiempo_comida(self, tipo: TipoTiempoComida) -> PlantillaTiempoComida:
        if any(tc.tipo == tipo for tc in self._tiempos_comida):
            raise PlantillaTiempoComidaDuplicadoError(tipo)
        tiempo = PlantillaTiempoComida.crear(plantilla_dia_id=self.id, tipo=tipo)
        self._tiempos_comida.append(tiempo)
        return tiempo

    def eliminar_tiempo_comida(self, tipo: TipoTiempoComida) -> None:
        tiempo = self._buscar_tiempo_comida(tipo)
        self._tiempos_comida.remove(tiempo)

    def obtener_tiempo_comida(self, tipo: TipoTiempoComida) -> PlantillaTiempoComida:
        return self._buscar_tiempo_comida(tipo)

    def _buscar_tiempo_comida(self, tipo: TipoTiempoComida) -> PlantillaTiempoComida:
        for tc in self._tiempos_comida:
            if tc.tipo == tipo:
                return tc
        raise PlantillaTiempoComidaNoEncontradoError(tipo)


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------

class PlantillaPlan:
    """Aggregate Root: plantilla reutilizable de plan alimentario (BC3).

    Define una estructura base de días → tiempos de comida → recetas (del catálogo)
    que el nutricionista puede usar para generar un PlanNutricional para un paciente
    y luego personalizarlo. A diferencia de PlanNutricional, no tiene ciclo de vida
    (ACTIVO/FINALIZADO/CANCELADO): es siempre editable, como cualquier catálogo.
    """

    @classmethod
    def crear(cls, nombre: str, descripcion: str, duracion: DuracionPlan) -> "PlantillaPlan":
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la plantilla no puede estar vacío.")
        instance = cls.__new__(cls)
        instance._id = uuid4()
        instance._nombre = nombre
        instance._descripcion = descripcion
        instance._duracion = duracion
        instance._dias: list[PlantillaDia] = []
        return instance

    def __init__(
        self,
        id: UUID,
        nombre: str,
        descripcion: str,
        duracion: DuracionPlan,
        dias: list[PlantillaDia],
    ) -> None:
        self._id = id
        self._nombre = nombre
        self._descripcion = descripcion
        self._duracion = duracion
        self._dias = dias

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def duracion(self) -> DuracionPlan:
        return self._duracion

    @property
    def dias(self) -> list[PlantillaDia]:
        return list(self._dias)

    def agregar_dia(self, numero_dia: int) -> PlantillaDia:
        if numero_dia < 1 or numero_dia > self._duracion.dias:
            raise PlantillaDiaFueraDeDuracionError(numero_dia, self._duracion.dias)
        if any(d.numero_dia == numero_dia for d in self._dias):
            raise PlantillaDiaDuplicadoError(numero_dia)
        dia = PlantillaDia.crear(plantilla_id=self._id, numero_dia=numero_dia)
        self._dias.append(dia)
        return dia

    def eliminar_dia(self, numero_dia: int) -> None:
        dia = self._obtener_dia(numero_dia)
        self._dias.remove(dia)

    def agregar_tiempo_comida(self, numero_dia: int, tipo: TipoTiempoComida):
        dia = self._obtener_dia(numero_dia)
        return dia.agregar_tiempo_comida(tipo)

    def eliminar_tiempo_comida(self, numero_dia: int, tipo: TipoTiempoComida) -> None:
        dia = self._obtener_dia(numero_dia)
        dia.eliminar_tiempo_comida(tipo)

    def agregar_receta(
        self,
        numero_dia: int,
        tipo: TipoTiempoComida,
        receta_catalogo_id: UUID,
        cantidad: Decimal,
        unidad: str,
    ):
        dia = self._obtener_dia(numero_dia)
        tiempo = dia.obtener_tiempo_comida(tipo)
        return tiempo.agregar_receta(receta_catalogo_id, cantidad, unidad)

    def eliminar_receta(self, numero_dia: int, tipo: TipoTiempoComida, receta_id: UUID) -> None:
        dia = self._obtener_dia(numero_dia)
        tiempo = dia.obtener_tiempo_comida(tipo)
        tiempo.eliminar_receta(receta_id)

    def _obtener_dia(self, numero_dia: int) -> PlantillaDia:
        for d in self._dias:
            if d.numero_dia == numero_dia:
                return d
        raise PlantillaDiaNoEncontradoError(numero_dia)
