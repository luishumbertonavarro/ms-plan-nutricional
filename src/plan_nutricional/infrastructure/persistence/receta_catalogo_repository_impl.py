from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from plan_nutricional.domain.model import Porcion, RecetaCatalogo
from plan_nutricional.domain.repositories import RecetaCatalogoRepository
from plan_nutricional.infrastructure.persistence.orm_models import RecetaCatalogoORM


def _receta_catalogo_from_orm(row: RecetaCatalogoORM) -> RecetaCatalogo:
    return RecetaCatalogo(
        id=row.id,
        nombre=row.nombre,
        descripcion=row.descripcion,
        instrucciones=row.instrucciones,
        porcion_default=Porcion(
            cantidad=Decimal(str(row.porcion_cantidad)), unidad=row.porcion_unidad
        ),
        activa=row.activa,
    )


class RecetaCatalogoRepositoryImpl(RecetaCatalogoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, receta: RecetaCatalogo) -> None:
        existing = await self._session.get(RecetaCatalogoORM, receta.id)
        if existing is None:
            self._session.add(
                RecetaCatalogoORM(
                    id=receta.id,
                    nombre=receta.nombre,
                    descripcion=receta.descripcion,
                    instrucciones=receta.instrucciones,
                    porcion_cantidad=receta.porcion_default.cantidad,
                    porcion_unidad=receta.porcion_default.unidad,
                    activa=receta.activa,
                )
            )
            return

        existing.nombre = receta.nombre
        existing.descripcion = receta.descripcion
        existing.instrucciones = receta.instrucciones
        existing.porcion_cantidad = receta.porcion_default.cantidad
        existing.porcion_unidad = receta.porcion_default.unidad
        existing.activa = receta.activa

    async def obtener_por_id(self, id: UUID) -> RecetaCatalogo | None:
        row = await self._session.get(RecetaCatalogoORM, id)
        return _receta_catalogo_from_orm(row) if row else None

    async def listar(self, solo_activas: bool = False) -> list[RecetaCatalogo]:
        stmt = select(RecetaCatalogoORM)
        if solo_activas:
            stmt = stmt.where(RecetaCatalogoORM.activa.is_(True))
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [_receta_catalogo_from_orm(r) for r in rows]
