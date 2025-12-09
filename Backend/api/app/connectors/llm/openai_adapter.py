"""
Conector para OpenAI API.

Soporta:
- GPT-4o-mini (recomendado para producción)
- GPT-4 (máxima calidad)
- GPT-4-turbo (balance calidad/costo)
"""

import openai
from typing import Dict, Optional, List
import json
import logging
from datetime import datetime

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIAdapter:
    """
    Adaptador para OpenAI API.
    
    Maneja la comunicación con OpenAI y el formato de requests/responses.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 4096
    ):
        """
        Args:
            api_key: API key de OpenAI (si no se provee, usa settings)
            model: Modelo a usar
            temperature: Creatividad (0.0 = determinístico, 1.0 = creativo)
            max_tokens: Máximo de tokens en la respuesta
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Configurar cliente OpenAI
        openai.api_key = self.api_key
        
        logger.info(f"OpenAI adapter inicializado con modelo: {model}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[str] = "json_object"
    ) -> Dict:
        """
        Genera una respuesta del LLM.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Instrucciones del sistema
            response_format: "json_object" para forzar JSON, o None
        
        Returns:
            {
                "content": "respuesta del LLM",
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": 250,
                    "completion_tokens": 1500,
                    "total_tokens": 1750
                },
                "latency_ms": 2345
            }
        """
        start_time = datetime.now()
        
        try:
            # Construir mensajes
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Llamar a OpenAI
            logger.info(f"Generando respuesta con {self.model}...")
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": response_format} if response_format else None
            )
            
            # Calcular latencia
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Extraer respuesta
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Uso de tokens
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info(f"✅ Respuesta generada ({latency_ms}ms, {usage['total_tokens']} tokens)")
            
            return {
                "content": content,
                "finish_reason": finish_reason,
                "usage": usage,
                "latency_ms": latency_ms
            }
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error al generar respuesta: {str(e)}")
            raise
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None
    ) -> Dict:
        """
        Genera una respuesta en formato JSON.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Instrucciones del sistema
            schema: JSON Schema esperado (para validación)
        
        Returns:
            Dict con el JSON parseado
        """
        # Agregar instrucción de JSON al system prompt
        if system_prompt:
            system_prompt += "\n\nYou MUST respond with valid JSON only. No markdown, no explanations."
        else:
            system_prompt = "You are a helpful assistant that responds with valid JSON only."
        
        # Generar respuesta
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json_object"
        )
        
        # Parsear JSON
        try:
            json_content = json.loads(response["content"])
            response["parsed_json"] = json_content
            response["validation_error"] = None
            
            # Validar contra schema si se provee
            if schema:
                # TODO: Implementar validación con jsonschema
                pass
            
            return response
        
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON: {str(e)}")
            response["parsed_json"] = None
            response["validation_error"] = f"Invalid JSON: {str(e)}"
            
            return response
    
    def estimate_cost(self, usage: Dict) -> float:
        """
        Estima el costo de una request basándose en el uso de tokens.
        
        Tarifas (Nov 2025):
        - gpt-4o-mini: $0.150/1M input, $0.600/1M output
        - gpt-4: $30/1M input, $60/1M output
        - gpt-4-turbo: $10/1M input, $30/1M output
        
        Args:
            usage: Dict con prompt_tokens y completion_tokens
        
        Returns:
            Costo en USD
        """
        rates = {
            "gpt-4o-mini": {"input": 0.150, "output": 0.600},
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        }
        
        model_rates = rates.get(self.model, rates["gpt-4o-mini"])
        
        input_cost = (usage["prompt_tokens"] / 1_000_000) * model_rates["input"]
        output_cost = (usage["completion_tokens"] / 1_000_000) * model_rates["output"]
        
        total_cost = input_cost + output_cost
        
        return round(total_cost, 6)
