import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from src.routes.auth_supabase import auth_bp
from src.routes.reports_supabase import reports_bp
from src.routes.analysis_supabase import analysis_bp
from src.routes.optimization_supabase import optimization_bp
from src.routes.export_supabase import export_bp

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enable CORS for frontend integration
CORS(app, origins=os.getenv('CORS_ORIGINS', '*').split(','))

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
app.register_blueprint(optimization_bp, url_prefix='/api/optimization')
app.register_blueprint(export_bp, url_prefix='/api/export')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and handle SPA routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return jsonify({
            'service': 'KDP Advertising Tool API',
            'version': '2.0.0',
            'database': 'Supabase',
            'status': 'running',
            'endpoints': {
                'auth': '/api/auth',
                'reports': '/api/reports',
                'analysis': '/api/analysis',
                'optimization': '/api/optimization',
                'export': '/api/export'
            }
        })

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({
                'service': 'KDP Advertising Tool API',
                'version': '2.0.0',
                'database': 'Supabase',
                'status': 'running',
                'message': 'Frontend not deployed - API only',
                'endpoints': {
                    'auth': {
                        'register': 'POST /api/auth/register',
                        'login': 'POST /api/auth/login',
                        'logout': 'POST /api/auth/logout',
                        'profile': 'GET/PUT /api/auth/profile',
                        'verify': 'GET /api/auth/verify'
                    },
                    'reports': {
                        'upload': 'POST /api/reports/upload',
                        'list': 'GET /api/reports',
                        'details': 'GET /api/reports/<id>'
                    },
                    'analysis': {
                        'analyze': 'POST /api/analysis/<report_id>',
                        'results': 'GET /api/analysis/<report_id>'
                    },
                    'optimization': {
                        'optimize': 'POST /api/optimization/<report_id>',
                        'recommendations': 'GET /api/optimization/<report_id>'
                    },
                    'export': {
                        'campaign_data': 'GET /api/export/<report_id>/campaigns',
                        'analysis': 'GET /api/export/<report_id>/analysis',
                        'recommendations': 'GET /api/export/<report_id>/recommendations'
                    }
                }
            })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        from src.config.supabase import SupabaseConfig
        client = SupabaseConfig.get_client()
        
        # Simple query to test connection
        result = client.table('users').select('id', count='exact').limit(1).execute()
        
        return jsonify({
            'status': 'healthy',
            'service': 'KDP Advertising Tool API',
            'version': '2.0.0',
            'database': 'Supabase',
            'database_status': 'connected',
            'user_count': result.count if result.count else 0
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'KDP Advertising Tool API',
            'version': '2.0.0',
            'database': 'Supabase',
            'database_status': 'error',
            'error': str(e)
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"Starting KDP Advertising Tool on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment PORT: {os.environ.get('PORT', 'Not set')}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

