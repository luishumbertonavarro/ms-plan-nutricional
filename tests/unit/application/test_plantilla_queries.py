"""Pruebas de los query handlers de plantillas de plan."""

from uuid import uuid4

from plan_nutricional.application.queries.queries import (
    ListarPlantillasQuery,
    ObtenerPlantillaPorIdQuery,
)
from plan_nutricional.application.use_cases.plantilla_queries import (
    ListarPlantillasHandler,
    ObtenerPlantillaPorIdHandler,
)


async def test_obtener_una_plantilla_por_id_devuelve_la_del_repositorio(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    handler = ObtenerPlantillaPorIdHandler(plantilla_repo_mock)

    # Act
    resultado = await handler.ejecutar(
        ObtenerPlantillaPorIdQuery(plantilla_id=plantilla.id)
    )

    # Assert
    assert resultado is plantilla
    plantilla_repo_mock.obtener_por_id.assert_awaited_once_with(plantilla.id)
    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_obtener_una_plantilla_inexistente_devuelve_none_sin_lanzar_error(
    plantilla_repo_mock,
):
    # Arrange
    plantilla_repo_mock.obtener_por_id.return_value = None
    handler = ObtenerPlantillaPorIdHandler(plantilla_repo_mock)

    # Act
    resultado = await handler.ejecutar(
        ObtenerPlantillaPorIdQuery(plantilla_id=uuid4())
    )

    # Assert
    assert resultado is None


async def test_listar_las_plantillas_delega_en_el_repositorio(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantillas = [construir_plantilla(), construir_plantilla(dias_duracion=30)]
    plantilla_repo_mock.listar.return_value = plantillas
    handler = ListarPlantillasHandler(plantilla_repo_mock)

    # Act
    resultado = await handler.ejecutar(ListarPlantillasQuery())

    # Assert
    assert resultado == plantillas
    plantilla_repo_mock.listar.assert_awaited_once_with()


async def test_listar_las_plantillas_cuando_no_hay_ninguna_devuelve_lista_vacia(
    plantilla_repo_mock,
):
    # Arrange
    plantilla_repo_mock.listar.return_value = []
    handler = ListarPlantillasHandler(plantilla_repo_mock)

    # Act
    resultado = await handler.ejecutar(ListarPlantillasQuery())

    # Assert
    assert resultado == []
