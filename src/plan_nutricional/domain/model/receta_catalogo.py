from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from plan_nutricional.domain.model.value_objects import Porcion


@dataclass
class RecetaCatalogo:
    """Receta reutilizable del catálogo, independiente de cualquier plan o plantilla.

    Sirve como fuente para poblar recetas en planes de pacientes y en plantillas de plan.
    """

    id: UUID
    nombre: str
    descripcion: str
    instrucciones: str
    porcion_default: Porcion
    activa: bool

    @classmethod
    def crear(
        cls,
        nombre: str,
        descripcion: str,
        instrucciones: str,
        cantidad: Decimal,
        unidad: str,
    ) -> "RecetaCatalogo":
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la receta no puede estar vacío.")
        return cls(
            id=uuid4(),
            nombre=nombre,
            descripcion=descripcion,
            instrucciones=instrucciones,
            porcion_default=Porcion(cantidad=cantidad, unidad=unidad),
            activa=True,
        )

    def actualizar(
        self,
        nombre: str,
        descripcion: str,
        instrucciones: str,
        cantidad: Decimal,
        unidad: str,
    ) -> None:
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la receta no puede estar vacío.")
        self.nombre = nombre
        self.descripcion = descripcion
        self.instrucciones = instrucciones
        self.porcion_default = Porcion(cantidad=cantidad, unidad=unidad)

    def activar(self) -> None:
        self.activa = True

    def desactivar(self) -> None:
        self.activa = False
