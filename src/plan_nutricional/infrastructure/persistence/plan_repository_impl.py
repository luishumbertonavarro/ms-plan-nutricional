from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from plan_nutricional.domain.model import (
    DuracionPlan,
    EstadoPlan,
    NecesidadNutricional,
    PlanDia,
    PlanNutricional,
    Porcion,
    Receta,
    RecomendacionNutricional,
    TiempoComida,
    TipoTiempoComida,
)
from plan_nutricional.domain.repositories import PlanNutricionalRepository
from plan_nutricional.infrastructure.persistence.orm_models import (
    PlanDiaORM,
    PlanNutricionalORM,
    RecetaORM,
    TiempoComidaORM,
)

_EAGER = [
    joinedload(PlanNutricionalORM.dias)
    .joinedload(PlanDiaORM.tiempos_comida)
    .joinedload(TiempoComidaORM.recetas),
]


# ---------------------------------------------------------------------------
# ORM -> Domain
# ---------------------------------------------------------------------------

def _receta_from_orm(row: RecetaORM) -> Receta:
    return Receta(
        id=row.id,
        tiempo_comida_id=row.tiempo_comida_id,
        nombre=row.nombre,
        descripcion=row.descripcion,
        instrucciones=row.instrucciones,
        porcion=Porcion(cantidad=Decimal(str(row.porcion_cantidad)), unidad=row.porcion_unidad),
    )


def _tiempo_comida_from_orm(row: TiempoComidaORM) -> TiempoComida:
    return TiempoComida(
        id=row.id,
        plan_dia_id=row.plan_dia_id,
        tipo=TipoTiempoComida(row.tipo),
        _recetas=[_receta_from_orm(r) for r in row.recetas],
    )


def _plan_dia_from_orm(row: PlanDiaORM) -> PlanDia:
    return PlanDia(
        id=row.id,
        plan_id=row.plan_id,
        numero_dia=row.numero_dia,
        _tiempos_comida=[_tiempo_comida_from_orm(t) for t in row.tiempos_comida],
    )


def _plan_from_orm(row: PlanNutricionalORM) -> PlanNutricional:
    return PlanNutricional(
        id=row.id,
        paciente_id=row.paciente_id,
        fecha_inicio=row.fecha_inicio,
        fecha_fin=row.fecha_fin,
        estado=EstadoPlan(row.estado),
        duracion=DuracionPlan(dias=row.duracion_dias),
        necesidad=NecesidadNutricional(
            calorias=Decimal(str(row.necesidad_calorias)),
            proteinas=Decimal(str(row.necesidad_proteinas)),
            grasas=Decimal(str(row.necesidad_grasas)),
            carbohidratos=Decimal(str(row.necesidad_carbohidratos)),
        ),
        recomendacion=RecomendacionNutricional(texto=row.recomendacion_texto),
        dias=[_plan_dia_from_orm(d) for d in row.dias],
    )


# ---------------------------------------------------------------------------
# Domain -> ORM
# ---------------------------------------------------------------------------

def _receta_to_orm(receta: Receta) -> RecetaORM:
    return RecetaORM(
        id=receta.id,
        tiempo_comida_id=receta.tiempo_comida_id,
        nombre=receta.nombre,
        descripcion=receta.descripcion,
        instrucciones=receta.instrucciones,
        porcion_cantidad=receta.porcion.cantidad,
        porcion_unidad=receta.porcion.unidad,
    )


def _tiempo_comida_to_orm(tiempo: TiempoComida) -> TiempoComidaORM:
    orm = TiempoComidaORM(id=tiempo.id, plan_dia_id=tiempo.plan_dia_id, tipo=tiempo.tipo.value)
    orm.recetas = [_receta_to_orm(r) for r in tiempo.recetas]
    return orm


def _plan_dia_to_orm(dia: PlanDia) -> PlanDiaORM:
    orm = PlanDiaORM(id=dia.id, plan_id=dia.plan_id, numero_dia=dia.numero_dia)
    orm.tiempos_comida = [_tiempo_comida_to_orm(t) for t in dia.tiempos_comida]
    return orm


