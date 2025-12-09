"""
API Router para generación de modelos con LLM
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict
import logging

from app.database import get_db
from app.models import User, Model
# from app.routers.auth import get_current_user  # TODO: Implementar auth
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


# ========================================
# TEMPORAL: Mock auth para pruebas
# ========================================
async def get_current_user(db: Session = Depends(get_db)) -> User:
    """TEMPORAL: Retorna usuario mock para pruebas sin auth"""
    # Buscar o crear usuario de prueba
    user = db.query(User).filter(User.email == "test@twinsec.com").first()
    if not user:
        user = User(
            username="test_user",
            email="test@twinsec.com",
            hashed_password="mock_hash",  # No se usa en pruebas
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

router = APIRouter(
    prefix="/models",
    tags=["models"]
)


# ========================================
# SCHEMAS
# ========================================

class ModelGenerateRequest(BaseModel):
    """Request para generar un modelo con LLM"""
    prompt: str = Field(..., description="Descripción del sistema a modelar")
    model_type: str = Field(..., description="Tipo de modelo (tank, microgrid, hvac, etc.)")
    use_rag: bool = Field(default=True, description="Usar RAG para enriquecer el prompt")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A water tank with inlet valve, outlet valve, and level sensor. Tank capacity 10m3, max flow 0.5 m3/s.",
                "model_type": "tank",
                "use_rag": True
            }
        }


class ModelGenerateResponse(BaseModel):
    """Response de generación de modelo"""
    success: bool
    model: Dict
    model_id: int
    llm_request_id: int
    metadata: Dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "model": {"metadata": {}, "solver": {}, "components": []},
                "model_id": 123,
                "llm_request_id": 456,
                "metadata": {
                    "cost_usd": 0.0012,
                    "latency_ms": 2345,
                    "total_tokens": 1750,
                    "rag_context_used": True,
                    "rag_fragments_count": 5
                }
            }
        }


class ModelListResponse(BaseModel):
    """Response para listado de modelos"""
    success: bool
    models: list
    total: int


# ========================================
# ENDPOINTS
# ========================================

@router.post("/generate", response_model=ModelGenerateResponse)
async def generate_model(
    request: ModelGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera un modelo OT completo usando LLM + RAG.
    
    **Flujo:**
    1. Usuario envía prompt describiendo el sistema
    2. RAG recupera contexto relevante de libros (si use_rag=True)
    3. Prompt se enriquece con teoría técnica
    4. LLM (OpenAI/Anthropic) genera JSON del modelo
    5. Se valida contra schema twinsec_model_v1.json
    6. Se guarda en BD (Model + LLMRequest)
    
    **Ejemplo de uso:**
    ```python
    response = requests.post(
        "http://localhost:8000/api/v1/models/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prompt": "A simple water tank with PID level control",
            "model_type": "tank",
            "use_rag": True
        }
    )
    ```
    """
    try:
        logger.info(f"Generando modelo '{request.model_type}' para usuario {current_user.id}")
        
        # Obtener servicio LLM
        llm_service = get_llm_service()
        
        # Generar modelo
        result = await llm_service.generate_model(
            user_prompt=request.prompt,
            model_type=request.model_type,
            user_id=current_user.id,
            db=db,
            use_rag=request.use_rag
        )
        
        # Guardar modelo en BD
        model = Model(
            name=f"{request.model_type}_{result['llm_request_id']}",
            description=request.prompt[:200],  # Truncar descripción
            model_type=request.model_type,
            version="1.0",
            content=result["model"],  # Corregido: content, no json_content
            llm_prompt=request.prompt,
            llm_provider=result["metadata"].get("provider"),
            llm_model=result["metadata"].get("model"),
            owner_id=current_user.id  # Corregido: owner_id, no created_by
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        logger.info(f"✅ Modelo guardado en BD (ID: {model.id})")
        
        return ModelGenerateResponse(
            success=True,
            model=result["model"],
            model_id=model.id,
            llm_request_id=result["llm_request_id"],
            metadata=result["metadata"]
        )
    
    except Exception as e:
        logger.error(f"❌ Error al generar modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar modelo: {str(e)}"
        )


@router.get("/", response_model=ModelListResponse)
async def list_models(
    skip: int = 0,
    limit: int = 50,
    model_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista los modelos del usuario actual.
    
    **Filtros:**
    - `model_type`: Filtrar por tipo (tank, microgrid, hvac, etc.)
    - `skip`, `limit`: Paginación
    """
    query = db.query(Model).filter(Model.owner_id == current_user.id)
    
    if model_type:
        query = query.filter(Model.model_type == model_type)
    
    total = query.count()
    models = query.offset(skip).limit(limit).all()
    
    return ModelListResponse(
        success=True,
        models=[{
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "model_type": m.model_type,
            "version": m.version,
            "created_at": m.created_at.isoformat()
        } for m in models],
        total=total
    )


@router.get("/{model_id}")
async def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene un modelo por ID.
    """
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.owner_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo no encontrado"
        )
    
    return {
        "success": True,
        "model": {
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "model_type": model.model_type,
            "version": model.version,
            "content": model.content,  # Corregido: content, no json_content
            "created_at": model.created_at.isoformat()
        }
    }


@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un modelo.
    """
    model = db.query(Model).filter(
        Model.id == model_id,
        Model.owner_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo no encontrado"
        )
    
    db.delete(model)
    db.commit()
    
    logger.info(f"Modelo {model_id} eliminado por usuario {current_user.id}")
    
    return {"success": True, "message": "Modelo eliminado"}
