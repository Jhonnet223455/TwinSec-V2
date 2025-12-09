"""
Modelo SQLAlchemy para historial de peticiones a LLMs
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


def generate_uuid():
    """Genera un UUID como string"""
    return str(uuid.uuid4())


class LLMRequest(Base):
    """
    Registro de peticiones realizadas a modelos de lenguaje grande (LLMs).
    
    Permite auditoría de:
    - Costos de API (cada llamada tiene un costo)
    - Debugging (qué prompt generó qué modelo)
    - Compliance (verificar que no se envió información sensible)
    - Performance (latencia y tasa de éxito)
    
    Relaciones:
        - user: Usuario que realizó la petición
        - model: Modelo de simulación generado (si tuvo éxito)
    """
    __tablename__ = "llm_requests"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), unique=True, default=generate_uuid, nullable=False, index=True)
    
    # Usuario que realizó la petición
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="llm_requests")
    
    # Modelo generado (si tuvo éxito)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    generated_model = relationship("Model")
    
    # Proveedor y modelo de LLM
    provider = Column(
        String(50),
        nullable=False,
        index=True
    )  # 'openai', 'anthropic', 'azure_openai', 'local'
    
    model_name = Column(String(100), nullable=False)
    # Ejemplos: 'gpt-4o-mini', 'gpt-4', 'claude-3-opus-20240229', 'claude-sonnet-4.5'
    
    # Contenido de la petición
    prompt = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)  # System prompt si se usó
    
    # Parámetros de generación
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    top_p = Column(Float, nullable=True)
    other_params = Column(JSON, nullable=True)  # Otros parámetros específicos del provider
    
    # Respuesta del LLM
    response = Column(Text, nullable=True)  # El JSON generado (crudo)
    finish_reason = Column(String(50), nullable=True)  # 'stop', 'length', 'content_filter'
    
    # Métricas de uso
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Costos (calculados según tarifas del provider)
    cost_usd = Column(Float, nullable=True)
    # Ejemplo: OpenAI GPT-4o-mini ~$0.15/1M input tokens, ~$0.60/1M output tokens
    
    # Performance
    latency_ms = Column(Integer, nullable=True)  # Tiempo de respuesta en milisegundos
    
    # Estado de la petición
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)  # 'rate_limit', 'invalid_request', etc.
    
    # Validación del JSON generado
    validation_passed = Column(Boolean, nullable=True)
    validation_errors = Column(JSON, nullable=True)  # Errores de validación contra el schema
    
    # Contexto adicional
    model_type_requested = Column(String(50), nullable=True)  # 'tank', 'microgrid', 'hvac', etc.
    user_metadata = Column(JSON, nullable=True)  # Metadata adicional del contexto
    
    # IP y User Agent (para seguridad)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)  # Cuando terminó la petición
    
    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<LLMRequest(id={self.id}, {status}, provider='{self.provider}', model='{self.model_name}', tokens={self.total_tokens})>"
    
    def to_dict(self):
        """Convierte la petición a diccionario para serialización"""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "provider": self.provider,
            "model_name": self.model_name,
            "success": self.success,
            "prompt": self.prompt[:200] + "..." if self.prompt and len(self.prompt) > 200 else self.prompt,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "validation_passed": self.validation_passed,
            "model_type_requested": self.model_type_requested,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def calculate_cost(self):
        """
        Calcula el costo de la petición según tarifas del provider.
        
        Tarifas aproximadas (Oct 2025):
        - GPT-4o-mini: $0.150/1M input, $0.600/1M output
        - GPT-4: $30/1M input, $60/1M output
        - Claude Sonnet 4.5: $3/1M input, $15/1M output
        - Claude Opus: $15/1M input, $75/1M output
        """
        if not self.prompt_tokens or not self.completion_tokens:
            return None
        
        # Tarifas por provider/model (USD por millón de tokens)
        rates = {
            "openai": {
                "gpt-4o-mini": {"input": 0.150, "output": 0.600},
                "gpt-4o": {"input": 2.50, "output": 10.00},
                "gpt-4": {"input": 30.00, "output": 60.00},
                "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            },
            "anthropic": {
                "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
                "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
                "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
                "claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
            },
            "azure_openai": {
                # Usar las mismas tarifas que OpenAI
                "gpt-4o-mini": {"input": 0.150, "output": 0.600},
                "gpt-4": {"input": 30.00, "output": 60.00},
            }
        }
        
        provider_rates = rates.get(self.provider, {})
        model_rates = provider_rates.get(self.model_name)
        
        if not model_rates:
            # Modelo desconocido, usar tarifa genérica conservadora
            model_rates = {"input": 5.00, "output": 15.00}
        
        input_cost = (self.prompt_tokens / 1_000_000) * model_rates["input"]
        output_cost = (self.completion_tokens / 1_000_000) * model_rates["output"]
        
        total_cost = input_cost + output_cost
        self.cost_usd = round(total_cost, 6)  # 6 decimales para precisión
        
        return self.cost_usd
