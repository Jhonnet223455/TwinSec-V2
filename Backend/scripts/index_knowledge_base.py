"""
Script para indexar manualmente el knowledge base.

Uso:
    python Backend/scripts/index_knowledge_base.py [--force]
    
Opciones:
    --force    Re-indexa aunque ya exista el índice
"""

import sys
from pathlib import Path

# Agregar la carpeta api al path
sys.path.append(str(Path(__file__).parent.parent / "api"))

from app.services.rag_service import RAGService
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Indexa el knowledge base para el sistema RAG"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-indexación aunque exista el índice"
    )
    
    args = parser.parse_args()
    
    print("🚀 TwinSec Studio - Indexación de Knowledge Base")
    print("=" * 60)
    
    # Rutas
    knowledge_base_path = Path(__file__).parent.parent / "knowledge_base"
    chroma_db_path = Path(__file__).parent.parent / "api" / "chroma_db"
    
    print(f"📚 Knowledge Base: {knowledge_base_path}")
    print(f"💾 ChromaDB: {chroma_db_path}")
    print("=" * 60)
    
    # Crear servicio RAG
    rag_service = RAGService(
        knowledge_base_path=str(knowledge_base_path),
        persist_directory=str(chroma_db_path)
    )
    
    # Inicializar (indexar)
    rag_service.initialize(force_reindex=args.force)
    
    # Mostrar estadísticas
    stats = rag_service.get_stats()
    
    print("\n" + "=" * 60)
    print("📊 Estadísticas del Índice")
    print("=" * 60)
    print(f"Total de documentos: {stats['total_documents']}")
    print(f"Total de chunks: {stats['total_chunks']}")
    print(f"Vector store inicializado: {stats['vectorstore_initialized']}")
    print(f"Modelo de embeddings: {stats['embedding_model']}")
    
    print("\n📂 Archivos indexados:")
    for file in stats['indexed_files']:
        print(f"  - {Path(file).name}")
    
    print("\n" + "=" * 60)
    print("✅ Indexación completada")
    print("=" * 60)
    
    # Prueba de búsqueda
    if stats['vectorstore_initialized']:
        print("\n🔍 Prueba de búsqueda semántica...")
        test_query = "water tank system mass balance equation"
        results = rag_service.retrieve_context(test_query, top_k=3)
        
        if results:
            print(f"\nResultados para: '{test_query}'")
            for i, result in enumerate(results, 1):
                print(f"\n[{i}] Score: {result['score']:.3f} | Source: {Path(result['source']).name}")
                print(f"    {result['content'][:200]}...")
        else:
            print("⚠️ No se encontraron resultados relevantes")
    
    print("\n🎉 Listo para usar el sistema RAG!")
    print("Ahora puedes iniciar la API y el LLM usará contexto de los libros.")


if __name__ == "__main__":
    main()
