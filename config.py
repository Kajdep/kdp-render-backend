"""
Fresh Supabase configuration for KDP Advertising Tool
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Create Supabase clients (basic initialization)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Service role client for admin operations
service_supabase: Client = None
if SUPABASE_SERVICE_KEY:
    service_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

class SupabaseConfig:
    """Fresh Supabase configuration class"""
    
    @staticmethod
    def get_client() -> Client:
        """Get the main Supabase client"""
        return supabase
    
    @staticmethod
    def get_service_client() -> Client:
        """Get the service role client for admin operations"""
        if not service_supabase:
            raise ValueError("SUPABASE_SERVICE_KEY not configured")
        return service_supabase
    
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
        """Test the Supabase connection"""
        try:
            # Try a simple query to test connection
            result = supabase.table('users').select('count', count='exact').execute()
            return {
                'status': 'success',
                'message': 'Supabase connection successful',
                'url': SUPABASE_URL,
                'user_count': result.count if hasattr(result, 'count') else 0
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Supabase connection failed: {str(e)}',
                'url': SUPABASE_URL
            }

