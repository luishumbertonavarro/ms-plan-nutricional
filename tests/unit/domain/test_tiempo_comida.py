"""Pruebas unitarias de la entidad `TiempoComida`.

Agrupa las recetas de una ingesta e impide que se repita el nombre de una receta
dentro del mismo tiempo de comida.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.domain.exceptions.plan_exceptions import (
    RecetaDuplicadaError,
    RecetaNoEncontradaError,
)
from plan_nutricional.domain.model.enums import TipoTiempoComida
from plan_nutricional.domain.model.tiempo_comida import TiempoComida


@pytest.fixture
def tiempo() -> TiempoComida:
    return TiempoComida.crear(plan_dia_id=uuid4(), tipo=TipoTiempoComida.DESAYUNO)


def test_crear_tiempo_comida_nace_sin_recetas(tiempo):
    # Assert
    assert tiempo.recetas == []
    assert tiempo.tiene_recetas is False


def test_agregar_receta_la_registra_con_su_porcion(tiempo):
    # Act
    receta = tiempo.agregar_receta(
        nombre="Avena",
        descripcion="Con fruta",
        instrucciones="Mezclar",
        cantidad=Decimal("250"),
        unidad="g",
    )

    # Assert
    assert receta.tiempo_comida_id == tiempo.id
    assert receta.porcion.cantidad == Decimal("250")
    assert tiempo.tiene_recetas is True


@pytest.mark.parametrize("nombre_repetido", ["Avena", "AVENA", "avena", "AvEnA"])
def test_agregar_receta_duplicada_lanza_error_sin_distinguir_mayusculas(
    tiempo, nombre_repetido
):
    # Arrange
    tiempo.agregar_receta("Avena", "d", "i", Decimal("100"), "g")

    # Act / Assert — la comparación se hace en minúsculas
    with pytest.raises(RecetaDuplicadaError):
        tiempo.agregar_receta(nombre_repetido, "d", "i", Decimal("100"), "g")


def test_agregar_receta_con_nombre_vacio_lanza_value_error(tiempo):
    # Act / Assert — la validación vive en la factory de Receta
    with pytest.raises(ValueError, match="nombre de la receta"):
        tiempo.agregar_receta("   ", "d", "i", Decimal("100"), "g")


def test_eliminar_receta_existente_la_quita(tiempo):
    # Arrange
    receta = tiempo.agregar_receta("Avena", "d", "i", Decimal("100"), "g")

    # Act
    tiempo.eliminar_receta(receta.id)

    # Assert
    assert tiempo.tiene_recetas is False


def test_eliminar_receta_inexistente_lanza_error(tiempo):
    # Act / Assert
    with pytest.raises(RecetaNoEncontradaError):
        tiempo.eliminar_receta(uuid4())


def test_la_lista_de_recetas_es_una_copia_defensiva(tiempo):
    # Arrange
    tiempo.agregar_receta("Avena", "d", "i", Decimal("100"), "g")

    # Act
    tiempo.recetas.clear()

    # Assert
    assert tiempo.tiene_recetas is True
