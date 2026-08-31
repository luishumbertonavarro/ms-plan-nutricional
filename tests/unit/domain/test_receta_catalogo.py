"""Pruebas unitarias del Aggregate Root `RecetaCatalogo`.

Receta reutilizable, independiente de cualquier plan. A diferencia de
`PlanNutricional` no tiene ciclo de vida de estados, solo una bandera `activa`
que determina si puede usarse en planes nuevos.
"""

from decimal import Decimal

import pytest

from plan_nutricional.domain.model.receta_catalogo import RecetaCatalogo


def test_crear_receta_nace_activa_con_su_porcion_por_defecto(receta_catalogo):
    # Assert
    assert receta_catalogo.activa is True
    assert receta_catalogo.porcion_default.cantidad == Decimal("250")
    assert receta_catalogo.porcion_default.unidad == "g"


@pytest.mark.parametrize("nombre", ["", "   ", "\n"])
def test_crear_receta_con_nombre_vacio_lanza_value_error(nombre):
    # Act / Assert
    with pytest.raises(ValueError, match="nombre de la receta"):
        RecetaCatalogo.crear(
            nombre=nombre,
            descripcion="d",
            instrucciones="i",
            cantidad=Decimal("100"),
            unidad="g",
        )


def test_crear_receta_con_cantidad_no_positiva_lanza_value_error():
    # Act / Assert — la validación proviene del Value Object Porcion
    with pytest.raises(ValueError, match="mayor que cero"):
        RecetaCatalogo.crear(
            nombre="Avena",
            descripcion="d",
            instrucciones="i",
            cantidad=Decimal("0"),
            unidad="g",
        )


def test_actualizar_reemplaza_los_datos_y_la_porcion(receta_catalogo):
    # Act
    receta_catalogo.actualizar(
        nombre="Avena integral",
        descripcion="Nueva descripción",
        instrucciones="Nuevas instrucciones",
        cantidad=Decimal("300"),
        unidad="ml",
    )

    # Assert
    assert receta_catalogo.nombre == "Avena integral"
    assert receta_catalogo.descripcion == "Nueva descripción"
    assert receta_catalogo.porcion_default.cantidad == Decimal("300")
    assert receta_catalogo.porcion_default.unidad == "ml"


def test_actualizar_con_nombre_vacio_lanza_error_y_no_modifica_nada(receta_catalogo):
    # Arrange
    nombre_original = receta_catalogo.nombre

    # Act / Assert
    with pytest.raises(ValueError, match="nombre de la receta"):
        receta_catalogo.actualizar("", "d", "i", Decimal("100"), "g")

    assert receta_catalogo.nombre == nombre_original


def test_desactivar_marca_la_receta_como_inactiva(receta_catalogo):
    # Act
    receta_catalogo.desactivar()

    # Assert
    assert receta_catalogo.activa is False


def test_activar_vuelve_a_habilitar_la_receta(receta_catalogo):
    # Arrange
    receta_catalogo.desactivar()

    # Act
    receta_catalogo.activar()

    # Assert
    assert receta_catalogo.activa is True
