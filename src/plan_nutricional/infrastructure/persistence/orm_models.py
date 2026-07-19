import uuid
from datetime import date, datetime

from sqlalchemy import (
    UUID,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RecetaCatalogoORM(Base):
    __tablename__ = "catalogo_recetas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    instrucciones: Mapped[str] = mapped_column(Text, nullable=False)

    porcion_cantidad: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    porcion_unidad: Mapped[str] = mapped_column(String(50), nullable=False)

    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PlanNutricionalORM(Base):
    __tablename__ = "planes_nutricionales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    duracion_dias: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    necesidad_calorias: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    necesidad_proteinas: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    necesidad_grasas: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    necesidad_carbohidratos: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    recomendacion_texto: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    dias: Mapped[list["PlanDiaORM"]] = relationship(
        "PlanDiaORM", back_populates="plan", cascade="all, delete-orphan"
    )


class PlanDiaORM(Base):
    __tablename__ = "plan_dias"
    __table_args__ = (UniqueConstraint("plan_id", "numero_dia", name="uq_plan_dias_plan_numero"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("planes_nutricionales.id"), nullable=False
    )
    numero_dia: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    plan: Mapped["PlanNutricionalORM"] = relationship("PlanNutricionalORM", back_populates="dias")
    tiempos_comida: Mapped[list["TiempoComidaORM"]] = relationship(
        "TiempoComidaORM", back_populates="plan_dia", cascade="all, delete-orphan"
    )


class TiempoComidaORM(Base):
    __tablename__ = "tiempos_comida"
    __table_args__ = (
        UniqueConstraint("plan_dia_id", "tipo", name="uq_tiempos_comida_dia_tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_dia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plan_dias.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)

    plan_dia: Mapped["PlanDiaORM"] = relationship("PlanDiaORM", back_populates="tiempos_comida")
    recetas: Mapped[list["RecetaORM"]] = relationship(
        "RecetaORM", back_populates="tiempo_comida", cascade="all, delete-orphan"
    )


class RecetaORM(Base):
    __tablename__ = "recetas"
    __table_args__ = (
        UniqueConstraint("tiempo_comida_id", "nombre", name="uq_recetas_tiempo_nombre"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tiempo_comida_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tiempos_comida.id"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    instrucciones: Mapped[str] = mapped_column(Text, nullable=False)

    porcion_cantidad: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    porcion_unidad: Mapped[str] = mapped_column(String(50), nullable=False)

    tiempo_comida: Mapped["TiempoComidaORM"] = relationship("TiempoComidaORM", back_populates="recetas")


class PlantillaPlanORM(Base):
    __tablename__ = "plantillas_planes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    duracion_dias: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    dias: Mapped[list["PlantillaDiaORM"]] = relationship(
        "PlantillaDiaORM", back_populates="plantilla", cascade="all, delete-orphan"
    )


class PlantillaDiaORM(Base):
    __tablename__ = "plantilla_dias"
    __table_args__ = (
        UniqueConstraint("plantilla_id", "numero_dia", name="uq_plantilla_dias_plantilla_numero"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plantilla_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plantillas_planes.id"), nullable=False
    )
    numero_dia: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    plantilla: Mapped["PlantillaPlanORM"] = relationship("PlantillaPlanORM", back_populates="dias")
    tiempos_comida: Mapped[list["PlantillaTiempoComidaORM"]] = relationship(
        "PlantillaTiempoComidaORM", back_populates="plantilla_dia", cascade="all, delete-orphan"
    )


class PlantillaTiempoComidaORM(Base):
    __tablename__ = "plantilla_tiempos_comida"
    __table_args__ = (
        UniqueConstraint(
            "plantilla_dia_id", "tipo", name="uq_plantilla_tiempos_comida_dia_tipo"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plantilla_dia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plantilla_dias.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)

    plantilla_dia: Mapped["PlantillaDiaORM"] = relationship(
        "PlantillaDiaORM", back_populates="tiempos_comida"
    )
    recetas: Mapped[list["PlantillaRecetaORM"]] = relationship(
        "PlantillaRecetaORM", back_populates="tiempo_comida", cascade="all, delete-orphan"
    )


class PlantillaRecetaORM(Base):
    __tablename__ = "plantilla_recetas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tiempo_comida_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plantilla_tiempos_comida.id"), nullable=False
    )
    receta_catalogo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalogo_recetas.id"), nullable=False
    )

    porcion_cantidad: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    porcion_unidad: Mapped[str] = mapped_column(String(50), nullable=False)

    tiempo_comida: Mapped["PlantillaTiempoComidaORM"] = relationship(
        "PlantillaTiempoComidaORM", back_populates="recetas"
    )
