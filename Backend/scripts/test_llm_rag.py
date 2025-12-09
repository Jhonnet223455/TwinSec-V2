"""
Script de ejemplo para probar el sistema LLM + RAG

Este script demuestra cómo usar el servicio LLM para generar modelos OT.

ANTES DE EJECUTAR:
1. Instalar dependencias: pip install -r Backend/requirements.txt
2. Configurar .env con OPENAI_API_KEY
3. Ejecutar migración: alembic upgrade head
4. Subir libros a Backend/knowledge_base/books/
5. Indexar: python Backend/scripts/index_knowledge_base.py
"""

import asyncio
import sys
from pathlib import Path


# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from app.database import get_db, engine
from app.models import Base, User
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from sqlalchemy.orm import Session


# ========================================
# EJEMPLOS DE PROMPTS
# ========================================

EXAMPLES = {
    "tank_simple": {
        "prompt": """A simple water tank system:
- Tank capacity: 10 m³
- Inlet valve with max flow 0.5 m³/s
- Outlet valve with constant flow 0.2 m³/s
- Level sensor (0-10 meters)
- Initial level: 5 meters""",
        "model_type": "tank"
    },
    
    "tank_pid": {
        "prompt": """Water tank with PID level control:
- Tank capacity: 15 m³, cross-sectional area 3 m²
- Inlet valve with PID-controlled flow (max 0.8 m³/s)
- Outlet valve with constant flow 0.3 m³/s
- Level sensor with 1% noise
- PID controller: Kp=2.0, Ki=0.5, Kd=0.1
- Setpoint: 7 meters
- Initial level: 3 meters""",
        "model_type": "tank"
    },
    
    "tanks_interconnected": {
        "prompt": """Two interconnected water tanks:
- Tank 1: 20 m³ capacity, receives input flow
- Tank 2: 15 m³ capacity, receives overflow from Tank 1
- Connecting pipe: diameter 0.15m, flow based on level difference
- Tank 1 inlet valve: max 1.0 m³/s
- Tank 2 outlet valve: max 0.5 m³/s
- Level sensors on both tanks
- Cascading control: Tank 1 controls input, Tank 2 controls output""",
        "model_type": "tank"
    },
    
    "hvac": {
        "prompt": """HVAC system for a 200 m² office:
- Heating coil: 50 kW max power
- Cooling coil: 40 kW max power
- Air handler: variable speed fan (0-100%)
- Room temperature sensor
- Outdoor temperature input
- PI temperature controller (setpoint: 22°C)
- Heat capacity of room: 240 kJ/K
- Heat loss coefficient: 0.5 kW/K""",
        "model_type": "hvac"
    },
    
    "microgrid": {
        "prompt": """Simple microgrid system:
- Solar PV: 100 kW peak, varies with irradiance
- Battery: 200 kWh capacity, 80 kW max charge/discharge
- Load: variable 30-60 kW
- Grid connection: bidirectional, max 50 kW
- Energy management system with 3 states: grid-connected, islanded, charging
- SOC constraints: 20-90%""",
        "model_type": "microgrid"
    }
}


# ========================================
# FUNCIONES AUXILIARES
# ========================================

def create_test_user(db: Session) -> User:
    """Crea usuario de prueba (o lo recupera si existe)"""
    user = db.query(User).filter(User.username == "testuser").first()
    
    if not user:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$dummy.hash"  # No necesitamos auth real
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Usuario de prueba creado (ID: {user.id})")
    else:
        print(f"✅ Usuario de prueba existente (ID: {user.id})")
    
    return user


