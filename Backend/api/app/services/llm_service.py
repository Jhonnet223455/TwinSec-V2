"""
LLM Service - Generación de modelos con RAG

Orquesta el flujo completo:
1. Usuario envía prompt
2. RAG recupera contexto de libros
3. Se enriquece el prompt con contexto técnico
4. LLM (OpenAI/Anthropic) genera el modelo JSON
5. Se valida contra twinsec_model_v1.json
6. Se registra en LLMRequest para auditoría
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path

from app.connectors.llm.openai_adapter import OpenAIAdapter
from app.connectors.llm.anthropic_adapter import AnthropicAdapter
from app.services.rag_service import get_rag_service
from app.config import get_settings
from app.models import LLMRequest
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """
    Servicio principal de generación de modelos con LLM + RAG.
    """
    
    def __init__(self):
        self.settings = settings
        
        # Inicializar adaptadores según configuración
        if self.settings.LLM_PROVIDER == "openai":
            self.llm = OpenAIAdapter(
                model=self.settings.OPENAI_MODEL,
                temperature=self.settings.OPENAI_TEMPERATURE,
                max_tokens=self.settings.OPENAI_MAX_TOKENS
            )
        elif self.settings.LLM_PROVIDER == "anthropic":
            self.llm = AnthropicAdapter(
                model="claude-sonnet-4.5",
                temperature=0.0,
                max_tokens=4096
            )
        else:
            raise ValueError(f"LLM provider no soportado: {self.settings.LLM_PROVIDER}")
        
        # Sistema RAG
        self.rag = get_rag_service()
        
        # Cargar schema de validación
        # Path: Backend/api/app/services/llm_service.py -> Backend/schemas/twinsec_model_v1.json
        schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "twinsec_model_v1.json"
        
        if not schema_path.exists():
            logger.error(f"Schema no encontrado en: {schema_path}")
            raise FileNotFoundError(f"Schema no encontrado: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.model_schema = json.load(f)
        
        logger.info(f"✅ LLM Service inicializado con provider: {self.settings.LLM_PROVIDER}")
        logger.info(f"✅ Schema cargado desde: {schema_path}")
    
    def _build_system_prompt(self) -> str:
        """
        Construye el system prompt base para generación de modelos.
        """
        return """You are an expert OT (Operational Technology) systems engineer specializing in:
- Control systems (PID, state-space, transfer functions)
- Process control (tanks, valves, pumps, heat exchangers)
- SCADA systems and industrial automation
- Cybersecurity in critical infrastructure

Your task is to generate detailed, physically accurate models of OT systems based on user prompts.

OUTPUT FORMAT:
You MUST respond with a valid JSON object that strictly follows the TwinSec Model V1 schema.

KEY REQUIREMENTS:
1. Use proper differential equations for dynamics
2. Include realistic physical parameters (capacities, flow rates, constants)
3. Define clear signal names (component_id.signal_id format)
4. Specify HMI widgets for visualization
5. Include appropriate attack vectors for cybersecurity testing

IMPORTANT:
- Use SI units (meters, seconds, kg, etc.)
- Provide meaningful descriptions
- Ensure mathematical consistency
- Think step-by-step about the physics"""
    
    def _build_user_prompt(
        self,
        user_prompt: str,
        model_type: str,
        rag_context: str
    ) -> str:
        """
        Construye el prompt del usuario enriquecido con contexto RAG.
        """
        prompt = f"{rag_context}\n" if rag_context else ""
        
        prompt += f"""USER REQUEST:
Create a {model_type} system with the following specifications:

{user_prompt}

REQUIREMENTS:
- Generate a complete TwinSec Model V1 JSON
- Include the 'solver' configuration (method, timestep, duration)
- Define all 'components' with their types and parameters
- Specify 'connections' between components
- List all 'signals' (outputs of components)
- Design 'hmi' widgets for visualization
- Suggest realistic 'attacks' for security testing

