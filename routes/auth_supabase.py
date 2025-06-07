"""
Authentication routes using Supabase
"""
from flask import Blueprint, request, jsonify
from src.services.supabase_auth import SupabaseAuthService
from functools import wraps

auth_bp = Blueprint('auth', __name__)
auth_service = SupabaseAuthService()

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        valid, user_data = auth_service.verify_session(token)
        
        if not valid:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not all([email, password, name]):
            return jsonify({'error': 'Email, password, and name are required'}), 400
        
        success, message, user_data = auth_service.register_user(email, password, name)
        
        if success:
            return jsonify({
                'message': message,
                'user': user_data
            }), 201
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not all([email, password]):
            return jsonify({'error': 'Email and password are required'}), 400
        
        success, message, user_data = auth_service.login_user(email, password)
        
        if success:
            return jsonify({
                'message': message,
                'user': user_data
            }), 200
        else:
            return jsonify({'error': message}), 401
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user"""
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        
        success = auth_service.logout_user(token)
        
        if success:
            return jsonify({'message': 'Logged out successfully'}), 200
        else:
            return jsonify({'error': 'Logout failed'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    try:
        return jsonify({
            'user': request.current_user
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = request.current_user['id']
        success, message = auth_service.update_user_profile(user_id, data)
        
        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': f'Profile update failed: {str(e)}'}), 500

@auth_bp.route('/verify', methods=['GET'])
@require_auth
def verify_session():
    """Verify current session"""
    try:
        return jsonify({
            'valid': True,
            'user': request.current_user
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Session verification failed: {str(e)}'}), 500