class PlanNutricionalRepositoryImpl(PlanNutricionalRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, plan: PlanNutricional) -> None:
        existing = await self._session.get(
            PlanNutricionalORM,
            plan.id,
            options=_EAGER,
        )
        if existing is None:
            orm = PlanNutricionalORM(
                id=plan.id,
                paciente_id=plan.paciente_id,
                fecha_inicio=plan.fecha_inicio,
                fecha_fin=plan.fecha_fin,
                estado=plan.estado.value,
                duracion_dias=plan.duracion.dias,
                necesidad_calorias=plan.necesidad.calorias,
                necesidad_proteinas=plan.necesidad.proteinas,
                necesidad_grasas=plan.necesidad.grasas,
                necesidad_carbohidratos=plan.necesidad.carbohidratos,
                recomendacion_texto=plan.recomendacion.texto,
            )
            orm.dias = [_plan_dia_to_orm(d) for d in plan.dias]
            self._session.add(orm)
            return

        existing.estado = plan.estado.value
        existing.recomendacion_texto = plan.recomendacion.texto

        self._sync_dias(existing, plan)

    def _sync_dias(self, existing: PlanNutricionalORM, plan: PlanNutricional) -> None:
        domain_dia_ids = {d.id for d in plan.dias}
        for dia_orm in list(existing.dias):
            if dia_orm.id not in domain_dia_ids:
                existing.dias.remove(dia_orm)

        for dia in plan.dias:
            dia_orm = next((d for d in existing.dias if d.id == dia.id), None)
            if dia_orm is None:
                existing.dias.append(_plan_dia_to_orm(dia))
            else:
                self._sync_tiempos_comida(dia_orm, dia)

    def _sync_tiempos_comida(self, dia_orm: PlanDiaORM, dia: PlanDia) -> None:
        domain_tiempo_ids = {t.id for t in dia.tiempos_comida}
        for tiempo_orm in list(dia_orm.tiempos_comida):
            if tiempo_orm.id not in domain_tiempo_ids:
                dia_orm.tiempos_comida.remove(tiempo_orm)

        for tiempo in dia.tiempos_comida:
            tiempo_orm = next((t for t in dia_orm.tiempos_comida if t.id == tiempo.id), None)
            if tiempo_orm is None:
                dia_orm.tiempos_comida.append(_tiempo_comida_to_orm(tiempo))
            else:
                self._sync_recetas(tiempo_orm, tiempo)

    def _sync_recetas(self, tiempo_orm: TiempoComidaORM, tiempo: TiempoComida) -> None:
        domain_receta_ids = {r.id for r in tiempo.recetas}
        for receta_orm in list(tiempo_orm.recetas):
            if receta_orm.id not in domain_receta_ids:
                tiempo_orm.recetas.remove(receta_orm)

        for receta in tiempo.recetas:
            receta_orm = next((r for r in tiempo_orm.recetas if r.id == receta.id), None)
            if receta_orm is None:
                tiempo_orm.recetas.append(_receta_to_orm(receta))
            else:
                receta_orm.nombre = receta.nombre
                receta_orm.descripcion = receta.descripcion
                receta_orm.instrucciones = receta.instrucciones
                receta_orm.porcion_cantidad = receta.porcion.cantidad
                receta_orm.porcion_unidad = receta.porcion.unidad

    async def obtener_por_id(self, id: UUID) -> PlanNutricional | None:
        stmt = select(PlanNutricionalORM).where(PlanNutricionalORM.id == id).options(*_EAGER)
        result = await self._session.execute(stmt)
        row = result.unique().scalar_one_or_none()
        return _plan_from_orm(row) if row else None

    async def obtener_por_paciente(self, paciente_id: UUID) -> list[PlanNutricional]:
        stmt = (
            select(PlanNutricionalORM)
            .where(PlanNutricionalORM.paciente_id == paciente_id)
            .options(*_EAGER)
        )
        result = await self._session.execute(stmt)
        rows = result.unique().scalars().all()
        return [_plan_from_orm(r) for r in rows]

    async def listar_activos(self) -> list[PlanNutricional]:
        stmt = (
            select(PlanNutricionalORM)
            .where(PlanNutricionalORM.estado == EstadoPlan.ACTIVO.value)
            .options(*_EAGER)
        )
        result = await self._session.execute(stmt)
        rows = result.unique().scalars().all()
        return [_plan_from_orm(r) for r in rows]
