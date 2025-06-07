"""
KDP Advertising Tool - Fresh Supabase Integration
"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from config import SupabaseConfig

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins="*")

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kdp-advertising-tool-super-secret-key-2024')

@app.route('/health')
@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'KDP Advertising Tool API',
        'version': '3.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'supabase': 'integrated',
        'message': 'Fresh Supabase integration ready'
    })

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'KDP Advertising Tool API',
        'version': '3.0.0',
        'status': 'running',
        'message': 'Fresh Supabase backend ready',
        'endpoints': {
            'health': '/api/health',
            'supabase_test': '/api/supabase/test',
            'auth': '/api/auth (coming soon)',
            'reports': '/api/reports (coming soon)',
            'analysis': '/api/analysis (coming soon)',
            'optimization': '/api/optimization (coming soon)'
        }
    })

@app.route('/api/supabase/test')
def test_supabase():
    """Test Supabase connection"""
    try:
        result = SupabaseConfig.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Supabase test failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    """Test endpoint to verify API is working"""
    if request.method == 'POST':
        data = request.get_json() or {}
        return jsonify({
            'message': 'POST request received',
            'data_received': data,
            'timestamp': datetime.utcnow().isoformat(),
            'supabase_ready': True
        })
    else:
        return jsonify({
            'message': 'GET request successful',
            'timestamp': datetime.utcnow().isoformat(),
            'supabase_ready': True,
            'next_steps': 'Add authentication and report processing'
        })

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"Starting KDP Advertising Tool (Fresh Supabase) on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Supabase URL: {SupabaseConfig.get_url()}")
    print(f"Ready for fresh Supabase integration!")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

