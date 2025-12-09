"""
Conectores para servicios externos.

Este paquete contiene adaptadores para integrar con:
- LLMs (OpenAI, Anthropic)
- Vector stores (ChromaDB)
- Bases de datos externas
"""

from app.connectors.llm import OpenAIAdapter, AnthropicAdapter

__all__ = ["OpenAIAdapter", "AnthropicAdapter"]
