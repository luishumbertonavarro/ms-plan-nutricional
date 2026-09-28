"""Pruebas unitarias de la entidad `Receta`.

`Receta` es la hoja del agregado `PlanNutricional`. Su única operación propia es
cambiar la porción; el resto de reglas (duplicados, búsqueda) viven en
`TiempoComida` y se prueban allí.
"""

from decimal import Decimal
from uuid import uuid4

from plan_nutricional.domain.model.receta import Receta
from plan_nutricional.domain.model.value_objects import Porcion


def _receta() -> Receta:
    return Receta.crear(
        tiempo_comida_id=uuid4(),
        nombre="Avena con frutas",
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar la avena con la fruta picada y servir.",
        porcion=Porcion(cantidad=Decimal("250"), unidad="g"),
    )


def test_crear_una_receta_le_asigna_identidad_y_conserva_su_porcion():
    # Arrange
    tiempo_comida_id = uuid4()
    porcion = Porcion(cantidad=Decimal("250"), unidad="g")

    # Act
    receta = Receta.crear(
        tiempo_comida_id=tiempo_comida_id,
        nombre="Avena con frutas",
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar y servir.",
        porcion=porcion,
    )

    # Assert
    assert receta.id is not None
    assert receta.tiempo_comida_id == tiempo_comida_id
    assert receta.porcion is porcion


def test_cambiar_la_porcion_reemplaza_el_value_object_completo():
    # Arrange — la porción es un VO inmutable: no se muta, se sustituye
    receta = _receta()
    nueva_porcion = Porcion(cantidad=Decimal("300"), unidad="ml")

    # Act
    receta.cambiar_porcion(nueva_porcion)

    # Assert
    assert receta.porcion is nueva_porcion
    assert receta.porcion.cantidad == Decimal("300")
    assert receta.porcion.unidad == "ml"


def test_cambiar_la_porcion_no_altera_la_identidad_ni_el_nombre_de_la_receta():
    # Arrange
    receta = _receta()
    receta_id = receta.id

    # Act
    receta.cambiar_porcion(Porcion(cantidad=Decimal("100"), unidad="g"))

    # Assert
    assert receta.id == receta_id
    assert receta.nombre == "Avena con frutas"