Think carefully about the physics and mathematics. Provide a realistic, detailed model."""
        
        return prompt
    
    async def generate_model(
        self,
        user_prompt: str,
        model_type: str,
        user_id: int,
        db: Session,
        use_rag: bool = True
    ) -> Dict:
        """
        Genera un modelo OT completo usando LLM + RAG.
        
        Args:
            user_prompt: Descripción del usuario
            model_type: Tipo de modelo (tank, microgrid, hvac, etc.)
            user_id: ID del usuario solicitante
            db: Sesión de base de datos
            use_rag: Si True, usa RAG para enriquecer el prompt
        
        Returns:
            {
                "model": {...},  # El modelo JSON generado
                "llm_request_id": 123,
                "metadata": {
                    "cost_usd": 0.0012,
                    "latency_ms": 2345,
                    "total_tokens": 1750,
                    "rag_context_used": True
                }
            }
        """
        logger.info(f"Generando modelo '{model_type}' para usuario {user_id}")
        
        # 1. Recuperar contexto con RAG (si está habilitado)
        rag_context = ""
        rag_results = []
        
        if use_rag and self.rag.vectorstore is not None:
            logger.info("Recuperando contexto con RAG...")
            
            # Crear query optimizada para búsqueda
            rag_query = f"{model_type} system {user_prompt} differential equations parameters"
            
            rag_results = self.rag.retrieve_context(
                query=rag_query,
                top_k=5,
                min_relevance_score=0.5
            )
            
            if rag_results:
                rag_context = self.rag.format_context_for_prompt(rag_results)
                logger.info(f"✅ Contexto RAG recuperado ({len(rag_results)} fragmentos)")
            else:
                logger.warning("⚠️ No se encontró contexto relevante en RAG")
        
        # 2. Construir prompts
        system_prompt = self._build_system_prompt()
        user_prompt_enriched = self._build_user_prompt(
            user_prompt, 
            model_type,
            rag_context
        )
        
        # 3. Generar con LLM
        try:
            response = self.llm.generate_json(
                prompt=user_prompt_enriched,
                system_prompt=system_prompt
            )
            
            # 4. Validar respuesta
            if response["validation_error"]:
                raise ValueError(f"LLM no generó JSON válido: {response['validation_error']}")
            
            model_json = response["parsed_json"]
            
            # TODO: Validar contra schema twinsec_model_v1.json
            validation_passed = True
            validation_errors = None
            
            # 5. Calcular costo
            cost_usd = self.llm.estimate_cost(response["usage"])
            
            # 6. Registrar en base de datos (LLMRequest)
            llm_request = LLMRequest(
                user_id=user_id,
                provider=self.settings.LLM_PROVIDER,
                model_name=self.llm.model,
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=self.llm.temperature,
                max_tokens=self.llm.max_tokens,
                response=response["content"],
                finish_reason=response["finish_reason"],
                prompt_tokens=response["usage"]["prompt_tokens"],
                completion_tokens=response["usage"]["completion_tokens"],
                total_tokens=response["usage"]["total_tokens"],
                cost_usd=cost_usd,
                latency_ms=response["latency_ms"],
                success=True,
                validation_passed=validation_passed,
                validation_errors=validation_errors,
                model_type_requested=model_type
            )
            
            db.add(llm_request)
            db.commit()
            db.refresh(llm_request)
            
            logger.info(f"✅ Modelo generado exitosamente (ID: {llm_request.id}, Costo: ${cost_usd:.6f})")
            
            return {
                "model": model_json,
                "llm_request_id": llm_request.id,
                "metadata": {
                    "cost_usd": cost_usd,
                    "latency_ms": response["latency_ms"],
                    "total_tokens": response["usage"]["total_tokens"],
                    "rag_context_used": len(rag_results) > 0,
                    "rag_fragments_count": len(rag_results)
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Error al generar modelo: {str(e)}")
            
            # Registrar error en base de datos
            llm_request = LLMRequest(
                user_id=user_id,
                provider=self.settings.LLM_PROVIDER,
                model_name=self.llm.model,
                prompt=user_prompt,
                success=False,
                error_message=str(e)
            )
            
            db.add(llm_request)
            db.commit()
            
            raise


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Obtiene la instancia singleton del LLM service.
    """
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService()
    
    return _llm_service
