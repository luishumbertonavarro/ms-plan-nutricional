from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5434/db_plan_nutricional"
    app_env: str = "development"
    log_level: str = "INFO"
    # URL base del microservicio de Pacientes (BC externo), usada por PacienteGatewayHttp.
    pacientes_base_url: str = "http://localhost:8001"

    # Service Discovery (Consul). Vacío = no se registra (desarrollo local y tests).
    servicio_nombre: str = "ms-plan-nutricional"
    servicio_puerto: int = 8000
    consul_url: str = ""

    # Broker (RabbitMQ). Vacío = no arrancan ni el relay del outbox ni el consumidor.
    rabbitmq_url: str = ""
    rabbitmq_exchange: str = "nurtricenter.events"
    rabbitmq_cola: str = "ms-plan-nutricional.eventos"
    outbox_intervalo_segundos: float = 2.0

    # Seguridad: el token lo emite el api-gateway; aquí se valida con el mismo secreto e issuer.
    auth_habilitada: bool = False
    jwt_secret: str = "nurtricenter-secreto-compartido-2026"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "nurtricenter-gateway"


settings = Settings()
