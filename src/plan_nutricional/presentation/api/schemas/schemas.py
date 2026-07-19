from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from plan_nutricional.domain.model.enums import EstadoPlan, TipoTiempoComida


# ---- Shared ----

class NecesidadNutricionalRequest(BaseModel):
    calorias: Decimal
    proteinas: Decimal
    grasas: Decimal
    carbohidratos: Decimal


class NecesidadNutricionalResponse(BaseModel):
    calorias: Decimal
    proteinas: Decimal
    grasas: Decimal
    carbohidratos: Decimal


# ---- Recetas ----

class AgregarRecetaRequest(BaseModel):
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str


class RecetaResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str


# ---- Tiempos de comida ----

class AgregarTiempoComidaRequest(BaseModel):
    tipo: TipoTiempoComida


class TiempoComidaResponse(BaseModel):
    id: UUID
    tipo: TipoTiempoComida
    recetas: list[RecetaResponse]


# ---- Días ----

class AgregarDiaRequest(BaseModel):
    numero_dia: int


class PlanDiaResponse(BaseModel):
    id: UUID
    numero_dia: int
    tiempos_comida: list[TiempoComidaResponse]


# ---- Planes ----

class CrearPlanRequest(BaseModel):
    paciente_id: UUID
    fecha_inicio: date
    duracion_dias: int
    necesidad: NecesidadNutricionalRequest
    recomendacion_texto: str


class PlanResponse(BaseModel):
    id: UUID
    paciente_id: UUID
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoPlan
    duracion_dias: int
    necesidad: NecesidadNutricionalResponse
    recomendacion_texto: str
    dias: list[PlanDiaResponse]


class ModificarRecomendacionRequest(BaseModel):
    texto: str


class CambiarEstadoPlanRequest(BaseModel):
    nuevo_estado: EstadoPlan


class AgregarRecetaDesdeCatalogoRequest(BaseModel):
    receta_catalogo_id: UUID
    cantidad: Decimal | None = None
    unidad: str | None = None


# ---- Catálogo de recetas ----

class CrearRecetaCatalogoRequest(BaseModel):
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str


class ActualizarRecetaCatalogoRequest(BaseModel):
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str


class RecetaCatalogoResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: str
    instrucciones: str
    cantidad: Decimal
    unidad: str
    activa: bool


# ---- Plantillas de plan ----

class CrearPlantillaRequest(BaseModel):
    nombre: str
    descripcion: str
    duracion_dias: int


class AgregarPlantillaDiaRequest(BaseModel):
    numero_dia: int


class AgregarPlantillaTiempoComidaRequest(BaseModel):
    tipo: TipoTiempoComida


class AgregarPlantillaRecetaRequest(BaseModel):
    receta_catalogo_id: UUID
    cantidad: Decimal
    unidad: str


class PlantillaRecetaResponse(BaseModel):
    id: UUID
    receta_catalogo_id: UUID
    cantidad: Decimal
    unidad: str


class PlantillaTiempoComidaResponse(BaseModel):
    id: UUID
    tipo: TipoTiempoComida
    recetas: list[PlantillaRecetaResponse]


class PlantillaDiaResponse(BaseModel):
    id: UUID
    numero_dia: int
    tiempos_comida: list[PlantillaTiempoComidaResponse]


class PlantillaResponse(BaseModel):
    id: UUID
    nombre: str
    descripcion: str
    duracion_dias: int
    dias: list[PlantillaDiaResponse]


class CrearPlanDesdePlantillaRequest(BaseModel):
    plantilla_id: UUID
    paciente_id: UUID
    fecha_inicio: date
    necesidad: NecesidadNutricionalRequest
    recomendacion_texto: str
