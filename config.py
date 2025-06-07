"""
Lazy Supabase configuration - No initialization at startup
This avoids the proxy error by only creating clients when needed
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration - check common environment variable names
SUPABASE_URL = (
    os.getenv('SUPABASE_URL') or 
    os.getenv('VITE_SUPABASE_URL') or 
    os.getenv('NEXT_PUBLIC_SUPABASE_URL')
)

SUPABASE_KEY = (
    os.getenv('SUPABASE_KEY') or 
    os.getenv('SUPABASE_ANON_KEY') or 
    os.getenv('VITE_SUPABASE_ANON_KEY') or 
    os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
)

SUPABASE_SERVICE_KEY = (
    os.getenv('SUPABASE_SERVICE_KEY') or 
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Global client variables - initialized lazily
_supabase_client: Optional[object] = None
_service_client: Optional[object] = None

class SupabaseConfig:
    """Lazy Supabase configuration - clients created only when needed"""
    
    @staticmethod
    def get_client():
        """Get the main Supabase client (lazy initialization)"""
        global _supabase_client
        
        if _supabase_client is None:
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
            try:
                from supabase import create_client
                _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                raise RuntimeError(f"Failed to create Supabase client: {str(e)}")
        
        return _supabase_client
    
    @staticmethod
    def get_service_client():
        """Get the service role client (lazy initialization)"""
        global _service_client
        
        if _service_client is None:
            if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set for admin operations")
            
            try:
                from supabase import create_client
                _service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            except Exception as e:
                raise RuntimeError(f"Failed to create Supabase service client: {str(e)}")
        
        return _service_client
    
    @staticmethod
    def get_url() -> str:
        """Get Supabase URL"""
        return SUPABASE_URL
    
    @staticmethod
    def get_anon_key() -> str:
        """Get Supabase anonymous key"""
        return SUPABASE_KEY
    
    @staticmethod
    def test_connection() -> dict:
        """Test the Supabase connection (lazy initialization)"""
        try:
            client = SupabaseConfig.get_client()
            # Try a simple query to test connection
            result = client.table('users').select('count', count='exact').execute()
            return {
                'status': 'success',
                'message': 'Supabase connection successful (lazy loaded)',
                'url': SUPABASE_URL,
                'user_count': result.count if hasattr(result, 'count') else 0
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Supabase connection failed: {str(e)}',
                'url': SUPABASE_URL,
                'error_type': type(e).__name__
            }
    
    @staticmethod
    def get_config_info() -> dict:
        """Get configuration information without initializing clients"""
        return {
            'supabase_url': SUPABASE_URL,
            'has_anon_key': bool(SUPABASE_KEY),
            'has_service_key': bool(SUPABASE_SERVICE_KEY),
            'client_initialized': _supabase_client is not None,
            'service_client_initialized': _service_client is not None
        }

