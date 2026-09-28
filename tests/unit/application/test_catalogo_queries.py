"""Pruebas de los query handlers del catálogo de recetas."""

from uuid import uuid4

import pytest

from plan_nutricional.application.queries.queries import (
    ListarRecetasCatalogoQuery,
    ObtenerRecetaCatalogoPorIdQuery,
)
from plan_nutricional.application.use_cases.catalogo_queries import (
    ListarRecetasCatalogoHandler,
    ObtenerRecetaCatalogoPorIdHandler,
)


async def test_obtener_una_receta_de_catalogo_por_id_devuelve_la_del_repositorio(
    catalogo_repo_mock, receta_catalogo
):
    # Arrange
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    handler = ObtenerRecetaCatalogoPorIdHandler(catalogo_repo_mock)

    # Act
    resultado = await handler.ejecutar(
        ObtenerRecetaCatalogoPorIdQuery(receta_catalogo_id=receta_catalogo.id)
    )

    # Assert
    assert resultado is receta_catalogo
    catalogo_repo_mock.obtener_por_id.assert_awaited_once_with(receta_catalogo.id)
    catalogo_repo_mock.guardar.assert_not_awaited()


async def test_obtener_una_receta_de_catalogo_inexistente_devuelve_none(
    catalogo_repo_mock,
):
    # Arrange
    catalogo_repo_mock.obtener_por_id.return_value = None
    handler = ObtenerRecetaCatalogoPorIdHandler(catalogo_repo_mock)

    # Act
    resultado = await handler.ejecutar(
        ObtenerRecetaCatalogoPorIdQuery(receta_catalogo_id=uuid4())
    )

    # Assert
    assert resultado is None


@pytest.mark.parametrize("solo_activas", [True, False])
async def test_listar_las_recetas_de_catalogo_propaga_el_filtro_solo_activas(
    catalogo_repo_mock, receta_catalogo, solo_activas
):
    # Arrange — el filtrado lo hace el repositorio; el handler solo lo transmite
    catalogo_repo_mock.listar.return_value = [receta_catalogo]
    handler = ListarRecetasCatalogoHandler(catalogo_repo_mock)

    # Act
    resultado = await handler.ejecutar(
        ListarRecetasCatalogoQuery(solo_activas=solo_activas)
    )

    # Assert
    assert resultado == [receta_catalogo]
    catalogo_repo_mock.listar.assert_awaited_once_with(solo_activas=solo_activas)


async def test_listar_las_recetas_de_un_catalogo_vacio_devuelve_lista_vacia(
    catalogo_repo_mock,
):
    # Arrange
    catalogo_repo_mock.listar.return_value = []
    handler = ListarRecetasCatalogoHandler(catalogo_repo_mock)

    # Act
    resultado = await handler.ejecutar(ListarRecetasCatalogoQuery())

    # Assert — por defecto la query no filtra
    assert resultado == []
    catalogo_repo_mock.listar.assert_awaited_once_with(solo_activas=False)
