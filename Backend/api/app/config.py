"""
Configuración de la aplicación
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Project Info
    PROJECT_NAME: str
    VERSION: str 
    API_V1_STR: str 
    
    # API Configuration
    API_HOST: str 
    API_PORT: int 
    API_DEBUG: bool 
    API_WORKERS: int 
    API_BASE_URL: str 
    
    # Security
    SECRET_KEY: str 
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    
    # Database
    DATABASE_URL: str 
    DATABASE_POOL_SIZE: int 
    DATABASE_MAX_OVERFLOW: int 
    
    # LLM Configuration
    LLM_PROVIDER: str 
    OPENAI_API_KEY: str 
    OPENAI_MODEL: str 
    OPENAI_TEMPERATURE: float 
    OPENAI_MAX_TOKENS: int
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT: str
    
    # Anthropic
    ANTHROPIC_API_KEY: str
    
    # Local LLM
    LOCAL_LLM_ENDPOINT: str

    # CORS
    CORS_ORIGINS: List[str] 
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Simulation Engine
    SIMULATION_MAX_DURATION: int 
    SIMULATION_DEFAULT_DT: float 
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int 
    WS_MESSAGE_QUEUE_SIZE: int 
    
    # OAuth (Social Login Providers)
    GOOGLE_CLIENT_ID: str 
    GOOGLE_CLIENT_SECRET: str 
    
    FACEBOOK_APP_ID: str 
    FACEBOOK_APP_SECRET: str 
    
    GITHUB_CLIENT_ID: str 
    GITHUB_CLIENT_SECRET: str 
    
    class Config:
        # Buscar .env en la carpeta api/, incluso si se ejecuta desde otro lugar
        env_file = os.environ.get('ENV_FILE', str(Path(__file__).parent.parent / ".env"))
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Se obtienen las configuraciones (cached)."""
    return Settings()
