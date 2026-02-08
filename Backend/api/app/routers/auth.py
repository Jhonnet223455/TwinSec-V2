"""
API Router para autenticación con JWT y OAuth (Google, Facebook)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import timedelta
import logging
import httpx

from app.database import get_db
from app.models import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# ========================================
# SCHEMAS
# ========================================

class UserRegisterRequest(BaseModel):
    """Request para registro de usuario"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Response con información del usuario"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response con tokens de autenticación"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordResetRequest(BaseModel):
    """Request para reset de contraseña"""
    email: EmailStr


# ========================================
# DEPENDENCIAS
# ========================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtiene el usuario actual desde el token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    return user


# ========================================
# ENDPOINTS
# ========================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario.
    """
    # Verificar si el email ya existe
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verificar si el username ya existe
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Crear nuevo usuario
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"New user registered: {user.email}")
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login con email/username y password.
    Retorna access_token y refresh_token.
    """
    # Buscar usuario por email o username
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    # Crear tokens
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.id}
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene información del usuario autenticado.
    """
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh del access token usando el refresh token.
    """
    payload = decode_access_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id: int = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Crear nuevo access token
    new_access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token,  # Mantener el mismo refresh token
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Envía email para reset de contraseña.
    TODO: Implementar envío de email.
    """
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    # No revelar si el email existe o no (seguridad)
    logger.info(f"Password reset requested for: {reset_data.email}")
    
    return {
        "message": "If the email exists, a password reset link has been sent"
    }


# ========================================
# OAUTH - GOOGLE
# ========================================

@router.get("/oauth/google")
async def oauth_google(request: Request, redirect_uri: Optional[str] = None):
    """
    Inicia el flujo de autenticación con Google OAuth.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )
    
    # Guardar redirect_uri en session/cookie si es necesario
    redirect_uri = redirect_uri or f"{request.base_url}"
    
    # URL de autorización de Google
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.API_BASE_URL}{settings.API_V1_STR}/auth/oauth/google/callback"
        "&response_type=code"
        "&scope=openid email profile"
        f"&state={redirect_uri}"
    )
    
    return RedirectResponse(url=google_auth_url)


@router.get("/oauth/google/callback")
async def oauth_google_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Callback de Google OAuth.
    Intercambia el código por un access token y crea/autentica al usuario.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )
    
    try:
        # Intercambiar código por token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/oauth/google/callback",
                    "grant_type": "authorization_code",
                }
            )
            token_data = token_response.json()
            
            # Obtener información del usuario
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_info = user_response.json()
        
        # Buscar o crear usuario
        user = db.query(User).filter(
            User.email == user_info["email"]
        ).first()
        
        if not user:
            # Crear nuevo usuario desde Google
            user = User(
                email=user_info["email"],
                username=user_info["email"].split("@")[0],
                hashed_password=get_password_hash(f"oauth_google_{user_info['id']}"),  # Password temporal
                full_name=user_info.get("name"),
                oauth_provider="google",
                oauth_id=user_info["id"],
                is_active=True,
                is_superuser=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user created via Google OAuth: {user.email}")
        
        # Crear tokens
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.id}
        )
        
        # Redirigir al frontend con tokens en query params
        redirect_url = state or "http://localhost:5173"
        return RedirectResponse(
            url=f"{redirect_url}?token={access_token}&refresh_token={refresh_token}"
        )
    
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google OAuth failed: {str(e)}"
        )


# ========================================
# OAUTH - FACEBOOK
# ========================================

@router.get("/oauth/facebook")
async def oauth_facebook(request: Request, redirect_uri: Optional[str] = None):
    """
    Inicia el flujo de autenticación con Facebook OAuth.
    """
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Facebook OAuth not configured"
        )
    
    redirect_uri = redirect_uri or f"{request.base_url}"
    
    # URL de autorización de Facebook
    facebook_auth_url = (
        "https://www.facebook.com/v18.0/dialog/oauth"
        f"?client_id={settings.FACEBOOK_APP_ID}"
        f"&redirect_uri={settings.API_BASE_URL}{settings.API_V1_STR}/auth/oauth/facebook/callback"
        "&response_type=code"
        "&scope=email,public_profile"
        f"&state={redirect_uri}"
    )
    
    return RedirectResponse(url=facebook_auth_url)


@router.get("/oauth/facebook/callback")
async def oauth_facebook_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Callback de Facebook OAuth.
    Intercambia el código por un access token y crea/autentica al usuario.
    """
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Facebook OAuth not configured"
        )
    
    try:
        # Intercambiar código por token
        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": settings.FACEBOOK_APP_ID,
                    "client_secret": settings.FACEBOOK_APP_SECRET,
                    "redirect_uri": f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/oauth/facebook/callback",
                    "code": code,
                }
            )
            token_data = token_response.json()
            
            # Obtener información del usuario
            user_response = await client.get(
                "https://graph.facebook.com/me",
                params={
                    "fields": "id,name,email",
                    "access_token": token_data["access_token"]
                }
            )
            user_info = user_response.json()
        
        if not user_info.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Facebook. Please grant email permission."
            )
        
        # Buscar o crear usuario
        user = db.query(User).filter(
            User.email == user_info["email"]
        ).first()
        
        if not user:
            # Crear nuevo usuario desde Facebook
            user = User(
                email=user_info["email"],
                username=user_info["email"].split("@")[0],
                hashed_password=get_password_hash(f"oauth_facebook_{user_info['id']}"),
                full_name=user_info.get("name"),
                oauth_provider="facebook",
                oauth_id=user_info["id"],
                is_active=True,
                is_superuser=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user created via Facebook OAuth: {user.email}")
        
        # Crear tokens
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user.id}
        )
        
        # Redirigir al frontend con tokens
        redirect_url = state or "http://localhost:5173"
        return RedirectResponse(
            url=f"{redirect_url}?token={access_token}&refresh_token={refresh_token}"
        )
    
    except Exception as e:
        logger.error(f"Facebook OAuth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Facebook OAuth failed: {str(e)}"
        )
