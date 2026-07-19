from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from plan_nutricional.domain.model.enums import EstadoPlan, TipoTiempoComida


@dataclass(frozen=True)
class NecesidadNutricionalData:
    calorias: Decimal
    proteinas: Decimal
    grasas: Decimal
    carbohidratos: Decimal


@dataclass(frozen=True)
class CrearPlanCommand:
    paciente_id: UUID
    fecha_inicio: date
    duracion_dias: int
    necesidad: NecesidadNutricionalData
    recomendacion_texto: str


@dataclass(frozen=True)
class AgregarDiaCommand:
    plan_id: UUID
    numero_dia: int


@dataclass(frozen=True)
class EliminarDiaCommand:
    plan_id: UUID
    numero_dia: int


@dataclass(frozen=True)
class AgregarTiempoComidaCommand:
    plan_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida


@dataclass(frozen=True)
class EliminarTiempoComidaCommand:
    plan_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida


@dataclass(frozen=True)
class AgregarRecetaCommand:
    plan_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str


@dataclass(frozen=True)
class EliminarRecetaCommand:
    plan_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida
    receta_id: UUID


@dataclass(frozen=True)
class ModificarRecomendacionCommand:
    plan_id: UUID
    texto: str


@dataclass(frozen=True)
class CambiarEstadoPlanCommand:
    plan_id: UUID
    nuevo_estado: EstadoPlan


@dataclass(frozen=True)
class AgregarRecetaDesdeCatalogoCommand:
    plan_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida
    receta_catalogo_id: UUID
    cantidad: Decimal | None = None
    unidad: str | None = None


# ---------------------------------------------------------------------------
# Catálogo de recetas
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrearRecetaCatalogoCommand:
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str


@dataclass(frozen=True)
class ActualizarRecetaCatalogoCommand:
    receta_catalogo_id: UUID
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str


@dataclass(frozen=True)
class CambiarEstadoRecetaCatalogoCommand:
    receta_catalogo_id: UUID
    activa: bool


# ---------------------------------------------------------------------------
# Plantillas de plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrearPlantillaCommand:
    nombre: str
    descripcion: str
    duracion_dias: int


@dataclass(frozen=True)
class AgregarPlantillaDiaCommand:
    plantilla_id: UUID
    numero_dia: int


@dataclass(frozen=True)
class EliminarPlantillaDiaCommand:
    plantilla_id: UUID
    numero_dia: int


@dataclass(frozen=True)
class AgregarPlantillaTiempoComidaCommand:
    plantilla_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida


@dataclass(frozen=True)
class EliminarPlantillaTiempoComidaCommand:
    plantilla_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida


@dataclass(frozen=True)
class AgregarPlantillaRecetaCommand:
    plantilla_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida
    receta_catalogo_id: UUID
    cantidad: Decimal
    unidad: str


@dataclass(frozen=True)
class EliminarPlantillaRecetaCommand:
    plantilla_id: UUID
    numero_dia: int
    tipo: TipoTiempoComida
    receta_id: UUID


@dataclass(frozen=True)
class CrearPlanDesdePlantillaCommand:
    plantilla_id: UUID
    paciente_id: UUID
    fecha_inicio: date
    necesidad: NecesidadNutricionalData
    recomendacion_texto: str
