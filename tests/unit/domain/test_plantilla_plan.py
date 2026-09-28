"""Pruebas unitarias del Aggregate Root `PlantillaPlan`.

Estructura reutilizable (días → tiempos de comida → recetas del catálogo) que
sirve de base para generar planes de pacientes.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.domain.exceptions.plantilla_exceptions import (
    PlantillaDiaDuplicadoError,
    PlantillaDiaFueraDeDuracionError,
    PlantillaDiaNoEncontradoError,
    PlantillaRecetaNoEncontradaError,
    PlantillaTiempoComidaDuplicadoError,
    PlantillaTiempoComidaNoEncontradoError,
)
from plan_nutricional.domain.model.enums import TipoTiempoComida
from plan_nutricional.domain.model.plantilla_plan import PlantillaPlan
from plan_nutricional.domain.model.value_objects import DuracionPlan


def test_crear_plantilla_nace_sin_dias(construir_plantilla):
    # Arrange / Act
    plantilla = construir_plantilla()

    # Assert
    assert plantilla.dias == []
    assert plantilla.duracion.dias == 15


@pytest.mark.parametrize("nombre", ["", "   ", "\n"])
def test_crear_plantilla_con_nombre_vacio_lanza_value_error(nombre):
    # Act / Assert
    with pytest.raises(ValueError, match="nombre de la plantilla"):
        PlantillaPlan.crear(
            nombre=nombre, descripcion="d", duracion=DuracionPlan(dias=15)
        )


@pytest.mark.parametrize("numero_dia", [0, 16, -1])
def test_agregar_dia_fuera_de_duracion_lanza_error(construir_plantilla, numero_dia):
    # Arrange
    plantilla = construir_plantilla(dias_duracion=15)

    # Act / Assert
    with pytest.raises(PlantillaDiaFueraDeDuracionError):
        plantilla.agregar_dia(numero_dia)


def test_agregar_dia_repetido_lanza_error(construir_plantilla):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)

    # Act / Assert
    with pytest.raises(PlantillaDiaDuplicadoError):
        plantilla.agregar_dia(1)


def test_agregar_tiempo_comida_en_dia_inexistente_lanza_error(construir_plantilla):
    # Arrange
    plantilla = construir_plantilla()

    # Act / Assert
    with pytest.raises(PlantillaDiaNoEncontradoError):
        plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)


def test_agregar_tiempo_comida_repetido_lanza_error(construir_plantilla):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)

    # Act / Assert
    with pytest.raises(PlantillaTiempoComidaDuplicadoError):
        plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)


def test_agregar_receta_referencia_al_catalogo_con_su_porcion(construir_plantilla):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    receta_catalogo_id = uuid4()

    # Act
    receta = plantilla.agregar_receta(
        numero_dia=1,
        tipo=TipoTiempoComida.DESAYUNO,
        receta_catalogo_id=receta_catalogo_id,
        cantidad=Decimal("200"),
        unidad="g",
    )

    # Assert — la plantilla guarda una referencia al catálogo, no una copia
    assert receta.receta_catalogo_id == receta_catalogo_id
    assert receta.porcion.cantidad == Decimal("200")


def test_agregar_receta_en_tiempo_de_comida_inexistente_lanza_error(construir_plantilla):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)

    # Act / Assert
    with pytest.raises(PlantillaTiempoComidaNoEncontradoError):
        plantilla.agregar_receta(1, TipoTiempoComida.CENA, uuid4(), Decimal("100"), "g")


def test_eliminar_receta_inexistente_lanza_error(construir_plantilla):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)

    # Act / Assert
    with pytest.raises(PlantillaRecetaNoEncontradaError):
        plantilla.eliminar_receta(1, TipoTiempoComida.DESAYUNO, uuid4())


def test_la_plantilla_no_tiene_ciclo_de_vida_y_siempre_es_editable(construir_plantilla):
    """A diferencia de PlanNutricional, la plantilla no tiene estados: no existe
    ningún `PlanNoModificableError` que pueda bloquear su edición."""
    # Arrange
    plantilla = construir_plantilla()

    # Act — se agrega y se elimina repetidamente sin restricción alguna
    plantilla.agregar_dia(1)
    plantilla.eliminar_dia(1)
    plantilla.agregar_dia(1)

    # Assert
    assert [d.numero_dia for d in plantilla.dias] == [1]


def test_agregar_receta_repetida_del_mismo_catalogo_no_esta_bloqueada(construir_plantilla):
    """Asimetría documentada: `TiempoComida` (del plan) sí impide recetas
    duplicadas, pero `PlantillaTiempoComida` no valida duplicados. Este test fija
    el comportamiento actual para que un cambio futuro sea deliberado."""
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    receta_catalogo_id = uuid4()

    # Act — se agrega dos veces la misma receta del catálogo
    plantilla.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, receta_catalogo_id, Decimal("100"), "g"
    )
    plantilla.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, receta_catalogo_id, Decimal("200"), "g"
    )

    # Assert — no se lanza excepción y quedan dos entradas
    tiempo = plantilla.dias[0].tiempos_comida[0]
    assert len(tiempo.recetas) == 2


def test_la_lista_de_dias_es_una_copia_defensiva(construir_plantilla):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)

    # Act
    plantilla.dias.clear()

    # Assert
    assert len(plantilla.dias) == 1


# ---------------------------------------------------------------------------
# Rehidratación desde el repositorio
# ---------------------------------------------------------------------------

def test_rehidratar_una_plantilla_por_constructor_conserva_su_identidad_y_sus_dias():
    """El repositorio no usa `crear`: reconstruye el agregado con `__init__`.

    Es un camino distinto al de la factoría y merece su propia prueba, porque el
    repositorio lo recorre en cada lectura de la base de datos.
    """
    # Arrange
    plantilla_id = uuid4()
    original = PlantillaPlan.crear(
        nombre="Plantilla hipocalórica",
        descripcion="Base de 15 días",
        duracion=DuracionPlan(dias=15),
    )
    original.agregar_dia(1)

    # Act
    rehidratada = PlantillaPlan(
        id=plantilla_id,
        nombre="Plantilla hipocalórica",
        descripcion="Base de 15 días",
        duracion=DuracionPlan(dias=15),
        dias=original.dias,
    )

    # Assert
    assert rehidratada.id == plantilla_id
    assert rehidratada.nombre == "Plantilla hipocalórica"
    assert rehidratada.descripcion == "Base de 15 días"
    assert rehidratada.duracion.dias == 15
    assert [d.numero_dia for d in rehidratada.dias] == [1]


def test_rehidratar_una_plantilla_no_revalida_el_nombre_a_diferencia_de_crear():
    """Asimetría real del modelo, documentada aquí en vez de corregida.

    `PlantillaPlan.crear` rechaza un nombre en blanco; el constructor de
    rehidratación no valida nada, porque asume que los datos que vienen de la
    base ya pasaron por la factoría en su día.
    """
    # Arrange / Act
    rehidratada = PlantillaPlan(
        id=uuid4(),
        nombre="",
        descripcion="Vino así desde la base de datos",
        duracion=DuracionPlan(dias=30),
        dias=[],
    )

    # Assert — el constructor la acepta...
    assert rehidratada.nombre == ""

    # ...mientras que la factoría la habría rechazado
    with pytest.raises(ValueError):
        PlantillaPlan.crear(
            nombre="", descripcion="Sin nombre", duracion=DuracionPlan(dias=30)
        )
