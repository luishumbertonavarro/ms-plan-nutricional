"""Pruebas unitarias de los Value Objects del dominio.

Los VO son `dataclass(frozen=True)` que validan sus invariantes en `__post_init__`
y lanzan `ValueError` si el valor recibido es inválido. Al ser objetos puros, se
prueban directamente: no hay dependencias que doblar.
"""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from plan_nutricional.domain.model.value_objects import (
    DuracionPlan,
    NecesidadNutricional,
    Porcion,
    RecomendacionNutricional,
)


# ---------------------------------------------------------------------------
# NecesidadNutricional
# ---------------------------------------------------------------------------

class TestNecesidadNutricional:

    def test_crear_con_valores_positivos_conserva_los_macronutrientes(self):
        # Arrange / Act
        necesidad = NecesidadNutricional(
            calorias=Decimal("2000"),
            proteinas=Decimal("120"),
            grasas=Decimal("60"),
            carbohidratos=Decimal("250"),
        )

        # Assert
        assert necesidad.calorias == Decimal("2000")
        assert necesidad.proteinas == Decimal("120")
        assert necesidad.grasas == Decimal("60")
        assert necesidad.carbohidratos == Decimal("250")

    def test_crear_con_todos_los_valores_en_cero_es_valido(self):
        # Arrange / Act
        necesidad = NecesidadNutricional(
            calorias=Decimal("0"),
            proteinas=Decimal("0"),
            grasas=Decimal("0"),
            carbohidratos=Decimal("0"),
        )

        # Assert — cero está permitido; la regla es "no negativo", no "positivo".
        assert necesidad.calorias == Decimal("0")

    @pytest.mark.parametrize(
        "campo",
        ["calorias", "proteinas", "grasas", "carbohidratos"],
    )
    def test_crear_con_un_macronutriente_negativo_lanza_value_error(self, campo):
        # Arrange — todos válidos salvo el campo bajo prueba
        valores = {
            "calorias": Decimal("2000"),
            "proteinas": Decimal("120"),
            "grasas": Decimal("60"),
            "carbohidratos": Decimal("250"),
        }
        valores[campo] = Decimal("-1")

        # Act / Assert — el mensaje debe identificar el campo culpable
        with pytest.raises(ValueError, match=campo):
            NecesidadNutricional(**valores)


# ---------------------------------------------------------------------------
# DuracionPlan
# ---------------------------------------------------------------------------

class TestDuracionPlan:

    @pytest.mark.parametrize("dias", [15, 30])
    def test_crear_con_duracion_permitida_conserva_el_valor(self, dias):
        # Arrange / Act
        duracion = DuracionPlan(dias=dias)

        # Assert
        assert duracion.dias == dias

    @pytest.mark.parametrize("dias", [0, 1, 7, 14, 16, 29, 31, -5])
    def test_crear_con_duracion_no_permitida_lanza_value_error(self, dias):
        # Act / Assert — la regla de negocio admite únicamente 15 o 30 días
        with pytest.raises(ValueError, match="15 o 30 días"):
            DuracionPlan(dias=dias)

    def test_duracion_es_inmutable(self):
        # Arrange
        duracion = DuracionPlan(dias=15)

        # Act / Assert — es un Value Object: no se puede mutar tras crearlo
        with pytest.raises(FrozenInstanceError):
            duracion.dias = 30

    def test_dos_duraciones_con_el_mismo_valor_son_iguales(self):
        # Arrange / Act / Assert — los VO se comparan por valor, no por identidad
        assert DuracionPlan(dias=15) == DuracionPlan(dias=15)
        assert DuracionPlan(dias=15) != DuracionPlan(dias=30)


# ---------------------------------------------------------------------------
# RecomendacionNutricional
# ---------------------------------------------------------------------------

class TestRecomendacionNutricional:

    def test_crear_con_texto_conserva_la_recomendacion(self):
        # Arrange / Act
        recomendacion = RecomendacionNutricional(texto="Reducir sodio")

        # Assert
        assert recomendacion.texto == "Reducir sodio"

    @pytest.mark.parametrize("texto", ["", "   ", "\n", "\t  \n"])
    def test_crear_con_texto_vacio_o_en_blanco_lanza_value_error(self, texto):
        # Act / Assert
        with pytest.raises(ValueError, match="no puede estar vacía"):
            RecomendacionNutricional(texto=texto)


# ---------------------------------------------------------------------------
# Porcion
# ---------------------------------------------------------------------------

class TestPorcion:

    def test_crear_con_cantidad_positiva_conserva_cantidad_y_unidad(self):
        # Arrange / Act
        porcion = Porcion(cantidad=Decimal("0.5"), unidad="kg")

        # Assert
        assert porcion.cantidad == Decimal("0.5")
        assert porcion.unidad == "kg"

    @pytest.mark.parametrize("cantidad", [Decimal("0"), Decimal("-1"), Decimal("-0.01")])
    def test_crear_con_cantidad_no_positiva_lanza_value_error(self, cantidad):
        # Act / Assert
        with pytest.raises(ValueError, match="mayor que cero"):
            Porcion(cantidad=cantidad, unidad="g")

    @pytest.mark.parametrize("unidad", ["", "   ", "\n"])
    def test_crear_con_unidad_vacia_lanza_value_error(self, unidad):
        # Act / Assert
        with pytest.raises(ValueError, match="unidad .* no puede estar vacía"):
            Porcion(cantidad=Decimal("100"), unidad=unidad)
