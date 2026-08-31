"""Pruebas unitarias del Aggregate Root `PlanNutricional`.

Es el corazón del Bounded Context: protege todas las invariantes del plan
(duración, unicidad de días, ciclo de vida). No tiene ninguna dependencia de
infraestructura, por lo que se prueba con objetos reales y sin mocks.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.domain.exceptions.plan_exceptions import (
    DiaDuplicadoError,
    DiaFueraDeDuracionError,
    DiaNoEncontradoError,
    PlanNoModificableError,
    RecetaDuplicadaError,
    TiempoComidaDuplicadoError,
    TiempoComidaNoEncontradoError,
    TransicionEstadoInvalidaError,
)
from plan_nutricional.domain.model.enums import EstadoPlan, TipoTiempoComida
from plan_nutricional.domain.model.plan_nutricional import PlanNutricional
from plan_nutricional.domain.model.value_objects import (
    DuracionPlan,
    NecesidadNutricional,
    RecomendacionNutricional,
)


# ---------------------------------------------------------------------------
# Creación
# ---------------------------------------------------------------------------

class TestCrearPlan:

    @pytest.mark.parametrize(
        "dias_duracion, fecha_fin_esperada",
        [
            (15, date(2026, 1, 15)),
            (30, date(2026, 1, 30)),
        ],
    )
    def test_crear_calcula_la_fecha_fin_segun_la_duracion(
        self, necesidad, dias_duracion, fecha_fin_esperada
    ):
        # Arrange / Act
        plan = PlanNutricional.crear(
            paciente_id=uuid4(),
            fecha_inicio=date(2026, 1, 1),
            duracion=DuracionPlan(dias=dias_duracion),
            necesidad=necesidad,
            recomendacion=RecomendacionNutricional(texto="Dieta hipocalórica"),
        )

        # Assert — la fecha de inicio cuenta como día 1, de ahí el "- 1"
        assert plan.fecha_fin == fecha_fin_esperada

    def test_crear_deja_el_plan_activo_y_sin_dias(self, construir_plan):
        # Arrange / Act
        plan = construir_plan()

        # Assert
        assert plan.estado is EstadoPlan.ACTIVO
        assert plan.es_activo is True
        assert plan.dias == []
        assert plan.total_dias_agregados == 0

    def test_crear_asigna_un_identificador_distinto_a_cada_plan(self, construir_plan):
        # Arrange / Act
        primero = construir_plan()
        segundo = construir_plan()

        # Assert
        assert primero.id != segundo.id


# ---------------------------------------------------------------------------
# Gestión de días
# ---------------------------------------------------------------------------

class TestAgregarDia:

    def test_agregar_dia_valido_lo_incorpora_al_plan(self, construir_plan):
        # Arrange
        plan = construir_plan(dias_duracion=15)

        # Act
        dia = plan.agregar_dia(3)

        # Assert
        assert dia.numero_dia == 3
        assert dia.plan_id == plan.id
        assert plan.total_dias_agregados == 1

    @pytest.mark.parametrize(
        "dias_duracion, numero_dia",
        [
            (15, 0),
            (15, 16),
            (15, -1),
            (30, 31),
            (30, 0),
        ],
    )
    def test_agregar_dia_fuera_de_duracion_lanza_error(
        self, construir_plan, dias_duracion, numero_dia
    ):
        # Arrange
        plan = construir_plan(dias_duracion=dias_duracion)

        # Act / Assert — solo se admiten días entre 1 y la duración del plan
        with pytest.raises(DiaFueraDeDuracionError):
            plan.agregar_dia(numero_dia)

        assert plan.total_dias_agregados == 0

    def test_agregar_dia_repetido_lanza_error_y_no_duplica(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[5])

        # Act / Assert
        with pytest.raises(DiaDuplicadoError):
            plan.agregar_dia(5)

        assert plan.total_dias_agregados == 1

    @pytest.mark.parametrize(
        "estado", [EstadoPlan.FINALIZADO, EstadoPlan.CANCELADO]
    )
    def test_agregar_dia_en_plan_no_activo_lanza_error(self, construir_plan, estado):
        # Arrange
        plan = construir_plan(estado=estado)

        # Act / Assert — solo los planes ACTIVO admiten cambios
        with pytest.raises(PlanNoModificableError):
            plan.agregar_dia(1)


class TestEliminarDia:

    def test_eliminar_dia_existente_lo_quita_del_plan(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1, 2])

        # Act
        plan.eliminar_dia(1)

        # Assert
        assert [d.numero_dia for d in plan.dias] == [2]

    def test_eliminar_dia_inexistente_lanza_error(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1])

        # Act / Assert
        with pytest.raises(DiaNoEncontradoError):
            plan.eliminar_dia(9)

    def test_eliminar_dia_en_plan_no_activo_lanza_error(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1], estado=EstadoPlan.CANCELADO)

        # Act / Assert
        with pytest.raises(PlanNoModificableError):
            plan.eliminar_dia(1)


class TestCopiaDefensiva:
    """`plan.dias` devuelve `list(self._dias)`: una copia, no la lista interna.

    Es lo que impide que un consumidor del agregado modifique su estado saltándose
    las invariantes.
    """

    def test_modificar_la_lista_devuelta_no_altera_el_plan(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1])

        # Act — se intenta mutar el agregado por la puerta de atrás
        dias_expuestos = plan.dias
        dias_expuestos.clear()

        # Assert — el agregado conserva su estado
        assert plan.total_dias_agregados == 1

    def test_cada_lectura_devuelve_una_lista_distinta(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1])

        # Act / Assert
        assert plan.dias is not plan.dias


# ---------------------------------------------------------------------------
# Tiempos de comida y recetas (delegación en las entidades hijas)
# ---------------------------------------------------------------------------

class TestTiemposDeComida:

    def test_agregar_tiempo_comida_lo_asocia_al_dia_indicado(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1])

        # Act
        tiempo = plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)

        # Assert
        assert tiempo.tipo is TipoTiempoComida.DESAYUNO
        assert plan.dias[0].tiempos_comida == [tiempo]

    def test_agregar_tiempo_comida_en_dia_inexistente_lanza_error(self, construir_plan):
        # Arrange
        plan = construir_plan()

        # Act / Assert
        with pytest.raises(DiaNoEncontradoError):
            plan.agregar_tiempo_comida(1, TipoTiempoComida.ALMUERZO)

    def test_agregar_tiempo_comida_repetido_en_el_mismo_dia_lanza_error(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1])
        plan.agregar_tiempo_comida(1, TipoTiempoComida.CENA)

        # Act / Assert — un día no puede tener dos cenas
        with pytest.raises(TiempoComidaDuplicadoError):
            plan.agregar_tiempo_comida(1, TipoTiempoComida.CENA)

    def test_eliminar_tiempo_comida_inexistente_lanza_error(self, construir_plan):
        # Arrange
        plan = construir_plan(dias=[1])

        # Act / Assert
        with pytest.raises(TiempoComidaNoEncontradoError):
            plan.eliminar_tiempo_comida(1, TipoTiempoComida.MERIENDA)


class TestRecetas:

    @pytest.fixture
    def plan_con_desayuno(self, construir_plan):
        plan = construir_plan(dias=[1])
        plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
        return plan

    def test_agregar_receta_la_asocia_con_su_porcion(self, plan_con_desayuno):
        # Act
        receta = plan_con_desayuno.agregar_receta(
            numero_dia=1,
            tipo=TipoTiempoComida.DESAYUNO,
            nombre="Avena",
            descripcion="Con fruta",
            instrucciones="Mezclar y servir",
            cantidad=Decimal("250"),
            unidad="g",
        )

        # Assert
        assert receta.nombre == "Avena"
        assert receta.porcion.cantidad == Decimal("250")
        assert receta.porcion.unidad == "g"

    def test_agregar_receta_con_nombre_repetido_lanza_error_ignorando_mayusculas(
        self, plan_con_desayuno
    ):
        # Arrange
        plan_con_desayuno.agregar_receta(
            1, TipoTiempoComida.DESAYUNO, "Avena", "d", "i", Decimal("100"), "g"
        )

        # Act / Assert — la comparación de nombres es case-insensitive
        with pytest.raises(RecetaDuplicadaError):
            plan_con_desayuno.agregar_receta(
                1, TipoTiempoComida.DESAYUNO, "AVENA", "d", "i", Decimal("100"), "g"
            )

    def test_agregar_receta_con_cantidad_no_positiva_propaga_value_error(
        self, plan_con_desayuno
    ):
        # Act / Assert — la validación vive en el Value Object Porcion
        with pytest.raises(ValueError, match="mayor que cero"):
            plan_con_desayuno.agregar_receta(
                1, TipoTiempoComida.DESAYUNO, "Avena", "d", "i", Decimal("0"), "g"
            )

    def test_agregar_receta_en_tiempo_de_comida_inexistente_lanza_error(
        self, construir_plan
    ):
        # Arrange — el día existe pero no tiene el tiempo de comida pedido
        plan = construir_plan(dias=[1])

        # Act / Assert
        with pytest.raises(TiempoComidaNoEncontradoError):
            plan.agregar_receta(
                1, TipoTiempoComida.CENA, "Sopa", "d", "i", Decimal("300"), "ml"
            )

    def test_eliminar_receta_la_quita_del_tiempo_de_comida(self, plan_con_desayuno):
        # Arrange
        receta = plan_con_desayuno.agregar_receta(
            1, TipoTiempoComida.DESAYUNO, "Avena", "d", "i", Decimal("250"), "g"
        )

        # Act
        plan_con_desayuno.eliminar_receta(1, TipoTiempoComida.DESAYUNO, receta.id)

        # Assert
        tiempo = plan_con_desayuno.dias[0].tiempos_comida[0]
        assert tiempo.recetas == []


# ---------------------------------------------------------------------------
# Recomendación
# ---------------------------------------------------------------------------

class TestModificarRecomendacion:

    def test_modificar_recomendacion_reemplaza_el_value_object(self, construir_plan):
        # Arrange
        plan = construir_plan()

        # Act
        plan.modificar_recomendacion("Aumentar consumo de fibra")

        # Assert
        assert plan.recomendacion == RecomendacionNutricional(
            texto="Aumentar consumo de fibra"
        )

    def test_modificar_recomendacion_con_texto_vacio_lanza_value_error(self, construir_plan):
        # Arrange
        plan = construir_plan()

        # Act / Assert
        with pytest.raises(ValueError, match="no puede estar vacía"):
            plan.modificar_recomendacion("   ")

    def test_modificar_recomendacion_en_plan_no_activo_lanza_error(self, construir_plan):
        # Arrange
        plan = construir_plan(estado=EstadoPlan.FINALIZADO)

        # Act / Assert
        with pytest.raises(PlanNoModificableError):
            plan.modificar_recomendacion("Otro texto")


# ---------------------------------------------------------------------------
# Ciclo de vida: matriz completa de transiciones de estado
# ---------------------------------------------------------------------------

class TestTransicionesDeEstado:
    """Transiciones permitidas:

        ACTIVO     → FINALIZADO, CANCELADO
        FINALIZADO → (ninguna)
        CANCELADO  → (ninguna)
    """

    @pytest.mark.parametrize(
        "estado_destino", [EstadoPlan.FINALIZADO, EstadoPlan.CANCELADO]
    )
    def test_desde_activo_se_puede_finalizar_o_cancelar(self, construir_plan, estado_destino):
        # Arrange
        plan = construir_plan()

        # Act
        plan.cambiar_estado(estado_destino)

        # Assert
        assert plan.estado is estado_destino
        assert plan.es_activo is False

    @pytest.mark.parametrize(
        "estado_inicial, estado_destino",
        [
            (EstadoPlan.ACTIVO, EstadoPlan.ACTIVO),
            (EstadoPlan.FINALIZADO, EstadoPlan.ACTIVO),
            (EstadoPlan.FINALIZADO, EstadoPlan.CANCELADO),
            (EstadoPlan.FINALIZADO, EstadoPlan.FINALIZADO),
            (EstadoPlan.CANCELADO, EstadoPlan.ACTIVO),
            (EstadoPlan.CANCELADO, EstadoPlan.FINALIZADO),
            (EstadoPlan.CANCELADO, EstadoPlan.CANCELADO),
        ],
    )
    def test_transicion_no_permitida_lanza_error_y_conserva_el_estado(
        self, construir_plan, estado_inicial, estado_destino
    ):
        # Arrange
        plan = construir_plan(estado=estado_inicial)

        # Act / Assert
        with pytest.raises(TransicionEstadoInvalidaError):
            plan.cambiar_estado(estado_destino)

        assert plan.estado is estado_inicial

    def test_finalizar_es_un_atajo_de_cambiar_estado(self, construir_plan):
        # Arrange
        plan = construir_plan()

        # Act
        plan.finalizar()

        # Assert
        assert plan.estado is EstadoPlan.FINALIZADO

    def test_cancelar_es_un_atajo_de_cambiar_estado(self, construir_plan):
        # Arrange
        plan = construir_plan()

        # Act
        plan.cancelar()

        # Assert
        assert plan.estado is EstadoPlan.CANCELADO


# ---------------------------------------------------------------------------
# Rehidratación desde el repositorio
# ---------------------------------------------------------------------------

def test_constructor_rehidrata_un_plan_con_todos_sus_datos():
    """El constructor (a diferencia de `crear`) reconstruye un plan ya existente
    tal como lo devuelve el repositorio, sin recalcular nada."""
    # Arrange
    plan_id, paciente_id = uuid4(), uuid4()

    # Act
    plan = PlanNutricional(
        id=plan_id,
        paciente_id=paciente_id,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 15),
        estado=EstadoPlan.FINALIZADO,
        duracion=DuracionPlan(dias=15),
        necesidad=NecesidadNutricional(
            calorias=Decimal("1800"),
            proteinas=Decimal("100"),
            grasas=Decimal("50"),
            carbohidratos=Decimal("200"),
        ),
        recomendacion=RecomendacionNutricional(texto="Mantener"),
        dias=[],
    )

    # Assert
    assert plan.id == plan_id
    assert plan.paciente_id == paciente_id
    assert plan.estado is EstadoPlan.FINALIZADO
    assert plan.duracion.dias == 15
