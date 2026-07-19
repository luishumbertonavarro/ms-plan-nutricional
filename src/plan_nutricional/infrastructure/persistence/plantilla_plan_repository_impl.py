from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from plan_nutricional.domain.model import (
    DuracionPlan,
    PlantillaDia,
    PlantillaPlan,
    PlantillaReceta,
    PlantillaTiempoComida,
    Porcion,
    TipoTiempoComida,
)
from plan_nutricional.domain.repositories import PlantillaPlanRepository
from plan_nutricional.infrastructure.persistence.orm_models import (
    PlantillaDiaORM,
    PlantillaPlanORM,
    PlantillaRecetaORM,
    PlantillaTiempoComidaORM,
)

_EAGER = [
    joinedload(PlantillaPlanORM.dias)
    .joinedload(PlantillaDiaORM.tiempos_comida)
    .joinedload(PlantillaTiempoComidaORM.recetas),
]


# ---------------------------------------------------------------------------
# ORM -> Domain
# ---------------------------------------------------------------------------

def _plantilla_receta_from_orm(row: PlantillaRecetaORM) -> PlantillaReceta:
    return PlantillaReceta(
        id=row.id,
        tiempo_comida_id=row.tiempo_comida_id,
        receta_catalogo_id=row.receta_catalogo_id,
        porcion=Porcion(cantidad=Decimal(str(row.porcion_cantidad)), unidad=row.porcion_unidad),
    )


def _plantilla_tiempo_comida_from_orm(row: PlantillaTiempoComidaORM) -> PlantillaTiempoComida:
    return PlantillaTiempoComida(
        id=row.id,
        plantilla_dia_id=row.plantilla_dia_id,
        tipo=TipoTiempoComida(row.tipo),
        _recetas=[_plantilla_receta_from_orm(r) for r in row.recetas],
    )


def _plantilla_dia_from_orm(row: PlantillaDiaORM) -> PlantillaDia:
    return PlantillaDia(
        id=row.id,
        plantilla_id=row.plantilla_id,
        numero_dia=row.numero_dia,
        _tiempos_comida=[_plantilla_tiempo_comida_from_orm(t) for t in row.tiempos_comida],
    )


def _plantilla_from_orm(row: PlantillaPlanORM) -> PlantillaPlan:
    return PlantillaPlan(
        id=row.id,
        nombre=row.nombre,
        descripcion=row.descripcion,
        duracion=DuracionPlan(dias=row.duracion_dias),
        dias=[_plantilla_dia_from_orm(d) for d in row.dias],
    )


# ---------------------------------------------------------------------------
# Domain -> ORM
# ---------------------------------------------------------------------------

def _plantilla_receta_to_orm(receta: PlantillaReceta) -> PlantillaRecetaORM:
    return PlantillaRecetaORM(
        id=receta.id,
        tiempo_comida_id=receta.tiempo_comida_id,
        receta_catalogo_id=receta.receta_catalogo_id,
        porcion_cantidad=receta.porcion.cantidad,
        porcion_unidad=receta.porcion.unidad,
    )


def _plantilla_tiempo_comida_to_orm(tiempo: PlantillaTiempoComida) -> PlantillaTiempoComidaORM:
    orm = PlantillaTiempoComidaORM(
        id=tiempo.id, plantilla_dia_id=tiempo.plantilla_dia_id, tipo=tiempo.tipo.value
    )
    orm.recetas = [_plantilla_receta_to_orm(r) for r in tiempo.recetas]
    return orm


def _plantilla_dia_to_orm(dia: PlantillaDia) -> PlantillaDiaORM:
    orm = PlantillaDiaORM(id=dia.id, plantilla_id=dia.plantilla_id, numero_dia=dia.numero_dia)
    orm.tiempos_comida = [_plantilla_tiempo_comida_to_orm(t) for t in dia.tiempos_comida]
    return orm


class PlantillaPlanRepositoryImpl(PlantillaPlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, plantilla: PlantillaPlan) -> None:
        existing = await self._session.get(PlantillaPlanORM, plantilla.id, options=_EAGER)
        if existing is None:
            orm = PlantillaPlanORM(
                id=plantilla.id,
                nombre=plantilla.nombre,
                descripcion=plantilla.descripcion,
                duracion_dias=plantilla.duracion.dias,
            )
            orm.dias = [_plantilla_dia_to_orm(d) for d in plantilla.dias]
            self._session.add(orm)
            return

        existing.nombre = plantilla.nombre
        existing.descripcion = plantilla.descripcion

        self._sync_dias(existing, plantilla)

    def _sync_dias(self, existing: PlantillaPlanORM, plantilla: PlantillaPlan) -> None:
        domain_dia_ids = {d.id for d in plantilla.dias}
        for dia_orm in list(existing.dias):
            if dia_orm.id not in domain_dia_ids:
                existing.dias.remove(dia_orm)

        for dia in plantilla.dias:
            dia_orm = next((d for d in existing.dias if d.id == dia.id), None)
            if dia_orm is None:
                existing.dias.append(_plantilla_dia_to_orm(dia))
            else:
                self._sync_tiempos_comida(dia_orm, dia)

    def _sync_tiempos_comida(self, dia_orm: PlantillaDiaORM, dia: PlantillaDia) -> None:
        domain_tiempo_ids = {t.id for t in dia.tiempos_comida}
        for tiempo_orm in list(dia_orm.tiempos_comida):
            if tiempo_orm.id not in domain_tiempo_ids:
                dia_orm.tiempos_comida.remove(tiempo_orm)

        for tiempo in dia.tiempos_comida:
            tiempo_orm = next((t for t in dia_orm.tiempos_comida if t.id == tiempo.id), None)
            if tiempo_orm is None:
                dia_orm.tiempos_comida.append(_plantilla_tiempo_comida_to_orm(tiempo))
            else:
                self._sync_recetas(tiempo_orm, tiempo)

    def _sync_recetas(
        self, tiempo_orm: PlantillaTiempoComidaORM, tiempo: PlantillaTiempoComida
    ) -> None:
        domain_receta_ids = {r.id for r in tiempo.recetas}
        for receta_orm in list(tiempo_orm.recetas):
            if receta_orm.id not in domain_receta_ids:
                tiempo_orm.recetas.remove(receta_orm)

        for receta in tiempo.recetas:
            receta_orm = next((r for r in tiempo_orm.recetas if r.id == receta.id), None)
            if receta_orm is None:
                tiempo_orm.recetas.append(_plantilla_receta_to_orm(receta))
            else:
                receta_orm.receta_catalogo_id = receta.receta_catalogo_id
                receta_orm.porcion_cantidad = receta.porcion.cantidad
                receta_orm.porcion_unidad = receta.porcion.unidad

    async def obtener_por_id(self, id: UUID) -> PlantillaPlan | None:
        stmt = select(PlantillaPlanORM).where(PlantillaPlanORM.id == id).options(*_EAGER)
        result = await self._session.execute(stmt)
        row = result.unique().scalar_one_or_none()
        return _plantilla_from_orm(row) if row else None

    async def listar(self) -> list[PlantillaPlan]:
        stmt = select(PlantillaPlanORM).options(*_EAGER)
        result = await self._session.execute(stmt)
        rows = result.unique().scalars().all()
        return [_plantilla_from_orm(r) for r in rows]
