"""Pruebas de la traducción de errores de dominio a respuestas HTTP.

`register_exception_handlers(app)` registra veintiún manejadores que convierten
cada excepción del dominio en un `JSONResponse` con `status_code` y un código
`tipo` estable que el cliente puede interpretar sin parsear el mensaje.

**Por qué es una prueba unitaria y no de integración.** Los manejadores son
closures, pero Starlette las deja accesibles en `app.exception_handlers`, y
ninguna usa el `request`. Se pueden invocar directamente sobre un `FastAPI()`
desnudo: sin rutas, sin cliente HTTP y sin base de datos. Lo que se prueba aquí
es **la tabla de traducción**. Que FastAPI enrute de verdad una excepción hasta
su manejador durante una petición real lo cubre
`tests/integration/test_planes_api_flujo_incorrecto.py`, que es otra cosa.
"""

import json
from uuid import uuid4

import pytest
from fastapi import FastAPI

from plan_nutricional.domain import exceptions as excepciones_de_dominio
from plan_nutricional.domain.exceptions import (
    DiaDuplicadoError,
    DiaFueraDeDuracionError,
    DiaNoEncontradoError,
    PacienteNoEncontradoError,
    PlanNoEncontradoError,
    PlanNoModificableError,
    PlanNutricionalDomainError,
    PlantillaDiaDuplicadoError,
    PlantillaDiaFueraDeDuracionError,
    PlantillaDiaNoEncontradoError,
    PlantillaNoEncontradaError,
    PlantillaRecetaNoEncontradaError,
    PlantillaTiempoComidaDuplicadoError,
    PlantillaTiempoComidaNoEncontradoError,
    RecetaCatalogoInactivaError,
    RecetaCatalogoNoEncontradaError,
    RecetaDuplicadaError,
    RecetaNoEncontradaError,
    TiempoComidaDuplicadoError,
    TiempoComidaNoEncontradoError,
    TransicionEstadoInvalidaError,
)
from plan_nutricional.domain.model import EstadoPlan, TipoTiempoComida
from plan_nutricional.presentation.api.exception_handlers import (
    register_exception_handlers,
)

# Tabla de traducción: (excepción ya construida, status HTTP, código `tipo`).
# Es el contrato público del microservicio frente a sus clientes.
CASOS = [
    # 404 — el recurso no existe
    (PlanNoEncontradoError(uuid4()), 404, "PLAN_NO_ENCONTRADO"),
    (PacienteNoEncontradoError(uuid4()), 404, "PACIENTE_NO_ENCONTRADO"),
    (DiaNoEncontradoError(3), 404, "DIA_NO_ENCONTRADO"),
    (
        TiempoComidaNoEncontradoError(TipoTiempoComida.DESAYUNO),
        404,
        "TIEMPO_COMIDA_NO_ENCONTRADO",
    ),
    (RecetaNoEncontradaError(uuid4()), 404, "RECETA_NO_ENCONTRADA"),
    (
        RecetaCatalogoNoEncontradaError(uuid4()),
        404,
        "RECETA_CATALOGO_NO_ENCONTRADA",
    ),
    (PlantillaNoEncontradaError(uuid4()), 404, "PLANTILLA_NO_ENCONTRADA"),
    (PlantillaDiaNoEncontradoError(2), 404, "PLANTILLA_DIA_NO_ENCONTRADO"),
    (
        PlantillaTiempoComidaNoEncontradoError(TipoTiempoComida.CENA),
        404,
        "PLANTILLA_TIEMPO_COMIDA_NO_ENCONTRADO",
    ),
    (
        PlantillaRecetaNoEncontradaError(uuid4()),
        404,
        "PLANTILLA_RECETA_NO_ENCONTRADA",
    ),
    # 409 — conflicto con el estado actual del recurso
    (PlanNoModificableError(EstadoPlan.FINALIZADO), 409, "PLAN_NO_MODIFICABLE"),
    (
        TransicionEstadoInvalidaError(EstadoPlan.FINALIZADO, EstadoPlan.ACTIVO),
        409,
        "TRANSICION_ESTADO_INVALIDA",
    ),
    (DiaDuplicadoError(1), 409, "DIA_DUPLICADO"),
    (
        TiempoComidaDuplicadoError(TipoTiempoComida.DESAYUNO),
        409,
        "TIEMPO_COMIDA_DUPLICADO",
    ),
    (RecetaDuplicadaError("Avena con frutas"), 409, "RECETA_DUPLICADA"),
    (RecetaCatalogoInactivaError(uuid4()), 409, "RECETA_CATALOGO_INACTIVA"),
    (PlantillaDiaDuplicadoError(1), 409, "PLANTILLA_DIA_DUPLICADO"),
    (
        PlantillaTiempoComidaDuplicadoError(TipoTiempoComida.ALMUERZO),
        409,
        "PLANTILLA_TIEMPO_COMIDA_DUPLICADO",
    ),
    # 422 — la petición es coherente pero viola una invariante
    (DiaFueraDeDuracionError(99, 15), 422, "DIA_FUERA_DE_DURACION"),
    (
        PlantillaDiaFueraDeDuracionError(99, 15),
        422,
        "PLANTILLA_DIA_FUERA_DE_DURACION",
    ),
    (ValueError("La duración del plan debe ser 15 o 30 días."), 422, "VALOR_INVALIDO"),
]


