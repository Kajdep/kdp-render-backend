"""
Supabase authentication service
"""
from typing import Dict, Optional, Tuple
from supabase import Client
from src.config.supabase import SupabaseConfig
import hashlib
import secrets
import re

class SupabaseAuthService:
    """Authentication service using Supabase"""
    
    def __init__(self):
        self.client = SupabaseConfig.get_client()
        self.service_client = SupabaseConfig.get_service_client()
    
    def register_user(self, email: str, password: str, name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user
        
        Args:
            email: User's email address
            password: User's password
            name: User's full name
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Validate email format
            if not self._is_valid_email(email):
                return False, "Invalid email format", None
            
            # Validate password strength
            if not self._is_strong_password(password):
                return False, "Password must be at least 8 characters with uppercase, lowercase, number, and special character", None
            
            # Check if user already exists
            existing_user = self.client.table('users').select('id').eq('email', email).execute()
            if existing_user.data:
                return False, "User with this email already exists", None
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user in database
            user_data = {
                'email': email,
                'name': name,
                'password_hash': password_hash,
                'subscription_tier': 'free',
                'email_notifications': True,
                'timezone': 'UTC',
                'preferred_model': 'meta-llama/llama-3.1-8b-instruct:free'
            }
            
            result = self.client.table('users').insert(user_data).execute()
            
            if result.data:
                user = result.data[0]
                # Generate session token
                session_token = self._generate_session_token()
                
                # Update user with session token
                self.client.table('users').update({
                    'session_token': session_token
                }).eq('id', user['id']).execute()
                
                return True, "User registered successfully", {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'session_token': session_token,
                    'subscription_tier': user['subscription_tier']
                }
            else:
                return False, "Failed to create user", None
                
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Login user with email and password
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Get user from database
            result = self.client.table('users').select('*').eq('email', email).execute()
            
            if not result.data:
                return False, "Invalid email or password", None
            
            user = result.data[0]
            
            # Verify password
            if not self._verify_password(password, user['password_hash']):
                return False, "Invalid email or password", None
            
            # Generate new session token
            session_token = self._generate_session_token()
            
            # Update user with new session token and last login
            self.client.table('users').update({
                'session_token': session_token,
                'last_login': 'now()'
            }).eq('id', user['id']).execute()
            
            return True, "Login successful", {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'session_token': session_token,
                'subscription_tier': user['subscription_tier'],
                'openrouter_api_key': user.get('openrouter_api_key'),
                'preferred_model': user.get('preferred_model', 'meta-llama/llama-3.1-8b-instruct:free')
            }
            
        except Exception as e:
            return False, f"Login failed: {str(e)}", None
    
    def verify_session(self, session_token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verify user session token
        
        Args:
            session_token: User's session token
            
        Returns:
            Tuple of (valid, user_data)
        """
        try:
            result = self.client.table('users').select('*').eq('session_token', session_token).execute()
            
            if result.data:
                user = result.data[0]
                return True, {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'subscription_tier': user['subscription_tier'],
                    'openrouter_api_key': user.get('openrouter_api_key'),
                    'preferred_model': user.get('preferred_model', 'meta-llama/llama-3.1-8b-instruct:free')
                }
            else:
                return False, None
                
        except Exception as e:
            return False, None
    
    def update_user_profile(self, user_id: int, updates: Dict) -> Tuple[bool, str]:
        """
        Update user profile
        
        Args:
            user_id: User's ID
            updates: Dictionary of fields to update
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Filter allowed fields
            allowed_fields = ['name', 'openrouter_api_key', 'preferred_model', 'email_notifications', 'timezone']
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not filtered_updates:
                return False, "No valid fields to update"
            
            result = self.client.table('users').update(filtered_updates).eq('id', user_id).execute()
            
            if result.data:
                return True, "Profile updated successfully"
            else:
                return False, "Failed to update profile"
                
        except Exception as e:
            return False, f"Update failed: {str(e)}"
    
    def logout_user(self, session_token: str) -> bool:
        """
        Logout user by invalidating session token
        
        Args:
            session_token: User's session token
            
        Returns:
            Success status
        """
        try:
            self.client.table('users').update({
                'session_token': None
            }).eq('session_token', session_token).execute()
            return True
        except:
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, hash_value = stored_hash.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == hash_value
        except:
            return False
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_strong_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special

