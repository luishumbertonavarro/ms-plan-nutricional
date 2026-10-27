# Eventos de integración — ms-plan-nutricional (BC3)

**Sistema:** NUR-TRICENTER · **Responsable:** Luis Humberto Navarro Ribeiro
**Estado:** implementado (outbox + RabbitMQ). Contratos finales en `Eventos_Integracion_NUR-TRICENTER.docx`. Los eventos que este servicio
**produce** salen de su código actual; los que **consume** son una propuesta que
debe confirmar el equipo que los produce.

> **Evento de integración** = algo que **ya pasó** en este microservicio y que le
> interesa a **otro** microservicio. Lo que solo le interesa a BC3 (agregar una
> receta, cambiar el texto de una recomendación) es un evento de **dominio** y no se
> publica: ver la [sección 5](#5-eventos-de-dominio-que-no-se-publican).

---

## 1. Convenciones del grupo (implementadas)

> Esta sección reemplaza la propuesta original del sobre `{evento_id, tipo, datos…}`.
> Lo acordado en `Eventos_Integracion_NUR-TRICENTER.docx` y lo que corre hoy es:

| Aspecto | Convención |
|---|---|
| Broker | **RabbitMQ**, exchange **topic** durable `nurtricenter.events` |
| Routing key | `entidad.participio` en minúsculas: `plan_nutricional.creado`, `calendario.cancelado`, `servicio.contratado` |
| Cuerpo | El JSON del evento **directo, sin sobre** (los bloques «datos» de este documento son el cuerpo completo) |
| Metadatos | Propiedades AMQP: `message_id` (id de la fila del outbox, para idempotencia), `type` (nombre del evento en PascalCase), `timestamp`, `content_type=application/json`, `delivery_mode=persistent` |
| Colas | Una cola durable por microservicio: `ms-plan-nutricional.eventos`, `ms-catering.eventos` |
| Formatos | Ids UUID en texto, fechas `YYYY-MM-DD`, decimales como texto (`"2000.00"`). Los consumidores aceptan camelCase (productores .NET) y snake_case |

**Tabla de routing keys del grupo**

| Evento | Routing key | Productor |
|---|---|---|
| PlanNutricionalCreado / Actualizado / Finalizado / Cancelado | `plan_nutricional.creado` · `.actualizado` · `.finalizado` · `.cancelado` | ms-plan-nutricional |
| CalendarioEntregaCreado | `calendario.creado` | ms-catering |
| DireccionEntregaCambiada | `direccion_entrega.cambiada` | ms-catering |
| DiaSinEntregaMarcado | `dia_sin_entrega.marcado` | ms-catering |
| CalendarioEntregaCancelado / Completado | `calendario.cancelado` · `calendario.completado` | ms-catering |
| ServicioContratado | `servicio.contratado` *(a confirmar con ms-contratos-facturacion)* | ms-contratos-facturacion |
| ContratoCancelado / ContratoCompletado | `contrato.cancelado` · `contrato.completado` *(a confirmar)* | ms-contratos-facturacion |
| PacienteRegistrado | `paciente.registrado` | ms-pacientes |
| OrdenCancelada | `orden.cancelada` | ms-produccion-alimentos |

Los nombres de los eventos consumidos que figuran más abajo (`ContratoServicioRegistrado`,
`ContratoServicioCancelado`) eran la propuesta inicial; el nombre acordado es el del docx:
**`ServicioContratado`** (`tipoServicio`: `EVALUACION | ASESORAMIENTO | CATERING`) y **`ContratoCancelado`**.

---

## 2. Resumen — tabla para el documento del grupo

| Nombre del evento | Descripción | Estructura (JSON) | Productor | Consumidores |
|---|---|---|---|---|
| `PlanNutricionalCreado` | El nutricionista asignó un plan de 15 o 30 días a un paciente (HU-13, HU-15). | [§3.1](#31-plannutricionalcreado) | ms-plan-nutricional | ms-catering, ms-produccion-alimentos, ms-evaluacion-seguimiento |
| `PlanNutricionalActualizado` | Cambió la estructura del plan: días, tiempos de comida o recetas (HU-13, HU-15). | [§3.2](#32-plannutricionalactualizado) | ms-plan-nutricional | ms-produccion-alimentos |
| `PlanNutricionalFinalizado` | El plan llegó a su fin (estado FINALIZADO). | [§3.3](#33-plannutricionalfinalizado) | ms-plan-nutricional | ms-catering, ms-produccion-alimentos, ms-evaluacion-seguimiento |
| `PlanNutricionalCancelado` | El plan se canceló antes de terminar (estado CANCELADO). | [§3.4](#34-plannutricionalcancelado) | ms-plan-nutricional | ms-catering, ms-produccion-alimentos, ms-evaluacion-seguimiento |
| `ContratoServicioRegistrado` | *(consumido)* Se contrató un servicio con duración de 15 o 30 días (HU-19). | [§4.1](#41-contratoservicioregistrado--de-ms-contratos-facturacion) | ms-contratos-facturacion | ms-plan-nutricional, ms-catering |
| `EvaluacionCorporalRegistrada` | *(consumido)* Se registró una evaluación corporal del paciente (HU-07, HU-11). | [§4.2](#42-evaluacioncorporalregistrada--de-ms-evaluacion-seguimiento) | ms-evaluacion-seguimiento | ms-plan-nutricional |

---

## 3. Eventos que PRODUCE ms-plan-nutricional

Todos se publican **después** del `commit` del caso de uso, nunca antes: si la
transacción falla, el evento no debe existir (ver [§6](#6-cómo-se-implementaría)).

### 3.1 `PlanNutricionalCreado`

**Cuándo:** al terminar `CrearPlanUseCase` (`POST /planes`) o
`CrearPlanDesdePlantillaUseCase` (`POST /planes/desde-plantilla`). El plan nace `ACTIVO`.

```json
{
  "evento_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "tipo": "PlanNutricionalCreado",
  "version": 1,
  "ocurrido_en": "2026-01-01T14:30:00Z",
  "productor": "ms-plan-nutricional",
  "correlacion_id": "0b2f8d1e-3c4a-4b5d-9e6f-7a8b9c0d1e2f",
  "datos": {
    "plan_id": "11111111-1111-4111-8111-111111111111",
    "paciente_id": "22222222-2222-4222-8222-222222222222",
    "fecha_inicio": "2026-01-01",
    "fecha_fin": "2026-01-15",
    "duracion_dias": 15,
    "estado": "ACTIVO",
    "plantilla_origen_id": null,
    "necesidad": {
      "calorias": "2000.00",
      "proteinas": "120.00",
      "grasas": "60.00",
      "carbohidratos": "250.00"
    }
  }
}
```

| Consumidor | Para qué lo usa |
|---|---|
| **ms-catering** | Vincula `plan_id` al calendario de entregas del paciente (campo `plan_nutricional_id`, hoy se carga a mano) y guarda `fecha_inicio` para saber qué día del plan corresponde a cada entrega. |
| **ms-produccion-alimentos** | Registra que el paciente tiene un plan vigente entre esas fechas; las recetas llegan con `PlanNutricionalActualizado`. |
| **ms-evaluacion-seguimiento** | Asocia las evaluaciones del período a ese plan, para poder comparar la evolución contra el plan vigente (HU-11). |

### 3.2 `PlanNutricionalActualizado`

**Cuándo:** después de cualquier cambio de estructura: agregar o eliminar un día,
un tiempo de comida o una receta (también desde el catálogo).

Lleva el **plan completo** (*event-carried state transfer*): cocina no necesita
consultar a BC3 para saber qué preparar, y si se pierde un evento intermedio, el
siguiente trae el estado entero. Por eso se emite **uno por cambio**, sin deltas.

```json
{
  "evento_id": "a3d5f8c1-2b4e-4c6a-8d9f-0e1a2b3c4d5e",
  "tipo": "PlanNutricionalActualizado",
  "version": 1,
  "ocurrido_en": "2026-01-01T15:05:00Z",
  "productor": "ms-plan-nutricional",
  "correlacion_id": "0b2f8d1e-3c4a-4b5d-9e6f-7a8b9c0d1e2f",
  "datos": {
    "plan_id": "11111111-1111-4111-8111-111111111111",
    "paciente_id": "22222222-2222-4222-8222-222222222222",
    "fecha_inicio": "2026-01-01",
    "fecha_fin": "2026-01-15",
    "estado": "ACTIVO",
    "dias": [
      {
        "numero_dia": 1,
        "fecha": "2026-01-01",
        "tiempos_comida": [
          {
            "tipo": "DESAYUNO",
            "recetas": [
              {
                "receta_id": "33333333-3333-4333-8333-333333333333",
                "nombre": "Avena con frutas",
                "instrucciones": "Cocer la avena 5 minutos y añadir la fruta picada.",
                "cantidad": "250.00",
                "unidad": "gr"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

- `tipo` de tiempo de comida: `DESAYUNO`, `MEDIA_MANANA`, `ALMUERZO`, `MERIENDA`, `CENA`, `MEDIA_NOCHE`.
- `fecha` del día = `fecha_inicio + (numero_dia - 1)`; se envía calculada para que
  cocina no tenga que repetir la regla.

| Consumidor | Para qué lo usa |
|---|---|
| **ms-produccion-alimentos** | Mantiene su réplica de "qué recetas y porciones come cada paciente cada día". Con eso y las entregas confirmadas por ms-catering arma la **orden de producción** (HU-31, HU-32) y el **envasado por porción**. |

### 3.3 `PlanNutricionalFinalizado`

**Cuándo:** `PATCH /planes/{id}/estado` con `FINALIZADO`. Estado terminal.

```json
{
  "evento_id": "c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f",
  "tipo": "PlanNutricionalFinalizado",
  "version": 1,
  "ocurrido_en": "2026-01-15T22:00:00Z",
  "productor": "ms-plan-nutricional",
  "correlacion_id": "0b2f8d1e-3c4a-4b5d-9e6f-7a8b9c0d1e2f",
  "datos": {
    "plan_id": "11111111-1111-4111-8111-111111111111",
    "paciente_id": "22222222-2222-4222-8222-222222222222",
    "fecha_fin": "2026-01-15"
  }
}
```

| Consumidor | Para qué lo usa |
|---|---|
| **ms-catering** | Deja de asociar entregas futuras a este plan. |
| **ms-produccion-alimentos** | Deja de considerar el plan en las órdenes de producción. |
| **ms-evaluacion-seguimiento** | Puede proponer la evaluación de cierre del plan (HU-11). |

### 3.4 `PlanNutricionalCancelado`

**Cuándo:** `PATCH /planes/{id}/estado` con `CANCELADO`. Estado terminal.

```json
{
  "evento_id": "d4e5f6a7-b8c9-4d0e-9f1a-2b3c4d5e6f7a",
  "tipo": "PlanNutricionalCancelado",
  "version": 1,
  "ocurrido_en": "2026-01-08T10:00:00Z",
  "productor": "ms-plan-nutricional",
  "correlacion_id": "0b2f8d1e-3c4a-4b5d-9e6f-7a8b9c0d1e2f",
  "datos": {
    "plan_id": "11111111-1111-4111-8111-111111111111",
    "paciente_id": "22222222-2222-4222-8222-222222222222",
    "cancelado_el": "2026-01-08"
  }
}
```

| Consumidor | Para qué lo usa |
|---|---|
| **ms-catering** | Desvincula el plan del calendario. **No** cancela el calendario: eso depende del contrato (BC4), no del plan. |
| **ms-produccion-alimentos** | Saca al paciente de las órdenes de producción a partir de `cancelado_el`. |
| **ms-evaluacion-seguimiento** | Registra el corte en el historial de evolución del paciente. |

---

## 4. Eventos que CONSUME ms-plan-nutricional (lo que pido a los demás)

Son **propuestas**: el equipo productor decide el contrato final. Lo que necesito
de cada uno es, como mínimo, los campos marcados.

### 4.1 `ContratoServicioRegistrado` — de ms-contratos-facturacion

**Pedido a:** Joel Cesar Barco Pañuni (BC4). **HU de origen:** HU-19.

```json
{
  "evento_id": "e5f6a7b8-c9d0-4e1f-8a2b-3c4d5e6f7a8b",
  "tipo": "ContratoServicioRegistrado",
  "version": 1,
  "ocurrido_en": "2025-12-28T09:00:00Z",
  "productor": "ms-contratos-facturacion",
  "correlacion_id": "0b2f8d1e-3c4a-4b5d-9e6f-7a8b9c0d1e2f",
  "datos": {
    "contrato_id": "44444444-4444-4444-8444-444444444444",
    "paciente_id": "22222222-2222-4222-8222-222222222222",
    "tipo_servicio": "CATERING",
    "duracion_dias": 15,
    "fecha_inicio": "2026-01-01",
    "fecha_fin": "2026-01-15",
    "direccion_entrega": {
      "direccion": "Av. Banzer 123",
      "referencia": "Portón verde",
      "zona": "Equipetrol"
    }
  }
}
```

- `tipo_servicio`: `EVALUACION_CORPORAL`, `ASESORAMIENTO_NUTRICIONAL` o `CATERING`.
- `duracion_dias`: 15 o 30 (mismos valores que `DuracionPlan` en BC3).
- `direccion_entrega`: solo cuando `tipo_servicio = CATERING` (la necesita ms-catering).

**Qué haría BC3:** dejar registrado que el paciente tiene un contrato vigente con
esa duración, para proponer al nutricionista un plan de la misma duración y fechas.
Hoy el README marca el contrato activo como "referenciado por ID"; esto lo hace real.

### 4.2 `EvaluacionCorporalRegistrada` — de ms-evaluacion-seguimiento

**Pedido a:** Joel Cesar Barco Pañuni (BC2). **HU de origen:** HU-07, HU-11.

```json
{
  "evento_id": "f6a7b8c9-d0e1-4f2a-9b3c-4d5e6f7a8b9c",
  "tipo": "EvaluacionCorporalRegistrada",
  "version": 1,
  "ocurrido_en": "2026-01-15T11:00:00Z",
  "productor": "ms-evaluacion-seguimiento",
  "correlacion_id": "0b2f8d1e-3c4a-4b5d-9e6f-7a8b9c0d1e2f",
  "datos": {
    "evaluacion_id": "55555555-5555-4555-8555-555555555555",
    "paciente_id": "22222222-2222-4222-8222-222222222222",
    "fecha": "2026-01-15",
    "peso_kg": "78.40",
    "altura_cm": "172.00",
    "imc": "26.50",
    "masa_grasa_pct": "24.10",
    "masa_muscular_pct": "38.20"
  }
}
```

**Qué haría BC3:** marcar el plan activo del paciente como "con evaluación nueva"
para que el nutricionista revise `necesidad` y la recomendación (HU-11: "comparar
evaluaciones … para determinar ajustes en su plan alimenticio"). No modifica el
plan automáticamente: la decisión es del profesional.

---

## 5. Eventos de dominio que NO se publican

| Evento de dominio | Por qué no es de integración |
|---|---|
| `DiaAgregado`, `TiempoComidaAgregado`, `RecetaAgregada`, `RecetaEliminada` | Son pasos de edición. Hacia afuera viajan resumidos en `PlanNutricionalActualizado`. |
| `RecomendacionNutricionalModificada` | Es texto para el paciente; nadie fuera de BC3 decide nada con él. Si la app quiere avisar al paciente, la consulta por REST. |
| `RecetaCatalogoCreada` / `Actualizada` / `Desactivada` | El catálogo es interno: cuando una receta entra a un plan, se **copia** al plan y viaja dentro de `PlanNutricionalActualizado`. |
| `PlantillaPlanCreada` y su edición | Las plantillas son herramienta del nutricionista. Solo importa el plan resultante (`plantilla_origen_id`). |

---

## 6. Cómo está implementado

1. **Transactional Outbox.** Los métodos del agregado `PlanNutricional` anotan eventos de
   dominio (`domain/model/eventos.py`). `PlanNutricionalRepositoryImpl.guardar()` los traduce
   (`infrastructure/messaging/eventos_integracion.py`) e inserta una fila en `outbox` **en la misma
   sesión**: `get_db_session` confirma o revierte todo junto.
2. **Relay** (`infrastructure/messaging/outbox_relay.py`): tarea en segundo plano que cada 2 s toma
   los pendientes con `FOR UPDATE SKIP LOCKED`, publica con *publisher confirms* y marca
   `publicado_en`. Si RabbitMQ está caído, suma `intentos`, guarda `ultimo_error` y reintenta.
3. **Consumidor idempotente** (`infrastructure/messaging/consumidor.py`): cola
   `ms-plan-nutricional.eventos` ← `servicio.contratado`, `contrato.cancelado`. Cada mensaje se
   aplica en una transacción junto con su fila en `eventos_procesados` (inbox): un duplicado se ignora.
   Con `ASESORAMIENTO` se registra en `asesoramientos_habilitados`; `contrato.cancelado` lo desactiva.
4. **Esquema:** `migraciones/001_mensajeria.sql` (también incluido en `bd-ms-plan-nutricional.sql`).

## 7. Integraciones síncronas que ya existen (REST, con contrato Pact)

No son eventos, pero completan el mapa:

| Relación | Tipo | Estado |
|---|---|---|
| `app-paciente` → `GET /planes/{id}`, `GET /planes/paciente/{id}` | Consulta (HU-16, HU-18) | ✅ verificado (`pacts/app-paciente-ms-plan-nutricional.json`) |
| ms-plan-nutricional → `GET /pacientes/{id}` de ms-pacientes | Consulta | ⏳ pact generado, lo verifica ms-pacientes |

## 8. Pendientes por equipo

| Equipo | Qué necesito acordar |
|---|---|
| ms-contratos-facturacion (BC4) | Publicar `ContratoServicioRegistrado` con `tipo_servicio`, `duracion_dias`, fechas y `direccion_entrega` para catering. |
| ms-evaluacion-seguimiento (BC2) | Publicar `EvaluacionCorporalRegistrada`; confirmar nombres de las medidas. |
| ms-produccion-alimentos (BC6) | Confirmar que `PlanNutricionalActualizado` le alcanza para armar la orden de producción (¿necesita `descripcion` de la receta?). |
| ms-catering (BC5, propio) | Consumir `PlanNutricionalCreado` / `Cancelado` (ver `EVENTOS_INTEGRACION.md` de ms-catering). |
