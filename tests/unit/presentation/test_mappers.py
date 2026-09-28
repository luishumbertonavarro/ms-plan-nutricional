"""Pruebas de los mappers dominio → esquemas de respuesta.

`presentation/api/schemas/mappers.py` contiene nueve **funciones puras**: reciben
un objeto del dominio y devuelven un modelo Pydantic. No usan `Request`, ni
sesión de base de datos, ni cliente HTTP, así que se prueban como cualquier otra
función del dominio — sin dobles y sin levantar nada.

Lo que verifican estos tests es el trabajo real del mapper: **aplanar los value
objects** (`Porcion` → `cantidad`/`unidad`, `NecesidadNutricional` → cuatro
campos, `RecomendacionNutricional` → `recomendacion_texto`, `DuracionPlan` →
`duracion_dias`) y **recorrer la jerarquía** completa del agregado.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from plan_nutricional.domain.model import EstadoPlan, TipoTiempoComida
from plan_nutricional.presentation.api.schemas.mappers import (
    plan_dia_to_response,
    plan_to_response,
    plantilla_dia_to_response,
    plantilla_receta_to_response,
    plantilla_tiempo_comida_to_response,
    plantilla_to_response,
    receta_catalogo_to_response,
    receta_to_response,
    tiempo_comida_to_response,
)


def _plan_completo(construir_plan):
    """Plan con un día, un tiempo de comida y una receta dentro."""
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan.agregar_receta(
        numero_dia=1,
        tipo=TipoTiempoComida.DESAYUNO,
        nombre="Avena con frutas",
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar la avena con la fruta picada y servir.",
        cantidad=Decimal("250"),
        unidad="g",
    )
    return plan


def test_mapear_un_plan_completo_serializa_dias_tiempos_y_recetas_anidados(
    construir_plan,
):
    # Arrange
    plan = _plan_completo(construir_plan)

    # Act
    respuesta = plan_to_response(plan)

    # Assert — la jerarquía llega entera hasta la hoja
    assert len(respuesta.dias) == 1
    dia = respuesta.dias[0]
    assert dia.numero_dia == 1
    assert len(dia.tiempos_comida) == 1
    tiempo = dia.tiempos_comida[0]
    assert tiempo.tipo is TipoTiempoComida.DESAYUNO
    assert len(tiempo.recetas) == 1
    assert tiempo.recetas[0].nombre == "Avena con frutas"


def test_mapear_un_plan_aplana_la_necesidad_la_duracion_y_la_recomendacion(
    construir_plan,
):
    # Arrange — los value objects no viajan como objetos, se aplanan en campos
    plan = construir_plan(dias_duracion=30)

    # Act
    respuesta = plan_to_response(plan)

    # Assert
    assert respuesta.id == plan.id
    assert respuesta.paciente_id == plan.paciente_id
    assert respuesta.fecha_inicio == date(2026, 1, 1)
    assert respuesta.fecha_fin == date(2026, 1, 30)
    assert respuesta.estado is EstadoPlan.ACTIVO
    assert respuesta.duracion_dias == 30
    assert respuesta.necesidad.calorias == Decimal("2000")
    assert respuesta.necesidad.proteinas == Decimal("120")
    assert respuesta.necesidad.grasas == Decimal("60")
    assert respuesta.necesidad.carbohidratos == Decimal("250")
    assert respuesta.recomendacion_texto == "Dieta hipocalórica"


def test_mapear_un_plan_sin_dias_devuelve_la_lista_de_dias_vacia(construir_plan):
    # Arrange
    plan = construir_plan()

    # Act
    respuesta = plan_to_response(plan)

    # Assert
    assert respuesta.dias == []


def test_mapear_un_dia_y_un_tiempo_de_comida_por_separado_conserva_su_identidad(
    construir_plan,
):
    # Arrange — los mappers intermedios también son públicos y se usan sueltos
    plan = _plan_completo(construir_plan)
    dia = plan.dias[0]
    tiempo = dia.tiempos_comida[0]

    # Act
    respuesta_dia = plan_dia_to_response(dia)
    respuesta_tiempo = tiempo_comida_to_response(tiempo)

    # Assert
    assert respuesta_dia.id == dia.id
    assert respuesta_tiempo.id == tiempo.id
    assert respuesta_tiempo.recetas[0].id == tiempo.recetas[0].id


def test_mapear_una_receta_aplana_su_porcion_en_cantidad_y_unidad(construir_plan):
    # Arrange
    plan = _plan_completo(construir_plan)
    receta = plan.dias[0].tiempos_comida[0].recetas[0]

    # Act
    respuesta = receta_to_response(receta)

    # Assert
    assert respuesta.id == receta.id
    assert respuesta.nombre == "Avena con frutas"
    assert respuesta.cantidad == Decimal("250")
    assert respuesta.unidad == "g"


def test_mapear_una_receta_de_catalogo_expone_su_porcion_por_defecto_y_su_estado(
    receta_catalogo,
):
    # Arrange
    receta_catalogo.desactivar()

    # Act
    respuesta = receta_catalogo_to_response(receta_catalogo)

    # Assert
    assert respuesta.id == receta_catalogo.id
    assert respuesta.nombre == "Avena con frutas"
    assert respuesta.cantidad == Decimal("250")
    assert respuesta.unidad == "g"
    assert respuesta.activa is False


def test_mapear_una_plantilla_completa_serializa_toda_su_jerarquia(
    construir_plantilla,
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.ALMUERZO)
    receta_catalogo_id = uuid4()
    plantilla.agregar_receta(
        numero_dia=1,
        tipo=TipoTiempoComida.ALMUERZO,
        receta_catalogo_id=receta_catalogo_id,
        cantidad=Decimal("200"),
        unidad="g",
    )

    # Act
    respuesta = plantilla_to_response(plantilla)

    # Assert
    assert respuesta.id == plantilla.id
    assert respuesta.nombre == "Plantilla hipocalórica"
    assert respuesta.duracion_dias == 15
    tiempo = respuesta.dias[0].tiempos_comida[0]
    assert tiempo.tipo is TipoTiempoComida.ALMUERZO
    # La plantilla no copia la receta: guarda la referencia al catálogo
    assert tiempo.recetas[0].receta_catalogo_id == receta_catalogo_id
    assert tiempo.recetas[0].cantidad == Decimal("200")


def test_mapear_las_partes_de_una_plantilla_por_separado_conserva_su_identidad(
    construir_plantilla,
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(2)
    plantilla.agregar_tiempo_comida(2, TipoTiempoComida.CENA)
    receta = plantilla.agregar_receta(
        numero_dia=2,
        tipo=TipoTiempoComida.CENA,
        receta_catalogo_id=uuid4(),
        cantidad=Decimal("150"),
        unidad="ml",
    )
    dia = plantilla.dias[0]
    tiempo = dia.tiempos_comida[0]

    # Act
    respuesta_dia = plantilla_dia_to_response(dia)
    respuesta_tiempo = plantilla_tiempo_comida_to_response(tiempo)
    respuesta_receta = plantilla_receta_to_response(receta)

    # Assert
    assert respuesta_dia.numero_dia == 2
    assert respuesta_tiempo.id == tiempo.id
    assert respuesta_receta.id == receta.id
    assert respuesta_receta.unidad == "ml"
