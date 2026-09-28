"""Pruebas del caso de uso `CrearRecetaCatalogoUseCase`.

Es el caso de uso más simple del microservicio: construye el agregado con la
factoría del dominio y lo persiste. No hay `obtener_por_id` previo, así que la
única rama de error es la validación del propio agregado.
"""

from decimal import Decimal

import pytest

from plan_nutricional.application.commands.commands import CrearRecetaCatalogoCommand
from plan_nutricional.application.use_cases.crear_receta_catalogo import (
    CrearRecetaCatalogoUseCase,
)


def _comando(nombre: str = "Avena con frutas") -> CrearRecetaCatalogoCommand:
    return CrearRecetaCatalogoCommand(
        nombre=nombre,
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar la avena con la fruta picada y servir.",
        cantidad=Decimal("250"),
        unidad="g",
    )


async def test_crear_una_receta_de_catalogo_la_devuelve_activa_y_la_persiste(
    catalogo_repo_mock,
):
    # Arrange
    caso_de_uso = CrearRecetaCatalogoUseCase(catalogo_repo_mock)

    # Act
    receta = await caso_de_uso.ejecutar(_comando())

    # Assert — una receta recién creada nace activa y con su porción por defecto
    assert receta.nombre == "Avena con frutas"
    assert receta.activa is True
    assert receta.porcion_default.cantidad == Decimal("250")
    assert receta.porcion_default.unidad == "g"
    catalogo_repo_mock.guardar.assert_awaited_once_with(receta)


async def test_crear_una_receta_de_catalogo_sin_nombre_no_persiste_nada(
    catalogo_repo_mock,
):
    # Arrange — la validación vive en `RecetaCatalogo.crear`, no en el caso de uso
    caso_de_uso = CrearRecetaCatalogoUseCase(catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(ValueError):
        await caso_de_uso.ejecutar(_comando(nombre="   "))

    catalogo_repo_mock.guardar.assert_not_awaited()


async def test_crear_una_receta_de_catalogo_con_porcion_negativa_no_persiste_nada(
    catalogo_repo_mock,
):
    # Arrange — la invariante la impone el value object `Porcion`
    caso_de_uso = CrearRecetaCatalogoUseCase(catalogo_repo_mock)
    comando = CrearRecetaCatalogoCommand(
        nombre="Avena con frutas",
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar y servir.",
        cantidad=Decimal("-1"),
        unidad="g",
    )

    # Act / Assert
    with pytest.raises(ValueError):
        await caso_de_uso.ejecutar(comando)

    catalogo_repo_mock.guardar.assert_not_awaited()
