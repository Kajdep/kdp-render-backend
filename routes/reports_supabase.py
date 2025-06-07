"""
Reports routes using Supabase
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import csv
from src.services.supabase_data import SupabaseDataService
from src.services.report_processor import ReportProcessor
from src.routes.auth_supabase import require_auth

reports_bp = Blueprint('reports', __name__)
data_service = SupabaseDataService()
report_processor = ReportProcessor()

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@reports_bp.route('/upload', methods=['POST'])
@require_auth
def upload_report():
    """Upload and process advertising report"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel files.'}), 400
        
        user_id = request.current_user['id']
        filename = secure_filename(file.filename)
        file_type = filename.rsplit('.', 1)[1].lower()
        
        # Create report record
        success, message, report_id = data_service.create_report(user_id, filename, file_type)
        if not success:
            return jsonify({'error': message}), 500
        
        # Save uploaded file temporarily
        upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, f"{report_id}_{filename}")
        file.save(file_path)
        
        # Process the file
        try:
            # Update status to processing
            data_service.update_report_processing(report_id, 'processing')
            
            # Process the report
            processed_data, campaigns = report_processor.process_file(file_path, file_type)
            
            # Save campaign data
            if campaigns:
                data_service.save_campaign_data(report_id, campaigns)
            
            # Update report with processed data
            data_service.update_report_processing(report_id, 'completed', processed_data=processed_data)
            
            # Clean up temporary file
            os.remove(file_path)
            
            return jsonify({
                'message': 'Report uploaded and processed successfully',
                'report_id': report_id,
                'summary': processed_data
            }), 200
            
        except Exception as e:
            # Update status to failed
            data_service.update_report_processing(report_id, 'failed', error_message=str(e))
            
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@reports_bp.route('', methods=['GET'])
@require_auth
def get_reports():
    """Get user's reports"""
    try:
        user_id = request.current_user['id']
        limit = request.args.get('limit', 50, type=int)
        
        reports = data_service.get_user_reports(user_id, limit)
        
        return jsonify({
            'reports': reports,
            'count': len(reports)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get reports: {str(e)}'}), 500

@reports_bp.route('/<int:report_id>', methods=['GET'])
@require_auth
def get_report_details(report_id):
    """Get detailed report information"""
    try:
        user_id = request.current_user['id']
        
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get campaign data
        campaigns = data_service.get_campaign_data(report_id)
        
        # Get analysis sessions
        analysis_sessions = data_service.get_analysis_sessions(report_id)
        
        return jsonify({
            'report': report,
            'campaigns': campaigns,
            'analysis_sessions': analysis_sessions
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get report details: {str(e)}'}), 500

@reports_bp.route('/stats', methods=['GET'])
@require_auth
def get_user_stats():
    """Get user statistics"""
    try:
        user_id = request.current_user['id']
        stats = data_service.get_user_stats(user_id)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

