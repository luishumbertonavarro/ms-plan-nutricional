"""Pruebas del caso de uso `CrearPlanDesdePlantillaUseCase`.

Recibe **tres** repositorios y recorre la plantilla resolviendo cada receta
contra el catálogo. Introduce dos técnicas de mocking adicionales:

  * `side_effect = [a, b, c]` — el mock devuelve un valor distinto en cada
    llamada sucesiva, para simular varias recetas del catálogo.
  * `await_count` / `assert_has_awaits` — verificar cuántas veces y con qué
    argumentos se llamó a la dependencia.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import call
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import (
    CrearPlanDesdePlantillaCommand,
    NecesidadNutricionalData,
)
from plan_nutricional.application.use_cases.crear_plan_desde_plantilla import (
    CrearPlanDesdePlantillaUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlantillaNoEncontradaError,
    RecetaCatalogoNoEncontradaError,
)
from plan_nutricional.domain.model import EstadoPlan, RecetaCatalogo, TipoTiempoComida


@pytest.fixture
def caso_de_uso(plan_repo_mock, plantilla_repo_mock, catalogo_repo_mock):
    # Ojo al orden de los parámetros: (plan_repo, plantilla_repo, catalogo_repo)
    return CrearPlanDesdePlantillaUseCase(
        plan_repo_mock, plantilla_repo_mock, catalogo_repo_mock
    )


@pytest.fixture
def comando():
    def _comando(plantilla_id):
        return CrearPlanDesdePlantillaCommand(
            plantilla_id=plantilla_id,
            paciente_id=uuid4(),
            fecha_inicio=date(2026, 1, 1),
            necesidad=NecesidadNutricionalData(
                calorias=Decimal("2000"),
                proteinas=Decimal("120"),
                grasas=Decimal("60"),
                carbohidratos=Decimal("250"),
            ),
            recomendacion_texto="Dieta hipocalórica",
        )

    return _comando


def construir_receta(nombre: str) -> RecetaCatalogo:
    return RecetaCatalogo.crear(
        nombre=nombre,
        descripcion=f"Descripción de {nombre}",
        instrucciones="Preparar y servir",
        cantidad=Decimal("200"),
        unidad="g",
    )


# ---------------------------------------------------------------------------
# Camino feliz
# ---------------------------------------------------------------------------

async def test_copia_la_estructura_completa_de_la_plantilla_al_plan(
    caso_de_uso,
    plan_repo_mock,
    plantilla_repo_mock,
    catalogo_repo_mock,
    construir_plantilla,
    comando,
):
    # Arrange — plantilla con 2 días, cada uno con un desayuno y una receta
    plantilla = construir_plantilla(dias_duracion=15)
    receta_ids = []
    for numero_dia in (1, 2):
        plantilla.agregar_dia(numero_dia)
        plantilla.agregar_tiempo_comida(numero_dia, TipoTiempoComida.DESAYUNO)
        receta_catalogo_id = uuid4()
        receta_ids.append(receta_catalogo_id)
        plantilla.agregar_receta(
            numero_dia,
            TipoTiempoComida.DESAYUNO,
            receta_catalogo_id,
            Decimal("150"),
            "g",
        )

    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    # side_effect: una receta distinta en cada llamada consecutiva al catálogo
    catalogo_repo_mock.obtener_por_id.side_effect = [
        construir_receta("Avena"),
        construir_receta("Tostadas"),
    ]

    # Act
    plan = await caso_de_uso.ejecutar(comando(plantilla.id))

    # Assert — estructura copiada
    assert plan.estado is EstadoPlan.ACTIVO
    assert plan.duracion == plantilla.duracion
    assert [d.numero_dia for d in plan.dias] == [1, 2]

    nombres = [
        receta.nombre
        for dia in plan.dias
        for tiempo in dia.tiempos_comida
        for receta in tiempo.recetas
    ]
    assert nombres == ["Avena", "Tostadas"]

    # Assert — se consultó el catálogo una vez por receta, con el id correcto
    assert catalogo_repo_mock.obtener_por_id.await_count == 2
    catalogo_repo_mock.obtener_por_id.assert_has_awaits(
        [call(receta_ids[0]), call(receta_ids[1])]
    )
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_la_porcion_del_plan_proviene_de_la_plantilla_no_del_catalogo(
    caso_de_uso,
    plantilla_repo_mock,
    catalogo_repo_mock,
    construir_plantilla,
    comando,
):
    # Arrange — la plantilla dice 150 g; la receta del catálogo, 200 g
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plantilla.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, uuid4(), Decimal("150"), "g"
    )
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    catalogo_repo_mock.obtener_por_id.return_value = construir_receta("Avena")

    # Act
    plan = await caso_de_uso.ejecutar(comando(plantilla.id))

    # Assert — manda la porción definida en la plantilla
    receta = plan.dias[0].tiempos_comida[0].recetas[0]
    assert receta.porcion.cantidad == Decimal("150")


async def test_plantilla_sin_dias_produce_un_plan_vacio_pero_valido(
    caso_de_uso,
    plan_repo_mock,
    plantilla_repo_mock,
    catalogo_repo_mock,
    construir_plantilla,
    comando,
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla_repo_mock.obtener_por_id.return_value = plantilla

    # Act
    plan = await caso_de_uso.ejecutar(comando(plantilla.id))

    # Assert
    assert plan.dias == []
    catalogo_repo_mock.obtener_por_id.assert_not_awaited()
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


# ---------------------------------------------------------------------------
# Ramas de error
# ---------------------------------------------------------------------------

async def test_plantilla_inexistente_lanza_error_y_no_persiste(
    caso_de_uso, plan_repo_mock, plantilla_repo_mock, catalogo_repo_mock, comando
):
    # Arrange
    plantilla_repo_mock.obtener_por_id.return_value = None

    # Act / Assert
    with pytest.raises(PlantillaNoEncontradaError):
        await caso_de_uso.ejecutar(comando(uuid4()))

    catalogo_repo_mock.obtener_por_id.assert_not_awaited()
    plan_repo_mock.guardar.assert_not_awaited()


async def test_receta_faltante_a_mitad_de_la_copia_aborta_sin_persistir(
    caso_de_uso,
    plan_repo_mock,
    plantilla_repo_mock,
    catalogo_repo_mock,
    construir_plantilla,
    comando,
):
    """Documenta que la copia no es atómica a nivel de agregado en memoria, pero
    sí lo es a nivel de persistencia: si falla una receta, no se guarda nada."""
    # Arrange — dos recetas; la segunda no está en el catálogo
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plantilla.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, uuid4(), Decimal("150"), "g"
    )
    plantilla.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, uuid4(), Decimal("150"), "g"
    )
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    catalogo_repo_mock.obtener_por_id.side_effect = [construir_receta("Avena"), None]

    # Act / Assert
    with pytest.raises(RecetaCatalogoNoEncontradaError):
        await caso_de_uso.ejecutar(comando(plantilla.id))

    assert catalogo_repo_mock.obtener_por_id.await_count == 2
    plan_repo_mock.guardar.assert_not_awaited()


async def test_una_receta_inactiva_del_catalogo_si_se_copia_al_plan(
    caso_de_uso,
    plan_repo_mock,
    plantilla_repo_mock,
    catalogo_repo_mock,
    construir_plantilla,
    comando,
):
    """HALLAZGO — asimetría de comportamiento entre dos casos de uso.

    `AgregarRecetaDesdeCatalogoUseCase` lanza `RecetaCatalogoInactivaError` si la
    receta está desactivada, pero `CrearPlanDesdePlantillaUseCase` no comprueba
    la bandera `activa` y la copia igualmente.

    Este test fija el comportamiento **actual** para dejar constancia de la
    inconsistencia; si se decide unificar el criterio, este test fallará y habrá
    que actualizarlo de forma deliberada.
    """
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plantilla.agregar_receta(
        1, TipoTiempoComida.DESAYUNO, uuid4(), Decimal("150"), "g"
    )
    plantilla_repo_mock.obtener_por_id.return_value = plantilla

    receta_inactiva = construir_receta("Avena")
    receta_inactiva.desactivar()
    catalogo_repo_mock.obtener_por_id.return_value = receta_inactiva

    # Act — no se lanza RecetaCatalogoInactivaError
    plan = await caso_de_uso.ejecutar(comando(plantilla.id))

    # Assert — la receta inactiva acabó en el plan del paciente
    assert plan.dias[0].tiempos_comida[0].recetas[0].nombre == "Avena"
    plan_repo_mock.guardar.assert_awaited_once()
