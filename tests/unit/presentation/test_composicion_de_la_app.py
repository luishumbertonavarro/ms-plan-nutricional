"""Pruebas del cableado de la aplicación FastAPI.

Estas pruebas afirman **cómo está compuesto el microservicio**, no qué hace cada
endpoint: que los tres routers están montados, que el contrato OpenAPI se genera
con todas las rutas declaradas, que las dependencias de repositorio anuncian el
*puerto* del dominio (y no la implementación concreta) y que la fábrica de
sesiones apunta a la base configurada.

**No necesitan PostgreSQL.** `create_async_engine` no abre ninguna conexión al
construirse, `Settings` trae valores por defecto y el `lifespan` solo se ejecuta
cuando arranca un servidor. Importar la app es, por tanto, una operación pura.

Qué NO cubren, a propósito: el cuerpo de los endpoints y el SQL de los
repositorios. Eso exige una petición real contra una base real y vive en
`tests/integration/`.
"""

import inspect

from fastapi import FastAPI
from fastapi.routing import APIRoute

from plan_nutricional.domain.repositories import (
    PlanNutricionalRepository,
    PlantillaPlanRepository,
    RecetaCatalogoRepository,
)
from plan_nutricional.infrastructure.config import settings
from plan_nutricional.infrastructure.persistence.database import (
    AsyncSessionFactory,
    engine,
)
from plan_nutricional.presentation.api.main import app
from plan_nutricional.presentation.api.routers import catalogo_recetas, planes, plantillas

# Una ruta de cada router, para comprobar que los tres están montados.
RUTAS_REPRESENTATIVAS = [
    "/planes",
    "/planes/desde-plantilla",
    "/planes/{plan_id}",
    "/planes/{plan_id}/dias/{numero_dia}/tiempos/{tipo}/recetas",
    "/catalogo-recetas",
    "/catalogo-recetas/{receta_catalogo_id}",
    "/catalogo-recetas/{receta_catalogo_id}/activar",
    "/plantillas",
    "/plantillas/{plantilla_id}",
    "/plantillas/{plantilla_id}/dias/{numero_dia}/tiempos/{tipo}/recetas",
]


def _rutas_de(aplicacion: FastAPI) -> set[str]:
    return {r.path for r in aplicacion.routes if isinstance(r, APIRoute)}


def test_la_app_monta_los_routers_de_planes_catalogo_y_plantillas():
    # Arrange / Act
    prefijos = {r.path.split("/")[1] for r in app.routes if isinstance(r, APIRoute)}

    # Assert — los tres bounded-context endpoints del microservicio
    assert {"planes", "catalogo-recetas", "plantillas"} <= prefijos


def test_la_app_declara_todas_las_rutas_representativas_de_los_tres_routers():
    # Arrange / Act
    rutas = _rutas_de(app)

    # Assert
    faltantes = [ruta for ruta in RUTAS_REPRESENTATIVAS if ruta not in rutas]
    assert faltantes == [], f"Rutas no montadas: {faltantes}"


def test_el_contrato_openapi_se_genera_e_incluye_las_rutas_publicadas():
    # Arrange / Act — generar el esquema ejercita todos los modelos de respuesta
    esquema = app.openapi()

    # Assert
    assert esquema["info"]["title"] == "ms-plan-nutricional — NUR-TRICENTER"
    for ruta in RUTAS_REPRESENTATIVAS:
        assert ruta in esquema["paths"], f"{ruta} no aparece en el OpenAPI"
    # Los esquemas de respuesta se publican para que el cliente los consuma
    componentes = esquema["components"]["schemas"]
    assert {"PlanResponse", "RecetaCatalogoResponse", "PlantillaResponse"} <= set(
        componentes
    )


def test_cada_router_inyecta_el_puerto_del_dominio_y_no_la_implementacion():
    """Protege la inversión de dependencias en el punto donde es fácil romperla.

    Si alguien anotara `-> PlanNutricionalRepositoryImpl`, la capa de
    presentación pasaría a depender de SQLAlchemy y la arquitectura dejaría de
    sostenerse. El tipo de retorno declarado es lo que documenta esa frontera.
    """
    # Arrange
    proveedores = [
        (planes._get_repo, PlanNutricionalRepository),
        (planes._get_catalogo_repo, RecetaCatalogoRepository),
        (planes._get_plantilla_repo, PlantillaPlanRepository),
        (catalogo_recetas._get_repo, RecetaCatalogoRepository),
        (plantillas._get_repo, PlantillaPlanRepository),
        (plantillas._get_catalogo_repo, RecetaCatalogoRepository),
    ]

    # Act / Assert
    for proveedor, puerto_esperado in proveedores:
        anotacion = inspect.signature(proveedor).return_annotation
        assert anotacion is puerto_esperado, (
            f"{proveedor.__module__}.{proveedor.__name__} debería devolver "
            f"{puerto_esperado.__name__} y declara {anotacion}"
        )


def test_la_fabrica_de_sesiones_apunta_a_la_base_de_datos_configurada():
    # Arrange / Act — construir el engine no abre ninguna conexión
    url = engine.url.render_as_string(hide_password=False)

    # Assert
    assert url == settings.database_url
    assert url.startswith("postgresql+asyncpg://")
    assert AsyncSessionFactory.kw["bind"] is engine
    # `expire_on_commit=False` es lo que permite leer el agregado tras el commit
    assert AsyncSessionFactory.kw["expire_on_commit"] is False
