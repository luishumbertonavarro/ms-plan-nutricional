from enum import Enum


class EstadoPlan(str, Enum):
    ACTIVO = "ACTIVO"
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"


class TipoTiempoComida(str, Enum):
    DESAYUNO = "DESAYUNO"
    MEDIA_MANANA = "MEDIA_MANANA"
    ALMUERZO = "ALMUERZO"
    MERIENDA = "MERIENDA"
    CENA = "CENA"
    MEDIA_NOCHE = "MEDIA_NOCHE"
