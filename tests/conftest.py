"""Fixtures compartidas por toda la suite de pruebas.

Se divide en dos bloques:

1. **Builders de dominio** — construyen objetos reales del modelo para no repetir
   el mismo armado en cada test.
2. **Mocks de los puertos** — dobles de prueba que sustituyen a los repositorios.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from plan_nutricional.domain.model import (
    DuracionPlan,
    EstadoPlan,
    NecesidadNutricional,
    PlanNutricional,
    PlantillaPlan,
    RecetaCatalogo,
    RecomendacionNutricional,
)
from plan_nutricional.domain.repositories import (
    PlanNutricionalRepository,
    PlantillaPlanRepository,
    RecetaCatalogoRepository,
)

# Fecha fija: los tests nunca deben depender de "hoy", o dejarían de ser
# deterministas y fallarían en función del día en que se ejecuten.
FECHA_INICIO = date(2026, 1, 1)


# ---------------------------------------------------------------------------
# Builders de dominio
# ---------------------------------------------------------------------------

@pytest.fixture
def necesidad() -> NecesidadNutricional:
    """Necesidad nutricional válida de referencia."""
    return NecesidadNutricional(
        calorias=Decimal("2000"),
        proteinas=Decimal("120"),
        grasas=Decimal("60"),
        carbohidratos=Decimal("250"),
    )


@pytest.fixture
def construir_plan(necesidad):
    """Factory de PlanNutricional.

    Por defecto devuelve un plan de 15 días, en estado ACTIVO y sin días
    agregados. Los parámetros permiten variar solo lo que el test necesita:

        plan = construir_plan()                              # 15 días, vacío
        plan = construir_plan(dias_duracion=30)              # 30 días
        plan = construir_plan(dias=[1, 2])                   # con dos días
        plan = construir_plan(estado=EstadoPlan.FINALIZADO)  # no modificable
    """

    def _construir(
        dias_duracion: int = 15,
        dias: list[int] | None = None,
        estado: EstadoPlan = EstadoPlan.ACTIVO,
    ) -> PlanNutricional:
        plan = PlanNutricional.crear(
            paciente_id=uuid4(),
            fecha_inicio=FECHA_INICIO,
            duracion=DuracionPlan(dias=dias_duracion),
            necesidad=necesidad,
            recomendacion=RecomendacionNutricional(texto="Dieta hipocalórica"),
        )
        for numero_dia in dias or []:
            plan.agregar_dia(numero_dia)
        # El estado se cambia al final: un plan no ACTIVO ya no admite cambios.
        if estado is not EstadoPlan.ACTIVO:
            plan.cambiar_estado(estado)
        return plan

    return _construir


@pytest.fixture
def receta_catalogo() -> RecetaCatalogo:
    """Receta del catálogo, activa, con porción por defecto de 250 g."""
    return RecetaCatalogo.crear(
        nombre="Avena con frutas",
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar la avena con la fruta picada y servir.",
        cantidad=Decimal("250"),
        unidad="g",
    )


@pytest.fixture
def construir_plantilla():
    """Factory de PlantillaPlan vacía, de 15 días por defecto."""

    def _construir(dias_duracion: int = 15) -> PlantillaPlan:
        return PlantillaPlan.crear(
            nombre="Plantilla hipocalórica",
            descripcion="Base de 15 días para pacientes con sobrepeso",
            duracion=DuracionPlan(dias=dias_duracion),
        )

    return _construir


# ---------------------------------------------------------------------------
# Mocks de los puertos (interfaces ABC definidas en el dominio)
# ---------------------------------------------------------------------------

@pytest.fixture
def plan_repo_mock() -> AsyncMock:
    """Doble de PlanNutricionalRepository (guardar / obtener_por_id / ...)."""
    return AsyncMock(spec=PlanNutricionalRepository)


@pytest.fixture
def catalogo_repo_mock() -> AsyncMock:
    """Doble de RecetaCatalogoRepository."""
    return AsyncMock(spec=RecetaCatalogoRepository)


@pytest.fixture
def plantilla_repo_mock() -> AsyncMock:
    """Doble de PlantillaPlanRepository."""
    return AsyncMock(spec=PlantillaPlanRepository)
