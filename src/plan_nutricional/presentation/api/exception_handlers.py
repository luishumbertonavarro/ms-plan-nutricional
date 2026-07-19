from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from plan_nutricional.domain.exceptions import (
    DiaDuplicadoError,
    DiaFueraDeDuracionError,
    DiaNoEncontradoError,
    PlanNoEncontradoError,
    PlanNoModificableError,
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


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PlanNoEncontradoError)
    async def plan_no_encontrado_handler(request: Request, exc: PlanNoEncontradoError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "PLAN_NO_ENCONTRADO"},
        )

    @app.exception_handler(DiaNoEncontradoError)
    async def dia_no_encontrado_handler(request: Request, exc: DiaNoEncontradoError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "DIA_NO_ENCONTRADO"},
        )

    @app.exception_handler(TiempoComidaNoEncontradoError)
    async def tiempo_comida_no_encontrado_handler(
        request: Request, exc: TiempoComidaNoEncontradoError
    ):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "TIEMPO_COMIDA_NO_ENCONTRADO"},
        )

    @app.exception_handler(RecetaNoEncontradaError)
    async def receta_no_encontrada_handler(request: Request, exc: RecetaNoEncontradaError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "RECETA_NO_ENCONTRADA"},
        )

    @app.exception_handler(PlanNoModificableError)
    async def plan_no_modificable_handler(request: Request, exc: PlanNoModificableError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "PLAN_NO_MODIFICABLE"},
        )

    @app.exception_handler(TransicionEstadoInvalidaError)
    async def transicion_estado_invalida_handler(
        request: Request, exc: TransicionEstadoInvalidaError
    ):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "TRANSICION_ESTADO_INVALIDA"},
        )

    @app.exception_handler(DiaDuplicadoError)
    async def dia_duplicado_handler(request: Request, exc: DiaDuplicadoError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "DIA_DUPLICADO"},
        )

    @app.exception_handler(TiempoComidaDuplicadoError)
    async def tiempo_comida_duplicado_handler(request: Request, exc: TiempoComidaDuplicadoError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "TIEMPO_COMIDA_DUPLICADO"},
        )

    @app.exception_handler(RecetaDuplicadaError)
    async def receta_duplicada_handler(request: Request, exc: RecetaDuplicadaError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "RECETA_DUPLICADA"},
        )

    @app.exception_handler(DiaFueraDeDuracionError)
    async def dia_fuera_de_duracion_handler(request: Request, exc: DiaFueraDeDuracionError):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "tipo": "DIA_FUERA_DE_DURACION"},
        )

    @app.exception_handler(RecetaCatalogoNoEncontradaError)
    async def receta_catalogo_no_encontrada_handler(
        request: Request, exc: RecetaCatalogoNoEncontradaError
    ):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "RECETA_CATALOGO_NO_ENCONTRADA"},
        )

    @app.exception_handler(RecetaCatalogoInactivaError)
    async def receta_catalogo_inactiva_handler(request: Request, exc: RecetaCatalogoInactivaError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "RECETA_CATALOGO_INACTIVA"},
        )

    @app.exception_handler(PlantillaNoEncontradaError)
    async def plantilla_no_encontrada_handler(request: Request, exc: PlantillaNoEncontradaError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "PLANTILLA_NO_ENCONTRADA"},
        )

    @app.exception_handler(PlantillaDiaNoEncontradoError)
    async def plantilla_dia_no_encontrado_handler(
        request: Request, exc: PlantillaDiaNoEncontradoError
    ):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "PLANTILLA_DIA_NO_ENCONTRADO"},
        )

    @app.exception_handler(PlantillaTiempoComidaNoEncontradoError)
    async def plantilla_tiempo_comida_no_encontrado_handler(
        request: Request, exc: PlantillaTiempoComidaNoEncontradoError
    ):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "PLANTILLA_TIEMPO_COMIDA_NO_ENCONTRADO"},
        )

    @app.exception_handler(PlantillaRecetaNoEncontradaError)
    async def plantilla_receta_no_encontrada_handler(
        request: Request, exc: PlantillaRecetaNoEncontradaError
    ):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "tipo": "PLANTILLA_RECETA_NO_ENCONTRADA"},
        )

    @app.exception_handler(PlantillaDiaDuplicadoError)
    async def plantilla_dia_duplicado_handler(request: Request, exc: PlantillaDiaDuplicadoError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "PLANTILLA_DIA_DUPLICADO"},
        )

    @app.exception_handler(PlantillaTiempoComidaDuplicadoError)
    async def plantilla_tiempo_comida_duplicado_handler(
        request: Request, exc: PlantillaTiempoComidaDuplicadoError
    ):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "tipo": "PLANTILLA_TIEMPO_COMIDA_DUPLICADO"},
        )

    @app.exception_handler(PlantillaDiaFueraDeDuracionError)
    async def plantilla_dia_fuera_de_duracion_handler(
        request: Request, exc: PlantillaDiaFueraDeDuracionError
    ):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "tipo": "PLANTILLA_DIA_FUERA_DE_DURACION"},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "tipo": "VALOR_INVALIDO"},
        )
