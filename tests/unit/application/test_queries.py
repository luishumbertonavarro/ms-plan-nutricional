"""Pruebas de los query handlers de `PlanNutricional` (lado *query* de CQRS).

Un query handler no tiene reglas de negocio: su único trabajo es delegar en el
puerto del repositorio y devolver lo que le den. Por eso lo que se verifica es
exactamente eso — **a qué método delega, con qué argumento y que no escribe
nada** — y no el contenido de los agregados, que ya cubren los tests de dominio.

Los tres handlers viven en el mismo módulo (`use_cases/queries.py`), así que el
espejo agrupa igual que el origen.
"""

from uuid import uuid4

from plan_nutricional.application.queries.queries import (
    ListarPlanesActivosQuery,
    ObtenerPlanesPacienteQuery,
    ObtenerPlanPorIdQuery,
)
from plan_nutricional.application.use_cases.queries import (
    ListarPlanesActivosHandler,
    ObtenerPlanesPacienteHandler,
    ObtenerPlanPorIdHandler,
)


async def test_obtener_un_plan_por_id_devuelve_el_plan_del_repositorio(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan()
    plan_repo_mock.obtener_por_id.return_value = plan
    handler = ObtenerPlanPorIdHandler(plan_repo_mock)

    # Act
    resultado = await handler.ejecutar(ObtenerPlanPorIdQuery(plan_id=plan.id))

    # Assert
    assert resultado is plan
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_not_awaited()


async def test_obtener_un_plan_por_id_inexistente_devuelve_none_sin_lanzar_error(
    plan_repo_mock,
):
    # Arrange — traducir el None a un 404 es tarea del router, no del handler
    plan_repo_mock.obtener_por_id.return_value = None
    handler = ObtenerPlanPorIdHandler(plan_repo_mock)
    plan_id = uuid4()

    # Act
    resultado = await handler.ejecutar(ObtenerPlanPorIdQuery(plan_id=plan_id))

    # Assert
    assert resultado is None
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan_id)


async def test_obtener_los_planes_de_un_paciente_delega_en_el_repositorio(
    plan_repo_mock, construir_plan
):
    # Arrange
    planes = [construir_plan(), construir_plan()]
    plan_repo_mock.obtener_por_paciente.return_value = planes
    handler = ObtenerPlanesPacienteHandler(plan_repo_mock)
    paciente_id = uuid4()

    # Act
    resultado = await handler.ejecutar(
        ObtenerPlanesPacienteQuery(paciente_id=paciente_id)
    )

    # Assert
    assert resultado == planes
    plan_repo_mock.obtener_por_paciente.assert_awaited_once_with(paciente_id)


async def test_obtener_los_planes_de_un_paciente_sin_planes_devuelve_lista_vacia(
    plan_repo_mock,
):
    # Arrange
    plan_repo_mock.obtener_por_paciente.return_value = []
    handler = ObtenerPlanesPacienteHandler(plan_repo_mock)

    # Act
    resultado = await handler.ejecutar(
        ObtenerPlanesPacienteQuery(paciente_id=uuid4())
    )

    # Assert
    assert resultado == []


async def test_listar_los_planes_activos_delega_en_listar_activos(
    plan_repo_mock, construir_plan
):
    # Arrange
    planes = [construir_plan()]
    plan_repo_mock.listar_activos.return_value = planes
    handler = ListarPlanesActivosHandler(plan_repo_mock)

    # Act
    resultado = await handler.ejecutar(ListarPlanesActivosQuery())

    # Assert — el filtro por estado lo aplica el repositorio, no el handler
    assert resultado == planes
    plan_repo_mock.listar_activos.assert_awaited_once_with()
    plan_repo_mock.obtener_por_paciente.assert_not_awaited()
