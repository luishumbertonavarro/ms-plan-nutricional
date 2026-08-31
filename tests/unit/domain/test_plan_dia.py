"""Pruebas unitarias de la entidad `PlanDia`.

Un día del plan agrupa sus tiempos de comida y garantiza que no se repita el tipo
(un día no puede tener dos desayunos).
"""

from uuid import uuid4

import pytest

from plan_nutricional.domain.exceptions.plan_exceptions import (
    TiempoComidaDuplicadoError,
    TiempoComidaNoEncontradoError,
)
from plan_nutricional.domain.model.enums import TipoTiempoComida
from plan_nutricional.domain.model.plan_dia import PlanDia


@pytest.fixture
def dia() -> PlanDia:
    return PlanDia.crear(plan_id=uuid4(), numero_dia=1)


def test_crear_dia_nace_sin_tiempos_de_comida(dia):
    # Assert
    assert dia.tiempos_comida == []
    assert dia.tiene_tiempos_comida is False


def test_agregar_tiempo_comida_lo_registra_en_el_dia(dia):
    # Act
    tiempo = dia.agregar_tiempo_comida(TipoTiempoComida.ALMUERZO)

    # Assert
    assert tiempo.tipo is TipoTiempoComida.ALMUERZO
    assert tiempo.plan_dia_id == dia.id
    assert dia.tiene_tiempos_comida is True


def test_agregar_tiempo_comida_repetido_lanza_error(dia):
    # Arrange
    dia.agregar_tiempo_comida(TipoTiempoComida.ALMUERZO)

    # Act / Assert
    with pytest.raises(TiempoComidaDuplicadoError):
        dia.agregar_tiempo_comida(TipoTiempoComida.ALMUERZO)


def test_agregar_tiempos_de_comida_de_distinto_tipo_es_valido(dia):
    # Act
    dia.agregar_tiempo_comida(TipoTiempoComida.DESAYUNO)
    dia.agregar_tiempo_comida(TipoTiempoComida.CENA)

    # Assert
    assert len(dia.tiempos_comida) == 2


def test_obtener_tiempo_comida_inexistente_lanza_error(dia):
    # Act / Assert
    with pytest.raises(TiempoComidaNoEncontradoError):
        dia.obtener_tiempo_comida(TipoTiempoComida.MEDIA_NOCHE)


def test_eliminar_tiempo_comida_lo_quita_del_dia(dia):
    # Arrange
    dia.agregar_tiempo_comida(TipoTiempoComida.MERIENDA)

    # Act
    dia.eliminar_tiempo_comida(TipoTiempoComida.MERIENDA)

    # Assert
    assert dia.tiempos_comida == []


def test_eliminar_tiempo_comida_inexistente_lanza_error(dia):
    # Act / Assert
    with pytest.raises(TiempoComidaNoEncontradoError):
        dia.eliminar_tiempo_comida(TipoTiempoComida.MERIENDA)


def test_la_lista_de_tiempos_de_comida_es_una_copia_defensiva(dia):
    # Arrange
    dia.agregar_tiempo_comida(TipoTiempoComida.DESAYUNO)

    # Act — mutar lo devuelto no debe afectar a la entidad
    dia.tiempos_comida.clear()

    # Assert
    assert dia.tiene_tiempos_comida is True