@pytest.fixture
def app_con_manejadores() -> FastAPI:
    """App de FastAPI sin rutas, solo con los manejadores registrados."""
    app = FastAPI()
    register_exception_handlers(app)
    return app


@pytest.mark.parametrize(
    ("excepcion", "status_esperado", "tipo_esperado"),
    CASOS,
    ids=[tipo for _, _, tipo in CASOS],
)
async def test_cada_excepcion_de_dominio_se_traduce_al_status_y_tipo_esperados(
    app_con_manejadores, excepcion, status_esperado, tipo_esperado
):
    # Arrange
    manejador = app_con_manejadores.exception_handlers[type(excepcion)]

    # Act — los manejadores no usan el `request`, por eso se pasa None
    respuesta = await manejador(None, excepcion)

    # Assert
    cuerpo = json.loads(respuesta.body)
    assert respuesta.status_code == status_esperado
    assert cuerpo["tipo"] == tipo_esperado
    assert cuerpo["detail"] == str(excepcion)


async def test_el_detalle_de_la_respuesta_reproduce_el_mensaje_del_dominio(
    app_con_manejadores,
):
    # Arrange — el mensaje lo escribe el dominio; la capa HTTP no lo reescribe
    plan_id = uuid4()
    excepcion = PlanNoEncontradoError(plan_id)
    manejador = app_con_manejadores.exception_handlers[PlanNoEncontradoError]

    # Act
    respuesta = await manejador(None, excepcion)

    # Assert
    cuerpo = json.loads(respuesta.body)
    assert str(plan_id) in cuerpo["detail"]


def test_toda_excepcion_de_dominio_declarada_tiene_un_manejador_registrado(
    app_con_manejadores,
):
    """Red de seguridad: una excepción nueva sin manejador acabaría en un 500.

    Recorre las excepciones que exporta `domain.exceptions` y exige que cada una
    esté registrada. Si mañana se añade una y se olvida el manejador, este test
    lo dice antes de que un cliente reciba un error opaco.
    """
    # Arrange
    declaradas = {
        getattr(excepciones_de_dominio, nombre)
        for nombre in excepciones_de_dominio.__all__
    } - {PlanNutricionalDomainError}

    # Act
    registradas = set(app_con_manejadores.exception_handlers)

    # Assert
    assert declaradas <= registradas, (
        "Sin manejador HTTP: "
        f"{sorted(e.__name__ for e in declaradas - registradas)}"
    )


def test_los_casos_probados_cubren_todas_las_excepciones_con_manejador(
    app_con_manejadores,
):
    """Evita que la tabla `CASOS` se quede atrás respecto a los manejadores."""
    # Arrange
    probadas = {type(excepcion) for excepcion, _, _ in CASOS}
    registradas = {
        clase
        for clase in app_con_manejadores.exception_handlers
        if isinstance(clase, type)
        and issubclass(clase, (PlanNutricionalDomainError, ValueError))
    }

    # Act / Assert
    assert registradas == probadas
