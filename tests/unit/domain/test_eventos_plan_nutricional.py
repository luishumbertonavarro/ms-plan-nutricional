"""Eventos de dominio que anota PlanNutricional y que el repositorio pasa al outbox."""
from datetime import date
from decimal import Decimal

import pytest

from plan_nutricional.domain.exceptions import (
    DiaFueraDeDuracionError,
    TransicionEstadoInvalidaError,
)
from plan_nutricional.domain.model import EstadoPlan, TipoTiempoComida
from plan_nutricional.domain.model.eventos import (
    PlanNutricionalActualizado,
    PlanNutricionalCancelado,
    PlanNutricionalCreado,
    PlanNutricionalFinalizado,
)


def _tipos(eventos) -> list[type]:
    return [type(e) for e in eventos]


def test_crear_plan_anota_plan_nutricional_creado(construir_plan):
    # Arrange / Act
    plan = construir_plan()

    # Assert
    assert _tipos(plan.eventos) == [PlanNutricionalCreado]
    assert plan.eventos[0].plan_id == plan.id


def test_extraer_eventos_devuelve_los_pendientes_y_los_vacia(construir_plan):
    # Arrange
    plan = construir_plan()

    # Act
    eventos = plan.extraer_eventos()

    # Assert
    assert _tipos(eventos) == [PlanNutricionalCreado]
    assert plan.eventos == []


def test_varios_cambios_de_estructura_anotan_un_solo_plan_actualizado(construir_plan):
    # Arrange
    plan = construir_plan()
    plan.extraer_eventos()

    # Act
    plan.agregar_dia(1)
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, "Avena", "Avena con fruta", "Cocer 5 minutos",
        Decimal("250"), "gr",
    )

    # Assert
    assert _tipos(plan.eventos) == [PlanNutricionalActualizado]


@pytest.mark.parametrize(
    "operacion",
    [
        lambda p: p.eliminar_dia(1),
        lambda p: p.eliminar_tiempo_comida(1, TipoTiempoComida.DESAYUNO),
    ],
    ids=["eliminar_dia", "eliminar_tiempo_comida"],
)
def test_eliminar_estructura_anota_plan_actualizado(construir_plan, operacion):
    # Arrange
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan.extraer_eventos()

    # Act
    operacion(plan)

    # Assert
    assert _tipos(plan.eventos) == [PlanNutricionalActualizado]


def test_eliminar_receta_anota_plan_actualizado(construir_plan):
    # Arrange
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    receta = plan.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, "Avena", "d", "i", Decimal("1"), "gr"
    )
    plan.extraer_eventos()

    # Act
    plan.eliminar_receta(1, TipoTiempoComida.DESAYUNO, receta.id)

    # Assert
    assert _tipos(plan.eventos) == [PlanNutricionalActualizado]


def test_modificar_recomendacion_no_anota_eventos_de_integracion(construir_plan):
    # Arrange
    plan = construir_plan()
    plan.extraer_eventos()

    # Act
    plan.modificar_recomendacion("Nueva recomendación")

    # Assert
    assert plan.eventos == []


def test_operacion_rechazada_no_anota_eventos(construir_plan):
    # Arrange
    plan = construir_plan(dias_duracion=15)
    plan.extraer_eventos()

    # Act / Assert
    with pytest.raises(DiaFueraDeDuracionError):
        plan.agregar_dia(16)
    assert plan.eventos == []


def test_finalizar_plan_anota_plan_finalizado_con_su_fecha_fin(construir_plan):
    # Arrange
    plan = construir_plan()
    plan.extraer_eventos()

    # Act
    plan.cambiar_estado(EstadoPlan.FINALIZADO)

    # Assert
    assert _tipos(plan.eventos) == [PlanNutricionalFinalizado]
    assert plan.eventos[0].fecha_fin == date(2026, 1, 15)


def test_cancelar_plan_anota_plan_cancelado(construir_plan):
    # Arrange
    plan = construir_plan()
    plan.extraer_eventos()

    # Act
    plan.cancelar()

    # Assert
    assert _tipos(plan.eventos) == [PlanNutricionalCancelado]
    assert isinstance(plan.eventos[0].cancelado_el, date)


def test_transicion_invalida_no_anota_eventos(construir_plan):
    # Arrange
    plan = construir_plan(estado=EstadoPlan.CANCELADO)
    plan.extraer_eventos()

    # Act / Assert
    with pytest.raises(TransicionEstadoInvalidaError):
        plan.finalizar()
    assert plan.eventos == []
