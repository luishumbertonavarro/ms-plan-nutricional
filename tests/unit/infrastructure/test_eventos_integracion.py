"""Los payloads respetan los contratos de Eventos_Integracion_NUR-TRICENTER.docx (sección 2)."""
from decimal import Decimal

from plan_nutricional.domain.model import TipoTiempoComida
from plan_nutricional.infrastructure.messaging.eventos_integracion import a_mensaje


def test_plan_creado_se_publica_en_plan_nutricional_creado_con_el_contrato(construir_plan):
    # Arrange
    plan = construir_plan()
    evento = plan.extraer_eventos()[0]

    # Act
    mensaje = a_mensaje(evento, plan)

    # Assert
    assert mensaje.tipo == "PlanNutricionalCreado"
    assert mensaje.routing_key == "plan_nutricional.creado"
    assert mensaje.payload == {
        "plan_id": str(plan.id),
        "paciente_id": str(plan.paciente_id),
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-01-15",
        "duracion_dias": 15,
        "estado": "ACTIVO",
        "plantilla_origen_id": None,
        "necesidad": {
            "calorias": "2000.00",
            "proteinas": "120.00",
            "grasas": "60.00",
            "carbohidratos": "250.00",
        },
    }
    assert mensaje.ocurrido_en == evento.ocurrido_en


def test_plan_actualizado_lleva_el_plan_completo_con_la_fecha_de_cada_dia(construir_plan):
    # Arrange
    plan = construir_plan()
    plan.extraer_eventos()
    plan.agregar_dia(3)
    plan.agregar_tiempo_comida(3, TipoTiempoComida.DESAYUNO)
    receta = plan.agregar_receta(
        3, TipoTiempoComida.DESAYUNO, "Avena con frutas", "d", "Cocer la avena",
        Decimal("250"), "gr",
    )

    # Act
    mensaje = a_mensaje(plan.extraer_eventos()[0], plan)

    # Assert
    assert mensaje.routing_key == "plan_nutricional.actualizado"
    assert mensaje.payload["dias"] == [
        {
            "numero_dia": 3,
            "fecha": "2026-01-03",
            "tiempos_comida": [
                {
                    "tipo": "DESAYUNO",
                    "recetas": [
                        {
                            "receta_id": str(receta.id),
                            "nombre": "Avena con frutas",
                            "instrucciones": "Cocer la avena",
                            "cantidad": "250.00",
                            "unidad": "gr",
                        }
                    ],
                }
            ],
        }
    ]


def test_plan_finalizado_se_publica_con_su_fecha_fin(construir_plan):
    # Arrange
    plan = construir_plan()
    plan.extraer_eventos()
    plan.finalizar()

    # Act
    mensaje = a_mensaje(plan.extraer_eventos()[0], plan)

    # Assert
    assert mensaje.routing_key == "plan_nutricional.finalizado"
    assert mensaje.payload == {
        "plan_id": str(plan.id),
        "paciente_id": str(plan.paciente_id),
        "fecha_fin": "2026-01-15",
    }


def test_plan_cancelado_se_publica_con_la_fecha_de_cancelacion(construir_plan):
    # Arrange
    plan = construir_plan()
    plan.extraer_eventos()
    plan.cancelar()
    evento = plan.extraer_eventos()[0]

    # Act
    mensaje = a_mensaje(evento, plan)

    # Assert
    assert mensaje.routing_key == "plan_nutricional.cancelado"
    assert mensaje.payload["cancelado_el"] == evento.cancelado_el.isoformat()
