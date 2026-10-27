"""Traduce eventos de dominio de PlanNutricional a mensajes de integración.

Contratos: Eventos_Integracion_NUR-TRICENTER.docx, sección 2. Convención del grupo:
exchange topic `nurtricenter.events`, routing key `entidad.participio` en minúsculas,
el payload viaja directo (sin sobre).
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from plan_nutricional.domain.model import PlanNutricional
from plan_nutricional.domain.model.eventos import (
    EventoDominio,
    PlanNutricionalActualizado,
    PlanNutricionalCancelado,
    PlanNutricionalCreado,
    PlanNutricionalFinalizado,
)


@dataclass(frozen=True)
class MensajeIntegracion:
    tipo: str
    routing_key: str
    payload: dict
    ocurrido_en: datetime


def _creado(plan: PlanNutricional) -> dict:
    return {
        "plan_id": str(plan.id),
        "paciente_id": str(plan.paciente_id),
        "fecha_inicio": plan.fecha_inicio.isoformat(),
        "fecha_fin": plan.fecha_fin.isoformat(),
        "duracion_dias": plan.duracion.dias,
        "estado": plan.estado.value,
        "plantilla_origen_id": None,
        "necesidad": {
            "calorias": f"{plan.necesidad.calorias:.2f}",
            "proteinas": f"{plan.necesidad.proteinas:.2f}",
            "grasas": f"{plan.necesidad.grasas:.2f}",
            "carbohidratos": f"{plan.necesidad.carbohidratos:.2f}",
        },
    }


def _actualizado(plan: PlanNutricional) -> dict:
    # Event-carried state transfer: el plan completo, para no depender del orden de los eventos.
    return {
        "plan_id": str(plan.id),
        "paciente_id": str(plan.paciente_id),
        "fecha_inicio": plan.fecha_inicio.isoformat(),
        "fecha_fin": plan.fecha_fin.isoformat(),
        "estado": plan.estado.value,
        "dias": [
            {
                "numero_dia": dia.numero_dia,
                "fecha": (plan.fecha_inicio + timedelta(days=dia.numero_dia - 1)).isoformat(),
                "tiempos_comida": [
                    {
                        "tipo": tiempo.tipo.value,
                        "recetas": [
                            {
                                "receta_id": str(receta.id),
                                "nombre": receta.nombre,
                                "instrucciones": receta.instrucciones,
                                "cantidad": f"{receta.porcion.cantidad:.2f}",
                                "unidad": receta.porcion.unidad,
                            }
                            for receta in tiempo.recetas
                        ],
                    }
                    for tiempo in dia.tiempos_comida
                ],
            }
            for dia in sorted(plan.dias, key=lambda d: d.numero_dia)
        ],
    }


def a_mensaje(evento: EventoDominio, plan: PlanNutricional) -> MensajeIntegracion:
    match evento:
        case PlanNutricionalCreado():
            tipo, routing_key, payload = "PlanNutricionalCreado", "plan_nutricional.creado", _creado(plan)
        case PlanNutricionalActualizado():
            tipo, routing_key, payload = (
                "PlanNutricionalActualizado", "plan_nutricional.actualizado", _actualizado(plan)
            )
        case PlanNutricionalFinalizado(fecha_fin=fecha_fin):
            tipo, routing_key = "PlanNutricionalFinalizado", "plan_nutricional.finalizado"
            payload = {
                "plan_id": str(plan.id),
                "paciente_id": str(plan.paciente_id),
                "fecha_fin": fecha_fin.isoformat(),
            }
        case PlanNutricionalCancelado(cancelado_el=cancelado_el):
            tipo, routing_key = "PlanNutricionalCancelado", "plan_nutricional.cancelado"
            payload = {
                "plan_id": str(plan.id),
                "paciente_id": str(plan.paciente_id),
                "cancelado_el": cancelado_el.isoformat(),
            }
        case _:
            raise ValueError(f"Evento sin contrato de integración: {type(evento).__name__}")
    return MensajeIntegracion(tipo, routing_key, payload, evento.ocurrido_en)
