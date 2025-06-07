from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from src.models.user import db, Report, User, CampaignData
from src.services.report_processor import ReportProcessor
from src.services.llm_service import LLMService

reports_bp = Blueprint('reports', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_or_create_demo_user():
    """Get or create a demo user for the application"""
    demo_user = User.query.filter_by(email='demo@kdptool.com').first()
    if not demo_user:
        demo_user = User(
            name='Demo User',
            email='demo@kdptool.com',
            subscription_tier='free'
        )
        db.session.add(demo_user)
        db.session.commit()
    return demo_user

@reports_bp.route('/upload', methods=['POST'])
def upload_report():
    """Upload and process Amazon advertising reports"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel files.'}), 400
        
        # Get or create demo user (in production, this would come from authentication)
        user = get_or_create_demo_user()
        user_id = user.id
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Create report record
        report = Report(
            user_id=user_id,
            filename=unique_filename,
            file_type='unknown',  # Will be determined during processing
            processing_status='pending'
        )
        db.session.add(report)
        db.session.commit()
        
        # Process the report
        processor = ReportProcessor()
        try:
            result = processor.process_report(file_path, report.id)
            
            # Update report with processing results
            report.processing_status = 'completed'
            report.processed = True
            report.file_type = result.get('report_type', 'unknown')
            report.date_range_start = result.get('date_range_start')
            report.date_range_end = result.get('date_range_end')
            report.total_spend = result.get('total_spend', 0)
            report.total_sales = result.get('total_sales', 0)
            report.total_impressions = result.get('total_impressions', 0)
            report.total_clicks = result.get('total_clicks', 0)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'report_id': report.id,
                'message': 'Report uploaded and processed successfully',
                'summary': {
                    'report_type': result.get('report_type'),
                    'date_range': f"{result.get('date_range_start')} to {result.get('date_range_end')}",
                    'total_spend': float(result.get('total_spend', 0)),
                    'total_sales': float(result.get('total_sales', 0)),
                    'campaigns_processed': result.get('campaigns_processed', 0),
                    'keywords_processed': result.get('keywords_processed', 0)
                }
            })
            
        except Exception as e:
            # Update report with error status
            report.processing_status = 'error'
            report.error_message = str(e)
            db.session.commit()
            
            return jsonify({
                'error': f'Error processing report: {str(e)}',
                'report_id': report.id
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@reports_bp.route('/list', methods=['GET'])
def list_reports():
    """Get list of uploaded reports for a user"""
    try:
        # Get or create demo user
        user = get_or_create_demo_user()
        user_id = user.id
        
        reports = Report.query.filter_by(user_id=user_id).order_by(Report.upload_date.desc()).all()
        
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'filename': report.filename,
                'file_type': report.file_type,
                'upload_date': report.upload_date.isoformat(),
                'processed': report.processed,
                'processing_status': report.processing_status,
                'error_message': report.error_message,
                'date_range_start': report.date_range_start.isoformat() if report.date_range_start else None,
                'date_range_end': report.date_range_end.isoformat() if report.date_range_end else None,
                'total_spend': float(report.total_spend) if report.total_spend else 0,
                'total_sales': float(report.total_sales) if report.total_sales else 0,
                'total_impressions': report.total_impressions or 0,
                'total_clicks': report.total_clicks or 0
            })
        
        return jsonify({
            'success': True,
            'reports': reports_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve reports: {str(e)}'}), 500

@reports_bp.route('/<int:report_id>', methods=['GET'])
def get_report_details(report_id):
    """Get detailed information about a specific report"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # Get campaign data for this report
        campaign_data = CampaignData.query.filter_by(report_id=report_id).all()
        
        campaigns = []
        for data in campaign_data:
            campaigns.append({
                'amazon_campaign_id': data.amazon_campaign_id,
                'campaign_name': data.campaign_name,
                'date': data.date.isoformat(),
                'impressions': data.impressions,
                'clicks': data.clicks,
                'ctr': float(data.ctr) if data.ctr else 0,
                'cpc': float(data.cpc) if data.cpc else 0,
                'spend': float(data.spend) if data.spend else 0,
                'sales': float(data.sales) if data.sales else 0,
                'acos': float(data.acos) if data.acos else 0,
                'roas': float(data.roas) if data.roas else 0,
                'orders': data.orders,
                'units': data.units,
                'conversion_rate': float(data.conversion_rate) if data.conversion_rate else 0
            })
        
        return jsonify({
            'success': True,
            'report': {
                'id': report.id,
                'filename': report.filename,
                'file_type': report.file_type,
                'upload_date': report.upload_date.isoformat(),
                'processed': report.processed,
                'processing_status': report.processing_status,
                'date_range_start': report.date_range_start.isoformat() if report.date_range_start else None,
                'date_range_end': report.date_range_end.isoformat() if report.date_range_end else None,
                'total_spend': float(report.total_spend) if report.total_spend else 0,
                'total_sales': float(report.total_sales) if report.total_sales else 0,
                'total_impressions': report.total_impressions or 0,
                'total_clicks': report.total_clicks or 0
            },
            'campaigns': campaigns
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve report details: {str(e)}'}), 500

@reports_bp.route('/<int:report_id>/summary', methods=['GET'])
def get_report_summary(report_id):
    """Get AI-generated summary of report performance"""
    try:
        report = Report.query.get_or_404(report_id)
        
        if not report.processed:
            return jsonify({'error': 'Report is not yet processed'}), 400
        
        # Get campaign data for analysis
        campaign_data = CampaignData.query.filter_by(report_id=report_id).all()
        
        if not campaign_data:
            return jsonify({'error': 'No campaign data found for this report'}), 404
        
        # Generate AI summary using LLM service
        llm_service = LLMService()
        
        # Prepare data for LLM analysis
        analysis_data = {
            'total_spend': float(report.total_spend) if report.total_spend else 0,
            'total_sales': float(report.total_sales) if report.total_sales else 0,
            'total_impressions': report.total_impressions or 0,
            'total_clicks': report.total_clicks or 0,
            'acos': (float(report.total_spend) / float(report.total_sales) * 100) if report.total_sales and report.total_spend else 0,
            'campaigns': len(campaign_data),
            'date_range': f"{report.date_range_start} to {report.date_range_end}" if report.date_range_start and report.date_range_end else "Unknown"
        }
        
        summary = llm_service.analyze_campaign_performance(analysis_data)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate report summary: {str(e)}'}), 500

@reports_bp.route('/<int:report_id>/delete', methods=['DELETE'])
def delete_report(report_id):
    """Delete a report and all associated data"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # Delete associated file
        file_path = os.path.join(UPLOAD_FOLDER, report.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete report (cascade will handle related data)
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete report: {str(e)}'}), 500

@reports_bp.route('/', methods=['GET'])
def reports_index():
    """Get basic reports information"""
    return jsonify({
        'success': True,
        'message': 'Reports API is working',
        'endpoints': [
            'POST /upload - Upload a new report',
            'GET /list - List all reports',
            'GET /<id> - Get report details',
            'GET /<id>/summary - Get AI summary',
            'DELETE /<id>/delete - Delete report'
        ]
    })

