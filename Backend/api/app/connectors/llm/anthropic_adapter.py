"""
Conector para Anthropic Claude API.

Soporta:
- Claude Sonnet 4.5 (recomendado para producción)
- Claude Opus (máxima calidad)
- Claude Haiku (más rápido y económico)
"""

import anthropic
from typing import Dict, Optional
import json
import logging
from datetime import datetime

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnthropicAdapter:
    """
    Adaptador para Anthropic Claude API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4.5",
        temperature: float = 0.0,
        max_tokens: int = 4096
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Cliente Anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        logger.info(f"Anthropic adapter inicializado con modelo: {model}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Genera una respuesta con Claude.
        """
        start_time = datetime.now()
        
        try:
            # Llamar a Claude
            logger.info(f"Generando respuesta con {self.model}...")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt if system_prompt else "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Calcular latencia
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Extraer respuesta
            content = message.content[0].text
            
            # Uso de tokens
            usage = {
                "prompt_tokens": message.usage.input_tokens,
                "completion_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens
            }
            
            logger.info(f"✅ Respuesta generada ({latency_ms}ms, {usage['total_tokens']} tokens)")
            
            return {
                "content": content,
                "finish_reason": message.stop_reason,
                "usage": usage,
                "latency_ms": latency_ms
            }
        
        except Exception as e:
            logger.error(f"Error al generar respuesta: {str(e)}")
            raise
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Genera una respuesta en formato JSON.
        """
        if system_prompt:
            system_prompt += "\n\nYou MUST respond with valid JSON only."
        else:
            system_prompt = "You are a helpful assistant that responds with valid JSON only."
        
        response = self.generate(prompt, system_prompt)
        
        try:
            json_content = json.loads(response["content"])
            response["parsed_json"] = json_content
            response["validation_error"] = None
            return response
        except json.JSONDecodeError as e:
            response["parsed_json"] = None
            response["validation_error"] = f"Invalid JSON: {str(e)}"
            return response
    
    def estimate_cost(self, usage: Dict) -> float:
        """
        Estima el costo.
        
        Tarifas (Nov 2025):
        - claude-sonnet-4.5: $3/1M input, $15/1M output
        - claude-opus: $15/1M input, $75/1M output
        - claude-haiku: $0.25/1M input, $1.25/1M output
        """
        rates = {
            "claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }
        
        model_rates = rates.get(self.model, rates["claude-sonnet-4.5"])
        
        input_cost = (usage["prompt_tokens"] / 1_000_000) * model_rates["input"]
        output_cost = (usage["completion_tokens"] / 1_000_000) * model_rates["output"]
        
        return round(input_cost + output_cost, 6)
