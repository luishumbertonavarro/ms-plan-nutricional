-- =============================================================================
-- SCRIPT DE BASE DE DATOS: ms-plan-nutricional (BC3 – Planificación Nutricional)
-- Sistema: NUR-TRICENTER – Sistema Integral de Gestión Nutricional
-- Base de datos: db_plan_nutricional
--
-- Este script se ejecuta AUTOMÁTICAMENTE al primer arranque del contenedor
-- plan_nutricional_db (montado en /docker-entrypoint-initdb.d/).
--
-- Si necesitas ejecutarlo manualmente:
--   docker exec -i plan_nutricional_db psql -U postgres -d db_plan_nutricional < bd-ms-plan-nutricional.sql
--
-- El script es idempotente: usa CREATE TABLE IF NOT EXISTS y CREATE INDEX IF NOT EXISTS.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- TABLA: catalogo_recetas  (Aggregate Root: RecetaCatalogo)
--
-- Recetas reutilizables, independientes de cualquier plan o plantilla.
-- Sirven de fuente para poblar recetas en planes de pacientes y en plantillas.
--
-- Value Object aplanado:
--   Porcion (porción por defecto) → columnas porcion_cantidad y porcion_unidad
-- =============================================================================
CREATE TABLE IF NOT EXISTS catalogo_recetas (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    nombre              VARCHAR(200)    NOT NULL,
    descripcion         TEXT            NOT NULL,
    instrucciones       TEXT            NOT NULL,

    porcion_cantidad    NUMERIC(10, 3)  NOT NULL,
    porcion_unidad      VARCHAR(50)     NOT NULL,

    activa              BOOLEAN         NOT NULL DEFAULT TRUE,

    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT pk_catalogo_recetas PRIMARY KEY (id),
    CONSTRAINT uq_catalogo_recetas_nombre UNIQUE (nombre),
    CONSTRAINT ck_catalogo_recetas_porcion_cantidad CHECK (porcion_cantidad > 0)
);

CREATE INDEX IF NOT EXISTS idx_catalogo_recetas_activa
    ON catalogo_recetas (activa);

-- =============================================================================
-- TABLA: planes_nutricionales  (Aggregate Root: PlanNutricional)
--
-- Value Objects aplanados:
--   NecesidadNutricional → columnas necesidad_*
--   RecomendacionNutricional → columna recomendacion_texto
--   DuracionPlan → columna duracion_dias (solo 15 o 30, validado en dominio)
-- =============================================================================
CREATE TABLE IF NOT EXISTS planes_nutricionales (
    id                          UUID            NOT NULL DEFAULT gen_random_uuid(),
    paciente_id                 UUID            NOT NULL,
    fecha_inicio                DATE            NOT NULL,
    fecha_fin                   DATE            NOT NULL,
    estado                      VARCHAR(20)     NOT NULL,   -- ACTIVO | FINALIZADO | CANCELADO
    duracion_dias               SMALLINT        NOT NULL,   -- 15 o 30

    -- NecesidadNutricional (Value Object aplanado)
    necesidad_calorias          NUMERIC(10, 2)  NOT NULL,
    necesidad_proteinas         NUMERIC(10, 2)  NOT NULL,
    necesidad_grasas            NUMERIC(10, 2)  NOT NULL,
    necesidad_carbohidratos     NUMERIC(10, 2)  NOT NULL,

    -- RecomendacionNutricional (Value Object aplanado)
    recomendacion_texto         TEXT            NOT NULL,

    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT pk_planes_nutricionales PRIMARY KEY (id),
    CONSTRAINT ck_planes_estado
        CHECK (estado IN ('ACTIVO', 'FINALIZADO', 'CANCELADO')),
    CONSTRAINT ck_planes_duracion
        CHECK (duracion_dias IN (15, 30)),
    CONSTRAINT ck_planes_fechas
        CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT ck_planes_necesidad_calorias
        CHECK (necesidad_calorias >= 0),
    CONSTRAINT ck_planes_necesidad_proteinas
        CHECK (necesidad_proteinas >= 0),
    CONSTRAINT ck_planes_necesidad_grasas
        CHECK (necesidad_grasas >= 0),
    CONSTRAINT ck_planes_necesidad_carbohidratos
        CHECK (necesidad_carbohidratos >= 0)
);

CREATE INDEX IF NOT EXISTS idx_planes_paciente_id
    ON planes_nutricionales (paciente_id);

CREATE INDEX IF NOT EXISTS idx_planes_estado
    ON planes_nutricionales (estado);