def test_rag_search():
    """Prueba la búsqueda RAG"""
    print("\n" + "="*60)
    print("🔍 TESTING RAG SEARCH")
    print("="*60)
    
    rag = get_rag_service()
    
    if rag.vectorstore is None:
        print("⚠️  RAG no inicializado. Ejecuta: python Backend/scripts/index_knowledge_base.py")
        return
    
    queries = [
        "PID controller tuning",
        "water tank differential equation",
        "transfer function state space"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        results = rag.retrieve_context(query, top_k=3, min_relevance_score=0.5)
        
        if results:
            print(f"   Encontrados {len(results)} fragmentos relevantes:")
            for i, r in enumerate(results, 1):
                print(f"   {i}. Score: {r['score']:.2f} | Source: {r['metadata']['source'][:50]}")
                print(f"      Content: {r['content'][:100]}...")
        else:
            print("   ❌ No se encontraron resultados relevantes")


async def test_model_generation(example_name: str, use_rag: bool = True):
    """Prueba la generación de un modelo"""
    print("\n" + "="*60)
    print(f"🚀 TESTING MODEL GENERATION: {example_name}")
    print("="*60)
    
    if example_name not in EXAMPLES:
        print(f"❌ Ejemplo '{example_name}' no existe. Opciones: {list(EXAMPLES.keys())}")
        return
    
    example = EXAMPLES[example_name]
    
    # Obtener DB session y usuario de prueba
    db = next(get_db())
    user = create_test_user(db)
    
    # Obtener servicio LLM
    llm_service = get_llm_service()
    
    print(f"\n📝 Prompt:")
    print(example["prompt"])
    print(f"\n🏷️  Model Type: {example['model_type']}")
    print(f"🔧 RAG Enabled: {use_rag}")
    
    print("\n⏳ Generando modelo (esto puede tardar 2-5 segundos)...")
    
    try:
        result = await llm_service.generate_model(
            user_prompt=example["prompt"],
            model_type=example["model_type"],
            user_id=user.id,
            db=db,
            use_rag=use_rag
        )
        
        print("\n✅ MODELO GENERADO EXITOSAMENTE")
        print("\n📊 Metadata:")
        print(f"   - Cost: ${result['metadata']['cost_usd']:.6f} USD")
        print(f"   - Latency: {result['metadata']['latency_ms']}ms")
        print(f"   - Total tokens: {result['metadata']['total_tokens']}")
        print(f"   - RAG context used: {result['metadata']['rag_context_used']}")
        if result['metadata']['rag_context_used']:
            print(f"   - RAG fragments: {result['metadata']['rag_fragments_count']}")
        print(f"   - LLM Request ID: {result['llm_request_id']}")
        
        # Mostrar resumen del modelo generado
        model = result["model"]
        print("\n📦 Modelo generado:")
        print(f"   - Name: {model['metadata']['name']}")
        print(f"   - Description: {model['metadata']['description']}")
        print(f"   - Type: {model['metadata']['model_type']}")
        print(f"   - Solver: {model['solver']['method']} (dt={model['solver']['timestep']}s)")
        print(f"   - Duration: {model['solver']['duration']}s")
        print(f"   - Components: {len(model['components'])}")
        
        # Listar componentes
        print("\n🔧 Componentes:")
        for comp in model['components']:
            print(f"   - {comp['id']} ({comp['type']})")
        
        # Listar señales
        print(f"\n📡 Señales: {len(model['signals'])}")
        for sig in model['signals'][:5]:  # Mostrar primeras 5
            print(f"   - {sig['id']} ({sig['type']}, unit: {sig.get('unit', 'N/A')})")
        
        if len(model['signals']) > 5:
            print(f"   ... y {len(model['signals']) - 5} más")
        
        # Listar widgets HMI
        print(f"\n🖥️  HMI Widgets: {len(model.get('hmi', []))}")
        for widget in model.get('hmi', [])[:3]:
            print(f"   - {widget['type']}: {widget.get('signal', 'N/A')}")
        
        db.close()
        
        return result
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.close()


# ========================================
# MAIN
# ========================================

async def main():
    """Función principal"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   TwinSec Studio - LLM + RAG Model Generation Test       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Crear tablas si no existen
    print("📊 Verificando base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos lista")
    
    # Test 1: Búsqueda RAG
    test_rag_search()
    
    # Test 2: Generación de modelo simple (SIN RAG)
    print("\n" + "="*60)
    print("Test 1: Modelo simple SIN RAG")
    print("="*60)
    await test_model_generation("tank_simple", use_rag=False)
    
    # Test 3: Generación de modelo con PID (CON RAG)
    print("\n" + "="*60)
    print("Test 2: Modelo con PID CON RAG")
    print("="*60)
    await test_model_generation("tank_pid", use_rag=True)
    
    print("\n" + "="*60)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*60)
    print("""
Próximos pasos:
1. Revisar los modelos generados en la BD
2. Probar otros ejemplos: 'tanks_interconnected', 'hvac', 'microgrid'
3. Implementar Objetivo 2: Inyección de ataques
    """)


if __name__ == "__main__":
    asyncio.run(main())
