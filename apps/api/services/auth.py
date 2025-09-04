"""
Authentication service using Supabase Auth
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseAuthService:
    """Handles authentication using Supabase Auth"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
        
        if self.supabase_url and self.supabase_key:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            # Create a service client for admin operations
            self.service_client: Client = create_client(self.supabase_url, self.service_role_key) if self.service_role_key else None
        else:
            self.client = None
            self.service_client = None
            logger.warning("Supabase credentials not configured")
    
    def sign_up(self, email: str, password: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sign up a new user with email and password"""
        if not self.client:
            return {
                'success': False,
                'error': 'Supabase not configured'
            }
            
        try:
            response = self.client.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': metadata or {}
                }
            })
            
            if response.user:
                logger.info(f"User signed up: {email}")
                return {
                    'success': True,
                    'user': response.user,
                    'session': response.session
                }
            else:
                return {
                    'success': False,
                    'error': 'Sign up failed'
                }
                
        except Exception as e:
            logger.error(f"Sign up error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user with email and password"""
        if not self.client:
            return {
                'success': False,
                'error': 'Supabase not configured'
            }
            
        try:
            response = self.client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if response.session:
                logger.info(f"User signed in: {email}")
                return {
                    'success': True,
                    'user': response.user,
                    'session': response.session,
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid credentials'
                }
                
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sign_out(self, access_token: str) -> Dict[str, Any]:
        """Sign out a user"""
        if not self.client:
            return {
                'success': False,
                'error': 'Supabase not configured'
            }
            
        try:
            # Set the session before signing out
            self.client.auth.set_session(access_token, "")
            self.client.auth.sign_out()
            
            logger.info("User signed out")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Sign out error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        if not self.client:
            return {
                'success': False,
                'error': 'Supabase not configured'
            }
            
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    'success': True,
                    'session': response.session,
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token
                }
            else:
                return {
                    'success': False,
                    'error': 'Token refresh failed'
                }
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user from access token"""
        if not self.client:
            return None
            
        try:
            # Set the session to get user
            self.client.auth.set_session(access_token, "")
            user = self.client.auth.get_user()
            
            if user:
                return {
                    'id': user.id,
                    'email': user.email,
                    'metadata': user.user_metadata,
                    'created_at': user.created_at
                }
            return None
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def reset_password_request(self, email: str) -> Dict[str, Any]:
        """Send password reset email"""
        if not self.client:
            return {
                'success': False,
                'error': 'Supabase not configured'
            }
            
        try:
            self.client.auth.reset_password_for_email(email)
            
            logger.info(f"Password reset email sent to: {email}")
            return {
                'success': True,
                'message': 'Password reset email sent'
            }
            
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_password(self, access_token: str, new_password: str) -> Dict[str, Any]:
        """Update user password"""
        if not self.client:
            return {
                'success': False,
                'error': 'Supabase not configured'
            }
            
        try:
            # Set the session before updating
            self.client.auth.set_session(access_token, "")
            response = self.client.auth.update_user({
                'password': new_password
            })
            
            if response.user:
                logger.info("Password updated successfully")
                return {
                    'success': True,
                    'user': response.user
                }
            else:
                return {
                    'success': False,
                    'error': 'Password update failed'
                }
                
        except Exception as e:
            logger.error(f"Password update error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        if not self.jwt_secret:
            logger.warning("JWT secret not configured")
            return None
            
        try:
            # Decode the Supabase JWT
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'], 
                               options={"verify_aud": False})
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None


class AuthMiddleware:
    """Authentication middleware for FastAPI"""
    
    def __init__(self):
        self.auth_service = SupabaseAuthService()
        self.whitelist_paths = [
            '/health',
            '/docs',
            '/openapi.json',
            '/auth/signup',
            '/auth/signin',
            '/auth/reset-password'
        ]
    
    async def __call__(self, request, call_next):
        """Check authentication for protected routes"""
        # Skip auth for whitelisted paths
        if any(request.url.path.startswith(path) for path in self.whitelist_paths):
            response = await call_next(request)
            return response
        
        # Check for authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={'error': 'Missing or invalid authorization header'}
            )
        
        # Verify token
        token = auth_header.replace('Bearer ', '')
        user_data = self.auth_service.get_user(token)
        
        if not user_data:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={'error': 'Invalid or expired token'}
            )
        
        # Add user info to request state
        request.state.user = user_data
        request.state.user_id = user_data.get('id')
        request.state.user_email = user_data.get('email')
        
        response = await call_next(request)
        return response


def get_auth_service():
    """Get authentication service"""
    return SupabaseAuthService()