-- =============================================================================
-- TABLA: plan_dias  (Entidad: PlanDia)
--
-- Cada fila representa un día numerado dentro del plan (1 a 15 o 1 a 30).
-- La combinación (plan_id, numero_dia) debe ser única — refleja DiaDuplicadoError.
-- =============================================================================
CREATE TABLE IF NOT EXISTS plan_dias (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    plan_id         UUID        NOT NULL,
    numero_dia      SMALLINT    NOT NULL,   -- 1 .. duracion_dias del plan

    CONSTRAINT pk_plan_dias PRIMARY KEY (id),
    CONSTRAINT fk_plan_dias_plan
        FOREIGN KEY (plan_id) REFERENCES planes_nutricionales (id) ON DELETE CASCADE,
    CONSTRAINT uq_plan_dias_plan_numero
        UNIQUE (plan_id, numero_dia),       -- refleja DiaDuplicadoError en dominio
    CONSTRAINT ck_plan_dias_numero
        CHECK (numero_dia >= 1)
);

CREATE INDEX IF NOT EXISTS idx_plan_dias_plan_id
    ON plan_dias (plan_id);

-- =============================================================================
-- TABLA: tiempos_comida  (Entidad: TiempoComida)
--
-- Cada fila representa una ingesta diaria (DESAYUNO, ALMUERZO, etc.).
-- La combinación (plan_dia_id, tipo) debe ser única — refleja TiempoComidaDuplicadoError.
-- =============================================================================
CREATE TABLE IF NOT EXISTS tiempos_comida (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    plan_dia_id     UUID        NOT NULL,
    tipo            VARCHAR(20) NOT NULL,   -- DESAYUNO | MEDIA_MANANA | ALMUERZO | MERIENDA | CENA | MEDIA_NOCHE

    CONSTRAINT pk_tiempos_comida PRIMARY KEY (id),
    CONSTRAINT fk_tiempos_comida_dia
        FOREIGN KEY (plan_dia_id) REFERENCES plan_dias (id) ON DELETE CASCADE,
    CONSTRAINT uq_tiempos_comida_dia_tipo
        UNIQUE (plan_dia_id, tipo),         -- refleja TiempoComidaDuplicadoError en dominio
    CONSTRAINT ck_tiempos_comida_tipo
        CHECK (tipo IN ('DESAYUNO', 'MEDIA_MANANA', 'ALMUERZO', 'MERIENDA', 'CENA', 'MEDIA_NOCHE'))
);

CREATE INDEX IF NOT EXISTS idx_tiempos_comida_plan_dia_id
    ON tiempos_comida (plan_dia_id);

-- =============================================================================
-- TABLA: recetas  (Entidad: Receta)
--
-- Value Object aplanado:
--   Porcion → columnas porcion_cantidad y porcion_unidad
--
-- El nombre de la receta debe ser único por tiempo de comida — refleja RecetaDuplicadaError.
-- =============================================================================
CREATE TABLE IF NOT EXISTS recetas (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    tiempo_comida_id    UUID            NOT NULL,
    nombre              VARCHAR(200)    NOT NULL,
    descripcion         TEXT            NOT NULL,
    instrucciones       TEXT            NOT NULL,

    -- Porcion (Value Object aplanado)
    porcion_cantidad    NUMERIC(10, 3)  NOT NULL,
    porcion_unidad      VARCHAR(50)     NOT NULL,

    CONSTRAINT pk_recetas PRIMARY KEY (id),
    CONSTRAINT fk_recetas_tiempo_comida
        FOREIGN KEY (tiempo_comida_id) REFERENCES tiempos_comida (id) ON DELETE CASCADE,
    CONSTRAINT uq_recetas_tiempo_nombre
        UNIQUE (tiempo_comida_id, nombre),  -- refleja RecetaDuplicadaError en dominio
    CONSTRAINT ck_recetas_porcion_cantidad
        CHECK (porcion_cantidad > 0)
);

CREATE INDEX IF NOT EXISTS idx_recetas_tiempo_comida_id
    ON recetas (tiempo_comida_id);

