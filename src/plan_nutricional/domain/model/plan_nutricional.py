from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from plan_nutricional.domain.model.enums import EstadoPlan, TipoTiempoComida
from plan_nutricional.domain.model.plan_dia import PlanDia
from plan_nutricional.domain.model.value_objects import (
    DuracionPlan,
    NecesidadNutricional,
    RecomendacionNutricional,
)
from plan_nutricional.domain.exceptions.plan_exceptions import (
    DiaDuplicadoError,
    DiaFueraDeDuracionError,
    DiaNoEncontradoError,
    PlanNoModificableError,
    TransicionEstadoInvalidaError,
)


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------

class PlanNutricional:
    """Aggregate Root de BC3 – Planificación Nutricional.

    Único punto de entrada para crear y modificar el plan alimenticio de un paciente.
    Controla el ciclo de vida de PlanDia → TiempoComida → Receta y protege todas
    las invariantes del agregado.
    """

    # ---------------------------------------------------------------------------
    # Factory
    # ---------------------------------------------------------------------------

    @classmethod
    def crear(
        cls,
        paciente_id: UUID,
        fecha_inicio: date,
        duracion: DuracionPlan,
        necesidad: NecesidadNutricional,
        recomendacion: RecomendacionNutricional,
    ) -> "PlanNutricional":
        plan_id = uuid4()
        fecha_fin = fecha_inicio + timedelta(days=duracion.dias - 1)
        instance = cls.__new__(cls)
        instance._id = plan_id
        instance._paciente_id = paciente_id
        instance._fecha_inicio = fecha_inicio
        instance._fecha_fin = fecha_fin
        instance._estado = EstadoPlan.ACTIVO
        instance._duracion = duracion
        instance._necesidad = necesidad
        instance._recomendacion = recomendacion
        instance._dias: list[PlanDia] = []
        return instance

    # ---------------------------------------------------------------------------
    # Constructor (para rehidratación desde el repositorio)
    # ---------------------------------------------------------------------------

    def __init__(
        self,
        id: UUID,
        paciente_id: UUID,
        fecha_inicio: date,
        fecha_fin: date,
        estado: EstadoPlan,
        duracion: DuracionPlan,
        necesidad: NecesidadNutricional,
        recomendacion: RecomendacionNutricional,
        dias: list[PlanDia],
    ) -> None:
        self._id = id
        self._paciente_id = paciente_id
        self._fecha_inicio = fecha_inicio
        self._fecha_fin = fecha_fin
        self._estado = estado
        self._duracion = duracion
        self._necesidad = necesidad
        self._recomendacion = recomendacion
        self._dias = dias

    # ---------------------------------------------------------------------------
    # Properties
    # ---------------------------------------------------------------------------

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def paciente_id(self) -> UUID:
        return self._paciente_id

    @property
    def fecha_inicio(self) -> date:
        return self._fecha_inicio

    @property
    def fecha_fin(self) -> date:
        return self._fecha_fin

    @property
    def estado(self) -> EstadoPlan:
        return self._estado

    @property
    def duracion(self) -> DuracionPlan:
        return self._duracion

    @property
    def necesidad(self) -> NecesidadNutricional:
        return self._necesidad

    @property
    def recomendacion(self) -> RecomendacionNutricional:
        return self._recomendacion

    @property
    def dias(self) -> list[PlanDia]:
        return list(self._dias)

    @property
    def total_dias_agregados(self) -> int:
        return len(self._dias)

    @property
    def es_activo(self) -> bool:
        return self._estado == EstadoPlan.ACTIVO

    # ---------------------------------------------------------------------------
    # Commands
    # ---------------------------------------------------------------------------

    def agregar_dia(self, numero_dia: int) -> PlanDia:
        self._verificar_modificable()
        if numero_dia < 1 or numero_dia > self._duracion.dias:
            raise DiaFueraDeDuracionError(numero_dia, self._duracion.dias)
        if any(d.numero_dia == numero_dia for d in self._dias):
            raise DiaDuplicadoError(numero_dia)
        dia = PlanDia.crear(plan_id=self._id, numero_dia=numero_dia)
        self._dias.append(dia)
        return dia

    def eliminar_dia(self, numero_dia: int) -> None:
        self._verificar_modificable()
        dia = self._obtener_dia(numero_dia)
        self._dias.remove(dia)

    def agregar_tiempo_comida(self, numero_dia: int, tipo: TipoTiempoComida):
        self._verificar_modificable()
        dia = self._obtener_dia(numero_dia)
        return dia.agregar_tiempo_comida(tipo)

    def eliminar_tiempo_comida(self, numero_dia: int, tipo: TipoTiempoComida) -> None:
        self._verificar_modificable()
        dia = self._obtener_dia(numero_dia)
        dia.eliminar_tiempo_comida(tipo)

    def agregar_receta(
        self,
        numero_dia: int,
        tipo: TipoTiempoComida,
        nombre: str,
        descripcion: str,
        instrucciones: str,
        cantidad: Decimal,
        unidad: str,
    ):
        self._verificar_modificable()
        dia = self._obtener_dia(numero_dia)
        tiempo = dia.obtener_tiempo_comida(tipo)
        return tiempo.agregar_receta(nombre, descripcion, instrucciones, cantidad, unidad)

    def eliminar_receta(
        self, numero_dia: int, tipo: TipoTiempoComida, receta_id: UUID
    ) -> None:
        self._verificar_modificable()
        dia = self._obtener_dia(numero_dia)
        tiempo = dia.obtener_tiempo_comida(tipo)
        tiempo.eliminar_receta(receta_id)

    def modificar_recomendacion(self, texto: str) -> None:
        self._verificar_modificable()
        self._recomendacion = RecomendacionNutricional(texto=texto)

    def cambiar_estado(self, nuevo_estado: EstadoPlan) -> None:
        transiciones_validas: dict[EstadoPlan, set[EstadoPlan]] = {
            EstadoPlan.ACTIVO: {EstadoPlan.FINALIZADO, EstadoPlan.CANCELADO},
            EstadoPlan.FINALIZADO: set(),
            EstadoPlan.CANCELADO: set(),
        }
        if nuevo_estado not in transiciones_validas[self._estado]:
            raise TransicionEstadoInvalidaError(self._estado, nuevo_estado)
        self._estado = nuevo_estado

    def finalizar(self) -> None:
        self.cambiar_estado(EstadoPlan.FINALIZADO)

    def cancelar(self) -> None:
        self.cambiar_estado(EstadoPlan.CANCELADO)

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _verificar_modificable(self) -> None:
        if self._estado != EstadoPlan.ACTIVO:
            raise PlanNoModificableError(self._estado)

    def _obtener_dia(self, numero_dia: int) -> PlanDia:
        for d in self._dias:
            if d.numero_dia == numero_dia:
                return d
        raise DiaNoEncontradoError(numero_dia)
