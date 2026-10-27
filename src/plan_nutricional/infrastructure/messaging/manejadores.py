"""Reacciones de BC2 a los eventos de ms-contratos-facturacion (ver docx, sección 5.1).

- servicio.contratado (tipoServicio = ASESORAMIENTO): habilita el asesoramiento del paciente.
- contrato.cancelado: revoca el asesoramiento de ese contrato.

Por ahora solo se lleva la réplica local; la creación de planes no se bloquea con ella.
"""
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from plan_nutricional.infrastructure.messaging.consumidor import Manejador, campo
from plan_nutricional.infrastructure.persistence.orm_models import AsesoramientoHabilitadoORM

_ASESORAMIENTO = "ASESORAMIENTO"


async def servicio_contratado(session: AsyncSession, payload: dict) -> None:
    if campo(payload, "tipoServicio", "tipo_servicio") != _ASESORAMIENTO:
        return
    contrato_id = UUID(campo(payload, "contratoId", "contrato_id"))
    fecha_inicio = payload.get("fechaInicio") or payload.get("fecha_inicio")
    asesoramiento = await session.get(AsesoramientoHabilitadoORM, contrato_id)
    if asesoramiento is None:
        asesoramiento = AsesoramientoHabilitadoORM(contrato_id=contrato_id)
        session.add(asesoramiento)
    asesoramiento.paciente_id = UUID(campo(payload, "pacienteId", "paciente_id"))
    asesoramiento.fecha_inicio = date.fromisoformat(fecha_inicio[:10]) if fecha_inicio else None
    asesoramiento.activo = True


async def contrato_cancelado(session: AsyncSession, payload: dict) -> None:
    contrato_id = UUID(campo(payload, "contratoId", "contrato_id"))
    asesoramiento = await session.get(AsesoramientoHabilitadoORM, contrato_id)
    if asesoramiento is not None:
        asesoramiento.activo = False


MANEJADORES: dict[str, Manejador] = {
    "servicio.contratado": servicio_contratado,
    "contrato.cancelado": contrato_cancelado,
}
