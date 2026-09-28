"""Pruebas del caso de uso `CambiarEstadoRecetaCatalogoUseCase`.

Un mismo caso de uso cubre activar y desactivar según el flag `activa` del
comando, así que las dos ramas se prueban con `parametrize`.
"""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import (
    CambiarEstadoRecetaCatalogoCommand,
)
from plan_nutricional.application.use_cases.cambiar_estado_receta_catalogo import (
    CambiarEstadoRecetaCatalogoUseCase,
)
from plan_nutricional.domain.exceptions import RecetaCatalogoNoEncontradaError


@pytest.mark.parametrize("activa", [True, False])
async def test_cambiar_el_estado_de_una_receta_existente_lo_aplica_y_persiste(
    catalogo_repo_mock, receta_catalogo, activa
):
    # Arrange — se parte del estado contrario al que se va a pedir
    receta_catalogo.activa = not activa
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    caso_de_uso = CambiarEstadoRecetaCatalogoUseCase(catalogo_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        CambiarEstadoRecetaCatalogoCommand(
            receta_catalogo_id=receta_catalogo.id, activa=activa
        )
    )

    # Assert
    assert receta_catalogo.activa is activa
    catalogo_repo_mock.obtener_por_id.assert_awaited_once_with(receta_catalogo.id)
    catalogo_repo_mock.guardar.assert_awaited_once_with(receta_catalogo)


async def test_cambiar_el_estado_de_una_receta_inexistente_lanza_error_y_no_persiste(
    catalogo_repo_mock,
):
    # Arrange
    catalogo_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = CambiarEstadoRecetaCatalogoUseCase(catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(RecetaCatalogoNoEncontradaError):
        await caso_de_uso.ejecutar(
            CambiarEstadoRecetaCatalogoCommand(
                receta_catalogo_id=uuid4(), activa=False
            )
        )

    catalogo_repo_mock.guardar.assert_not_awaited()
