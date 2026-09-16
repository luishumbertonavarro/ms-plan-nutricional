"""Cliente HTTP de `app-paciente`, el consumer simulado de ms-plan-nutricional.

Representa la app móvil del paciente (HU-18: "consultar mi plan actual"). En un
sistema real viviría en el repositorio de la app; aquí se incluye para que el
contrato se genere a partir de **código cliente real**, no de una petición
escrita a mano en el test.
"""
from uuid import UUID

import httpx


class PlanNoEncontrado(Exception):
    """ms-plan-nutricional respondió 404 para el plan pedido."""


class ClientePlanes:
    def __init__(self, base_url: str) -> None:
        self._base_url = str(base_url).rstrip("/")

    async def obtener_plan(self, plan_id: UUID) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            respuesta = await client.get(f"/planes/{plan_id}", headers={"Accept": "application/json"})
        if respuesta.status_code == 404:
            raise PlanNoEncontrado(str(plan_id))
        respuesta.raise_for_status()
        return respuesta.json()

    async def obtener_planes_paciente(self, paciente_id: UUID) -> list[dict]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            respuesta = await client.get(
                f"/planes/paciente/{paciente_id}", headers={"Accept": "application/json"}
            )
        respuesta.raise_for_status()
        return respuesta.json()
