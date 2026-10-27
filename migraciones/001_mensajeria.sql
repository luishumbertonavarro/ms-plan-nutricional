-- Mensajería: Transactional Outbox, inbox de idempotencia y réplica de contratos de asesoramiento.
-- Idempotente: se puede correr sobre una BD existente sin borrar el volumen.
--   docker exec -i plan_nutricional_db psql -U postgres -d db_plan_nutricional < migraciones/001_mensajeria.sql

CREATE TABLE IF NOT EXISTS outbox (
    id            UUID PRIMARY KEY,
    tipo          VARCHAR(100) NOT NULL,
    routing_key   VARCHAR(100) NOT NULL,
    payload       JSONB        NOT NULL,
    ocurrido_en   TIMESTAMPTZ  NOT NULL,
    publicado_en  TIMESTAMPTZ,
    intentos      INTEGER      NOT NULL DEFAULT 0,
    ultimo_error  TEXT
);
-- El relay solo busca pendientes: índice parcial.
CREATE INDEX IF NOT EXISTS ix_outbox_pendientes ON outbox (ocurrido_en) WHERE publicado_en IS NULL;

CREATE TABLE IF NOT EXISTS eventos_procesados (
    message_id    VARCHAR(100) PRIMARY KEY,
    routing_key   VARCHAR(100) NOT NULL,
    procesado_en  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS asesoramientos_habilitados (
    contrato_id     UUID PRIMARY KEY,
    paciente_id     UUID        NOT NULL,
    fecha_inicio    DATE,
    activo          BOOLEAN     NOT NULL DEFAULT TRUE,
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_asesoramientos_paciente ON asesoramientos_habilitados (paciente_id);
