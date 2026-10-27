"""Reglas de filtrado de los manejadores que no necesitan persistencia."""
from plan_nutricional.infrastructure.messaging.manejadores import MANEJADORES, servicio_contratado


def test_el_servicio_escucha_los_eventos_de_contratos_acordados_por_el_grupo():
    # Act / Assert
    assert set(MANEJADORES) == {"servicio.contratado", "contrato.cancelado"}


async def test_servicio_contratado_que_no_es_asesoramiento_se_ignora():
    # Arrange — sin sesión: si intentara persistir, el test fallaría
    payload = {"contratoId": "c1", "pacienteId": "p1", "tipoServicio": "CATERING"}

    # Act / Assert
    await servicio_contratado(None, payload)
