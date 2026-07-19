from dataclasses import dataclass
from uuid import UUID, uuid4

from plan_nutricional.domain.model.value_objects import Porcion


@dataclass
class Receta:
    """Preparación culinaria asignada a un tiempo de comida. Posee una Porcion (VO)."""

    id: UUID
    tiempo_comida_id: UUID
    nombre: str
    descripcion: str
    instrucciones: str
    porcion: Porcion

    @classmethod
    def crear(
        cls,
        tiempo_comida_id: UUID,
        nombre: str,
        descripcion: str,
        instrucciones: str,
        porcion: Porcion,
    ) -> "Receta":
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la receta no puede estar vacío.")
        return cls(
            id=uuid4(),
            tiempo_comida_id=tiempo_comida_id,
            nombre=nombre,
            descripcion=descripcion,
            instrucciones=instrucciones,
            porcion=porcion,
        )

    def cambiar_porcion(self, nueva_porcion: Porcion) -> None:
        self.porcion = nueva_porcion
