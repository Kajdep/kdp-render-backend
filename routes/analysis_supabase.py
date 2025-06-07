"""
Analysis routes using Supabase
"""
from flask import Blueprint, request, jsonify
from src.services.supabase_data import SupabaseDataService
from src.services.llm_service import LLMService
from src.routes.auth_supabase import require_auth

analysis_bp = Blueprint('analysis', __name__)
data_service = SupabaseDataService()
llm_service = LLMService()

@analysis_bp.route('/<int:report_id>', methods=['POST'])
@require_auth
def analyze_report(report_id):
    """Analyze a report with AI"""
    try:
        user_id = request.current_user['id']
        
        # Get report details
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        if not report['processed']:
            return jsonify({'error': 'Report not yet processed'}), 400
        
        # Get campaign data
        campaigns = data_service.get_campaign_data(report_id)
        if not campaigns:
            return jsonify({'error': 'No campaign data found'}), 404
        
        # Get user's preferred model and API key
        user_api_key = request.current_user.get('openrouter_api_key')
        preferred_model = request.current_user.get('preferred_model', 'meta-llama/llama-3.1-8b-instruct:free')
        
        # Perform analysis
        analysis_results = llm_service.analyze_campaign_performance(
            campaigns, 
            api_key=user_api_key,
            model=preferred_model
        )
        
        # Generate performance summary
        performance_summary = _generate_performance_summary(campaigns, report)
        
        # Generate recommendations
        recommendations = llm_service.generate_optimization_recommendations(
            campaigns,
            analysis_results,
            api_key=user_api_key,
            model=preferred_model
        )
        
        # Save analysis session
        success, session_id = data_service.save_analysis_session(
            report_id=report_id,
            user_id=user_id,
            analysis_type='campaign_performance',
            ai_model=preferred_model,
            analysis_results=analysis_results,
            recommendations=recommendations,
            performance_summary=performance_summary
        )
        
        if not success:
            return jsonify({'error': 'Failed to save analysis session'}), 500
        
        return jsonify({
            'session_id': session_id,
            'analysis': analysis_results,
            'recommendations': recommendations,
            'performance_summary': performance_summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@analysis_bp.route('/<int:report_id>', methods=['GET'])
@require_auth
def get_analysis_results(report_id):
    """Get analysis results for a report"""
    try:
        user_id = request.current_user['id']
        
        # Verify user owns the report
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get analysis sessions
        sessions = data_service.get_analysis_sessions(report_id)
        
        if not sessions:
            return jsonify({'error': 'No analysis found for this report'}), 404
        
        # Return the most recent analysis
        latest_session = sessions[0]
        
        return jsonify({
            'session_id': latest_session['id'],
            'analysis': latest_session['analysis_results'],
            'recommendations': latest_session['recommendations'],
            'performance_summary': latest_session['performance_summary'],
            'session_date': latest_session['session_date'],
            'ai_model_used': latest_session['ai_model_used']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get analysis: {str(e)}'}), 500

@analysis_bp.route('/<int:report_id>/sessions', methods=['GET'])
@require_auth
def get_analysis_sessions(report_id):
    """Get all analysis sessions for a report"""
    try:
        user_id = request.current_user['id']
        
        # Verify user owns the report
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get all analysis sessions
        sessions = data_service.get_analysis_sessions(report_id)
        
        return jsonify({
            'sessions': sessions,
            'count': len(sessions)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get analysis sessions: {str(e)}'}), 500

def _generate_performance_summary(campaigns, report):
    """Generate performance summary from campaign data"""
    try:
        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.get('state', '').lower() == 'enabled'])
        
        total_spend = sum(float(c.get('cost', 0) or 0) for c in campaigns)
        total_sales = sum(float(c.get('sales', 0) or 0) for c in campaigns)
        total_impressions = sum(int(c.get('impressions', 0) or 0) for c in campaigns)
        total_clicks = sum(int(c.get('clicks', 0) or 0) for c in campaigns)
        
        avg_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
        avg_roas = (total_sales / total_spend) if total_spend > 0 else 0
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        
        # Find top performers
        top_campaigns = sorted(
            [c for c in campaigns if c.get('sales', 0) and float(c.get('sales', 0)) > 0],
            key=lambda x: float(x.get('sales', 0)),
            reverse=True
        )[:5]
        
        # Find worst performers (high ACOS)
        worst_campaigns = sorted(
            [c for c in campaigns if c.get('acos') and float(c.get('acos', 0)) > 0],
            key=lambda x: float(x.get('acos', 0)),
            reverse=True
        )[:5]
        
        return {
            'overview': {
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_spend': round(total_spend, 2),
                'total_sales': round(total_sales, 2),
                'total_impressions': total_impressions,
                'total_clicks': total_clicks,
                'avg_acos': round(avg_acos, 2),
                'avg_roas': round(avg_roas, 2),
                'avg_ctr': round(avg_ctr, 4),
                'avg_cpc': round(avg_cpc, 2)
            },
            'top_campaigns': [
                {
                    'name': c.get('campaign_name', 'Unknown'),
                    'sales': float(c.get('sales', 0)),
                    'acos': float(c.get('acos', 0)) if c.get('acos') else 0,
                    'roas': float(c.get('roas', 0)) if c.get('roas') else 0
                }
                for c in top_campaigns
            ],
            'worst_campaigns': [
                {
                    'name': c.get('campaign_name', 'Unknown'),
                    'acos': float(c.get('acos', 0)),
                    'spend': float(c.get('cost', 0)),
                    'sales': float(c.get('sales', 0)) if c.get('sales') else 0
                }
                for c in worst_campaigns
            ]
        }
        
    except Exception as e:
        return {
            'overview': {
                'total_campaigns': len(campaigns),
                'error': f'Failed to calculate summary: {str(e)}'
            },
            'top_campaigns': [],
            'worst_campaigns': []
        }

