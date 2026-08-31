"""Pruebas del caso de uso `AgregarDiaUseCase` — ejemplo de referencia de mocking.

Este archivo es el patrón que siguen los demás casos de uso. Todos comparten la
misma estructura:

    1. recuperar el agregado del repositorio (`obtener_por_id`)
    2. si no existe, lanzar la excepción de dominio correspondiente
    3. invocar el método de dominio
    4. persistir (`guardar`)

El repositorio real habla con PostgreSQL. En una prueba unitaria se sustituye por
un **mock** (`AsyncMock(spec=PlanNutricionalRepository)`, definido en
`tests/conftest.py`), lo que permite:

  * controlar la entrada  → `plan_repo_mock.obtener_por_id.return_value = plan`
  * verificar la salida   → `plan_repo_mock.guardar.assert_awaited_once_with(plan)`

sin levantar ninguna base de datos.
"""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import AgregarDiaCommand
from plan_nutricional.application.use_cases.agregar_dia import AgregarDiaUseCase
from plan_nutricional.domain.exceptions import (
    DiaFueraDeDuracionError,
    PlanNoEncontradoError,
)
from plan_nutricional.domain.model import EstadoPlan
from plan_nutricional.domain.exceptions import PlanNoModificableError


async def test_agregar_dia_valido_devuelve_el_dia_y_persiste_el_plan(
    plan_repo_mock, construir_plan
):
    # Arrange — el mock devuelve el plan que decidimos, sin tocar la base de datos
    plan = construir_plan(dias_duracion=15)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarDiaUseCase(plan_repo_mock)

    # Act
    dia = await caso_de_uso.ejecutar(
        AgregarDiaCommand(plan_id=plan.id, numero_dia=3)
    )

    # Assert — se verifica el resultado y también CÓMO se usó la dependencia
    assert dia.numero_dia == 3
    assert plan.total_dias_agregados == 1
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_agregar_dia_en_plan_inexistente_lanza_error_y_no_persiste(plan_repo_mock):
    # Arrange — devolver None es la forma de simular "el plan no existe"
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = AgregarDiaUseCase(plan_repo_mock)
    plan_id = uuid4()

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(AgregarDiaCommand(plan_id=plan_id, numero_dia=1))

    # El caso de uso debe cortar antes de intentar guardar nada
    plan_repo_mock.guardar.assert_not_awaited()


async def test_agregar_dia_fuera_de_duracion_propaga_el_error_del_dominio(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias_duracion=15)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarDiaUseCase(plan_repo_mock)

    # Act / Assert — la regla la impone el agregado, no el caso de uso
    with pytest.raises(DiaFueraDeDuracionError):
        await caso_de_uso.ejecutar(AgregarDiaCommand(plan_id=plan.id, numero_dia=99))

    plan_repo_mock.guardar.assert_not_awaited()


async def test_agregar_dia_en_plan_finalizado_no_persiste(plan_repo_mock, construir_plan):
    # Arrange
    plan = construir_plan(estado=EstadoPlan.FINALIZADO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarDiaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoModificableError):
        await caso_de_uso.ejecutar(AgregarDiaCommand(plan_id=plan.id, numero_dia=1))

    plan_repo_mock.guardar.assert_not_awaited()


async def test_el_mock_con_spec_rechaza_metodos_que_no_existen_en_el_puerto(
    plan_repo_mock,
):
    """Demuestra por qué `spec=PlanNutricionalRepository` es obligatorio.

    Con `spec`, el mock solo acepta los métodos que declara el puerto. Sin él,
    cualquier método mal escrito devolvería otro mock y el test pasaría en verde
    ocultando el error.
    """
    # Act / Assert — método inexistente en el puerto
    with pytest.raises(AttributeError):
        plan_repo_mock.obtener_por_idd
