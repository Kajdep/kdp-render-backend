from flask import Blueprint, request, jsonify
import json
from datetime import datetime
from src.models.user import db, Report, User, AnalysisSession
from src.services.llm_service import LLMService
from src.services.report_processor import ReportProcessor

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/<int:report_id>', methods=['GET'])
def get_analysis(report_id):
    """Get comprehensive analysis for a report"""
    try:
        # Get the report
        report = Report.query.get_or_404(report_id)
        
        # Initialize services
        processor = ReportProcessor()
        llm_service = LLMService()
        
        # Get advanced analytics
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        # Get user for LLM analysis
        user = User.query.get(report.user_id)
        
        # Generate AI insights
        ai_insights = llm_service.analyze_performance(
            analytics['performance_summary'],
            user.openrouter_api_key if user else None,
            user.preferred_model if user else None
        )
        
        # Prepare response
        analysis_data = {
            'report_id': report_id,
            'report_name': report.filename,
            'date_range': {
                'start': report.date_range_start.isoformat() if report.date_range_start else None,
                'end': report.date_range_end.isoformat() if report.date_range_end else None
            },
            'performance_summary': analytics['performance_summary'],
            'campaign_analysis': analytics['campaign_analysis'],
            'trend_analysis': analytics['trend_analysis'],
            'efficiency_metrics': analytics['efficiency_metrics'],
            'recommendations': analytics['recommendations'],
            'ai_insights': ai_insights,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Save analysis session
        analysis_session = AnalysisSession(
            report_id=report_id,
            analysis_data=json.dumps(analysis_data),
            insights_generated=True,
            created_at=datetime.utcnow()
        )
        db.session.add(analysis_session)
        db.session.commit()
        
        return jsonify(analysis_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate analysis: {str(e)}'}), 500

@analysis_bp.route('/<int:report_id>/campaigns', methods=['GET'])
def get_campaign_analysis(report_id):
    """Get detailed campaign analysis"""
    try:
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        return jsonify({
            'campaign_analysis': analytics['campaign_analysis'],
            'efficiency_metrics': analytics['efficiency_metrics']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get campaign analysis: {str(e)}'}), 500

@analysis_bp.route('/<int:report_id>/trends', methods=['GET'])
def get_trend_analysis(report_id):
    """Get trend analysis for a report"""
    try:
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        return jsonify({
            'trend_analysis': analytics['trend_analysis'],
            'performance_summary': analytics['performance_summary']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get trend analysis: {str(e)}'}), 500

@analysis_bp.route('/<int:report_id>/insights', methods=['POST'])
def generate_custom_insights(report_id):
    """Generate custom AI insights based on user query"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get report and analytics
        report = Report.query.get_or_404(report_id)
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        # Get user for LLM analysis
        user = User.query.get(report.user_id)
        llm_service = LLMService()
        
        # Generate custom insights
        insights = llm_service.generate_custom_insights(
            query,
            analytics,
            user.openrouter_api_key if user else None,
            user.preferred_model if user else None
        )
        
        return jsonify({
            'query': query,
            'insights': insights,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate custom insights: {str(e)}'}), 500

@analysis_bp.route('/<int:report_id>/export', methods=['GET'])
def export_analysis(report_id):
    """Export analysis data"""
    try:
        # Get the latest analysis session
        analysis_session = AnalysisSession.query.filter_by(
            report_id=report_id
        ).order_by(AnalysisSession.created_at.desc()).first()
        
        if not analysis_session:
            return jsonify({'error': 'No analysis found for this report'}), 404
        
        analysis_data = json.loads(analysis_session.analysis_data)
        
        # Add export metadata
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'report_analysis': analysis_data
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to export analysis: {str(e)}'}), 500

@analysis_bp.route('/compare', methods=['POST'])
def compare_reports():
    """Compare multiple reports"""
    try:
        data = request.get_json()
        report_ids = data.get('report_ids', [])
        
        if len(report_ids) < 2:
            return jsonify({'error': 'At least 2 reports required for comparison'}), 400
        
        processor = ReportProcessor()
        comparisons = []
        
        for report_id in report_ids:
            report = Report.query.get(report_id)
            if not report:
                continue
                
            analytics = processor.get_report_analytics(report_id)
            if 'error' not in analytics:
                comparisons.append({
                    'report_id': report_id,
                    'report_name': report.filename,
                    'performance_summary': analytics['performance_summary'],
                    'date_range': {
                        'start': report.date_range_start.isoformat() if report.date_range_start else None,
                        'end': report.date_range_end.isoformat() if report.date_range_end else None
                    }
                })
        
        if len(comparisons) < 2:
            return jsonify({'error': 'Not enough valid reports for comparison'}), 400
        
        # Generate comparison insights
        comparison_data = {
            'reports': comparisons,
            'comparison_insights': _generate_comparison_insights(comparisons),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(comparison_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to compare reports: {str(e)}'}), 500

def _generate_comparison_insights(comparisons):
    """Generate insights from report comparisons"""
    insights = []
    
    if len(comparisons) < 2:
        return insights
    
    # Compare ACOS
    acos_values = [c['performance_summary']['overall_acos'] for c in comparisons]
    best_acos_idx = acos_values.index(min(acos_values))
    worst_acos_idx = acos_values.index(max(acos_values))
    
    insights.append({
        'type': 'acos_comparison',
        'best_report': comparisons[best_acos_idx]['report_name'],
        'best_acos': acos_values[best_acos_idx],
        'worst_report': comparisons[worst_acos_idx]['report_name'],
        'worst_acos': acos_values[worst_acos_idx],
        'improvement_potential': acos_values[worst_acos_idx] - acos_values[best_acos_idx]
    })
    
    # Compare ROAS
    roas_values = [c['performance_summary']['overall_roas'] for c in comparisons]
    best_roas_idx = roas_values.index(max(roas_values))
    worst_roas_idx = roas_values.index(min(roas_values))
    
    insights.append({
        'type': 'roas_comparison',
        'best_report': comparisons[best_roas_idx]['report_name'],
        'best_roas': roas_values[best_roas_idx],
        'worst_report': comparisons[worst_roas_idx]['report_name'],
        'worst_roas': roas_values[worst_roas_idx],
        'improvement_potential': roas_values[best_roas_idx] - roas_values[worst_roas_idx]
    })
    
    # Compare spend efficiency
    spend_values = [c['performance_summary']['total_spend'] for c in comparisons]
    sales_values = [c['performance_summary']['total_sales'] for c in comparisons]
    
    efficiency_ratios = [sales/spend if spend > 0 else 0 for spend, sales in zip(spend_values, sales_values)]
    best_efficiency_idx = efficiency_ratios.index(max(efficiency_ratios))
    
    insights.append({
        'type': 'efficiency_comparison',
        'most_efficient_report': comparisons[best_efficiency_idx]['report_name'],
        'efficiency_ratio': efficiency_ratios[best_efficiency_idx],
        'total_spend': spend_values[best_efficiency_idx],
        'total_sales': sales_values[best_efficiency_idx]
    })
    
    return insights

