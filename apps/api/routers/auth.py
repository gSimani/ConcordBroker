"""
Authentication routes using Supabase Auth
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from ..services.auth import get_auth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

class SignUpRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="User's full name")
    company: Optional[str] = Field(None, description="Company name")
    
class SignInRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
class AuthResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send reset link")

class UpdatePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

class UserInfo(BaseModel):
    id: str
    email: str
    created_at: str
    metadata: Optional[dict] = None


@router.post("/signup", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """Create a new user account"""
    auth_service = get_auth_service()
    
    try:
        # Build user metadata
        metadata = {}
        if request.full_name:
            metadata['full_name'] = request.full_name
        if request.company:
            metadata['company'] = request.company
            
        result = auth_service.sign_up(
            email=request.email,
            password=request.password,
            metadata=metadata
        )
        
        if result['success']:
            session = result.get('session')
            user = result.get('user')
            
            return AuthResponse(
                success=True,
                access_token=session.access_token if session else None,
                refresh_token=session.refresh_token if session else None,
                user_id=user.id if user else None,
                email=user.email if user else None,
                message="Account created successfully. Please check your email for verification."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Sign up failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign up error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/signin", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """Sign in with email and password"""
    auth_service = get_auth_service()
    
    try:
        result = auth_service.sign_in(
            email=request.email,
            password=request.password
        )
        
        if result['success']:
            return AuthResponse(
                success=True,
                access_token=result['access_token'],
                refresh_token=result['refresh_token'],
                user_id=result['user'].id,
                email=result['user'].email
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=result.get('error', 'Invalid credentials')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign in error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/signout")
async def sign_out(authorization: str = Header(None)):
    """Sign out the current user"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    auth_service = get_auth_service()
    token = authorization.replace('Bearer ', '')
    
    try:
        result = auth_service.sign_out(token)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Signed out successfully'
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Sign out failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign out error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    auth_service = get_auth_service()
    
    try:
        result = auth_service.refresh_token(request.refresh_token)
        
        if result['success']:
            return AuthResponse(
                success=True,
                access_token=result['access_token'],
                refresh_token=result['refresh_token']
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=result.get('error', 'Token refresh failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest):
    """Request password reset email"""
    auth_service = get_auth_service()
    
    try:
        result = auth_service.reset_password_request(request.email)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Password reset email sent. Please check your inbox.'
            }
        else:
            # Don't reveal if email exists or not
            return {
                'success': True,
                'message': 'If the email exists, a password reset link has been sent.'
            }
            
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        # Don't reveal errors for security
        return {
            'success': True,
            'message': 'If the email exists, a password reset link has been sent.'
        }


@router.post("/update-password")
async def update_password(
    request: UpdatePasswordRequest,
    authorization: str = Header(None)
):
    """Update user password (requires authentication)"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    auth_service = get_auth_service()
    token = authorization.replace('Bearer ', '')
    
    try:
        result = auth_service.update_password(token, request.new_password)
        
        if result['success']:
            return {
                'success': True,
                'message': 'Password updated successfully'
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Password update failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password update error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user(request: Request):
    """Get current authenticated user info"""
    # This will only be reached if auth middleware passes
    user = getattr(request.state, 'user', None)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    return UserInfo(
        id=user['id'],
        email=user['email'],
        created_at=user.get('created_at', ''),
        metadata=user.get('metadata')
    )