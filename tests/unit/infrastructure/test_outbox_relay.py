"""Partes puras del relay del outbox: cómo se arma el mensaje AMQP y su ciclo de vida sin broker."""
import json
from datetime import datetime, timezone
from uuid import uuid4

import aio_pika

from plan_nutricional.infrastructure.messaging.outbox_relay import OutboxRelay, _a_mensaje_amqp
from plan_nutricional.infrastructure.persistence.orm_models import OutboxORM


def test_mensaje_amqp_es_persistente_y_lleva_el_id_del_outbox_como_message_id():
    # Arrange
    fila = OutboxORM(
        id=uuid4(),
        tipo="PlanNutricionalCreado",
        routing_key="plan_nutricional.creado",
        payload={"plan_id": "p1", "nombre": "Ñandú"},
        ocurrido_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    # Act
    mensaje = _a_mensaje_amqp(fila)

    # Assert
    assert mensaje.message_id == str(fila.id)
    assert mensaje.type == "PlanNutricionalCreado"
    assert mensaje.content_type == "application/json"
    assert mensaje.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
    assert json.loads(mensaje.body) == {"plan_id": "p1", "nombre": "Ñandú"}


async def test_detener_sin_haber_iniciado_no_falla():
    # Arrange
    relay = OutboxRelay(None, "amqp://guest:guest@localhost/", "nurtricenter.events")

    # Act / Assert
    await relay.detener()


async def test_detener_cancela_la_tarea_del_relay():
    # Arrange
    relay = OutboxRelay(None, "amqp://guest:guest@localhost/", "nurtricenter.events")
    relay.iniciar()

    # Act — se detiene antes de la primera vuelta: no llega a tocar BD ni broker
    await relay.detener()

    # Assert
    assert relay._tarea.cancelled()
