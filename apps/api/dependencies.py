"""
API Dependencies
Common dependencies for FastAPI endpoints
"""

from typing import Optional, Dict
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from .config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """Get current authenticated user from JWT token"""
    
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # In production, verify user exists in database
        user = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict]:
    """Get user if authenticated, None otherwise"""
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
    except:
        return None


def require_role(role: str):
    """Require specific user role"""
    
    async def role_checker(user: Dict = Depends(get_current_user)):
        if user.get("role") != role and user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' required"
            )
        return user
    
    return role_checker