from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class NecesidadNutricional:
    """Requerimientos calóricos y de macronutrientes del paciente. Ninguno puede ser negativo."""

    calorias: Decimal
    proteinas: Decimal
    grasas: Decimal
    carbohidratos: Decimal

    def __post_init__(self) -> None:
        for nombre, valor in (
            ("calorias", self.calorias),
            ("proteinas", self.proteinas),
            ("grasas", self.grasas),
            ("carbohidratos", self.carbohidratos),
        ):
            if valor < 0:
                raise ValueError(f"El valor de '{nombre}' no puede ser negativo: {valor}.")


@dataclass(frozen=True)
class DuracionPlan:
    """Duración del plan. Solo se permiten planes de 15 o 30 días."""

    VALORES_PERMITIDOS = (15, 30)

    dias: int

    def __post_init__(self) -> None:
        if self.dias not in self.VALORES_PERMITIDOS:
            raise ValueError(
                f"La duración del plan debe ser 15 o 30 días, se recibió: {self.dias}."
            )


@dataclass(frozen=True)
class RecomendacionNutricional:
    """Indicación del nutricionista que guía la composición del plan. No puede estar vacía."""

    texto: str

    def __post_init__(self) -> None:
        if not self.texto or not self.texto.strip():
            raise ValueError("La recomendación nutricional no puede estar vacía.")


@dataclass(frozen=True)
class Porcion:
    """Cantidad y unidad de una receta asignada al paciente. La cantidad debe ser mayor que cero."""

    cantidad: Decimal
    unidad: str

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise ValueError(f"La cantidad de la porción debe ser mayor que cero: {self.cantidad}.")
        if not self.unidad or not self.unidad.strip():
            raise ValueError("La unidad de la porción no puede estar vacía.")