-- =============================================================================
-- TABLA: plantillas_planes  (Aggregate Root: PlantillaPlan)
--
-- Plantilla reutilizable de plan alimentario: define una estructura base de
-- días/tiempos de comida/recetas (del catálogo) que se puede usar para generar
-- un PlanNutricional para un paciente y luego personalizarlo. No tiene estado
-- (ACTIVO/FINALIZADO/CANCELADO) porque es catálogo, no una instancia de paciente.
-- =============================================================================
CREATE TABLE IF NOT EXISTS plantillas_planes (
    id                          UUID            NOT NULL DEFAULT gen_random_uuid(),
    nombre                      VARCHAR(200)    NOT NULL,
    descripcion                 TEXT            NOT NULL,
    duracion_dias               SMALLINT        NOT NULL,   -- 15 o 30

    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT pk_plantillas_planes PRIMARY KEY (id),
    CONSTRAINT uq_plantillas_planes_nombre UNIQUE (nombre),
    CONSTRAINT ck_plantillas_duracion CHECK (duracion_dias IN (15, 30))
);

-- =============================================================================
-- TABLA: plantilla_dias  (Entidad: PlantillaDia)
-- =============================================================================
CREATE TABLE IF NOT EXISTS plantilla_dias (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    plantilla_id    UUID        NOT NULL,
    numero_dia      SMALLINT    NOT NULL,   -- 1 .. duracion_dias de la plantilla

    CONSTRAINT pk_plantilla_dias PRIMARY KEY (id),
    CONSTRAINT fk_plantilla_dias_plantilla
        FOREIGN KEY (plantilla_id) REFERENCES plantillas_planes (id) ON DELETE CASCADE,
    CONSTRAINT uq_plantilla_dias_plantilla_numero
        UNIQUE (plantilla_id, numero_dia),
    CONSTRAINT ck_plantilla_dias_numero
        CHECK (numero_dia >= 1)
);

CREATE INDEX IF NOT EXISTS idx_plantilla_dias_plantilla_id
    ON plantilla_dias (plantilla_id);

-- =============================================================================
-- TABLA: plantilla_tiempos_comida  (Entidad: PlantillaTiempoComida)
-- =============================================================================
CREATE TABLE IF NOT EXISTS plantilla_tiempos_comida (
    id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
    plantilla_dia_id    UUID        NOT NULL,
    tipo                VARCHAR(20) NOT NULL,

    CONSTRAINT pk_plantilla_tiempos_comida PRIMARY KEY (id),
    CONSTRAINT fk_plantilla_tiempos_comida_dia
        FOREIGN KEY (plantilla_dia_id) REFERENCES plantilla_dias (id) ON DELETE CASCADE,
    CONSTRAINT uq_plantilla_tiempos_comida_dia_tipo
        UNIQUE (plantilla_dia_id, tipo),
    CONSTRAINT ck_plantilla_tiempos_comida_tipo
        CHECK (tipo IN ('DESAYUNO', 'MEDIA_MANANA', 'ALMUERZO', 'MERIENDA', 'CENA', 'MEDIA_NOCHE'))
);

CREATE INDEX IF NOT EXISTS idx_plantilla_tiempos_comida_dia_id
    ON plantilla_tiempos_comida (plantilla_dia_id);

-- =============================================================================
-- TABLA: plantilla_recetas  (Entidad: PlantillaReceta)
--
-- Referencia a una receta del catálogo (catalogo_recetas), con la porción
-- sugerida para esa plantilla. No almacena texto de receta: siempre se resuelve
-- contra catalogo_recetas — es lo que fuerza la reutilización (HU-14/HU-17).
-- =============================================================================
CREATE TABLE IF NOT EXISTS plantilla_recetas (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    tiempo_comida_id    UUID            NOT NULL,
    receta_catalogo_id  UUID            NOT NULL,

    porcion_cantidad    NUMERIC(10, 3)  NOT NULL,
    porcion_unidad      VARCHAR(50)     NOT NULL,

    CONSTRAINT pk_plantilla_recetas PRIMARY KEY (id),
    CONSTRAINT fk_plantilla_recetas_tiempo_comida
        FOREIGN KEY (tiempo_comida_id) REFERENCES plantilla_tiempos_comida (id) ON DELETE CASCADE,
    CONSTRAINT fk_plantilla_recetas_catalogo
        FOREIGN KEY (receta_catalogo_id) REFERENCES catalogo_recetas (id),
    CONSTRAINT ck_plantilla_recetas_porcion_cantidad
        CHECK (porcion_cantidad > 0)
);

CREATE INDEX IF NOT EXISTS idx_plantilla_recetas_tiempo_comida_id
    ON plantilla_recetas (tiempo_comida_id);

CREATE INDEX IF NOT EXISTS idx_plantilla_recetas_receta_catalogo_id
    ON plantilla_recetas (receta_catalogo_id);

-- =============================================================================
-- FIN DEL SCRIPT
-- =============================================================================