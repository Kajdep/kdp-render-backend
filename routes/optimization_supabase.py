"""
Optimization routes using Supabase
"""
from flask import Blueprint, request, jsonify
from src.services.supabase_data import SupabaseDataService
from src.services.llm_service import LLMService
from src.routes.auth_supabase import require_auth

optimization_bp = Blueprint('optimization', __name__)
data_service = SupabaseDataService()
llm_service = LLMService()

@optimization_bp.route('/<int:report_id>', methods=['POST'])
@require_auth
def optimize_campaigns(report_id):
    """Generate optimization recommendations for campaigns"""
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
        
        # Generate comprehensive optimization recommendations
        recommendations = _generate_comprehensive_recommendations(campaigns)
        
        # Get AI-powered insights
        ai_insights = llm_service.generate_optimization_recommendations(
            campaigns,
            recommendations,
            api_key=user_api_key,
            model=preferred_model
        )
        
        # Combine recommendations with AI insights
        final_recommendations = {
            **recommendations,
            'ai_insights': ai_insights,
            'model_used': preferred_model
        }
        
        # Save optimization session
        success, session_id = data_service.save_analysis_session(
            report_id=report_id,
            user_id=user_id,
            analysis_type='optimization',
            ai_model=preferred_model,
            analysis_results=final_recommendations,
            recommendations=final_recommendations,
            performance_summary=recommendations.get('summary', {})
        )
        
        if not success:
            return jsonify({'error': 'Failed to save optimization session'}), 500
        
        return jsonify({
            'session_id': session_id,
            'recommendations': final_recommendations
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Optimization failed: {str(e)}'}), 500

@optimization_bp.route('/<int:report_id>', methods=['GET'])
@require_auth
def get_optimization_results(report_id):
    """Get optimization results for a report"""
    try:
        user_id = request.current_user['id']
        
        # Verify user owns the report
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get optimization sessions
        sessions = data_service.get_analysis_sessions(report_id)
        optimization_sessions = [s for s in sessions if s.get('analysis_type') == 'optimization']
        
        if not optimization_sessions:
            return jsonify({'error': 'No optimization found for this report'}), 404
        
        # Return the most recent optimization
        latest_session = optimization_sessions[0]
        
        return jsonify({
            'session_id': latest_session['id'],
            'recommendations': latest_session['recommendations'],
            'session_date': latest_session['session_date'],
            'ai_model_used': latest_session['ai_model_used']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get optimization: {str(e)}'}), 500

def _generate_comprehensive_recommendations(campaigns):
    """Generate comprehensive optimization recommendations"""
    try:
        recommendations = {
            'summary': {
                'total_campaigns': len(campaigns),
                'recommendations_count': 0,
                'potential_savings': 0,
                'potential_revenue_increase': 0
            },
            'campaign_recommendations': [],
            'bid_adjustments': [],
            'budget_recommendations': [],
            'negative_keywords': [],
            'scaling_opportunities': []
        }
        
        for campaign in campaigns:
            campaign_name = campaign.get('campaign_name', 'Unknown')
            acos = float(campaign.get('acos', 0)) if campaign.get('acos') else 0
            spend = float(campaign.get('cost', 0)) if campaign.get('cost') else 0
            sales = float(campaign.get('sales', 0)) if campaign.get('sales') else 0
            impressions = int(campaign.get('impressions', 0)) if campaign.get('impressions') else 0
            clicks = int(campaign.get('clicks', 0)) if campaign.get('clicks') else 0
            
            # High ACOS campaigns (>50%)
            if acos > 50 and spend > 10:
                recommendations['campaign_recommendations'].append({
                    'campaign': campaign_name,
                    'issue': 'High ACOS',
                    'current_acos': acos,
                    'recommendation': 'Reduce bids by 20-30% or pause underperforming keywords',
                    'priority': 'High',
                    'potential_savings': spend * 0.3
                })
                recommendations['summary']['potential_savings'] += spend * 0.3
                recommendations['summary']['recommendations_count'] += 1
            
            # Low impression campaigns
            if impressions < 1000 and spend > 5:
                recommendations['campaign_recommendations'].append({
                    'campaign': campaign_name,
                    'issue': 'Low Impressions',
                    'current_impressions': impressions,
                    'recommendation': 'Increase bids by 15-25% or expand keyword targeting',
                    'priority': 'Medium',
                    'potential_revenue_increase': sales * 0.2
                })
                recommendations['summary']['potential_revenue_increase'] += sales * 0.2
                recommendations['summary']['recommendations_count'] += 1
            
            # High performing campaigns (low ACOS, good sales)
            if acos < 30 and sales > 100:
                recommendations['scaling_opportunities'].append({
                    'campaign': campaign_name,
                    'current_acos': acos,
                    'current_sales': sales,
                    'recommendation': 'Scale up: Increase budget by 50-100%',
                    'priority': 'High',
                    'potential_revenue_increase': sales * 0.5
                })
                recommendations['summary']['potential_revenue_increase'] += sales * 0.5
                recommendations['summary']['recommendations_count'] += 1
            
            # Bid adjustment recommendations
            cpc = (spend / clicks) if clicks > 0 else 0
            if cpc > 2.0:
                recommendations['bid_adjustments'].append({
                    'campaign': campaign_name,
                    'current_cpc': round(cpc, 2),
                    'recommendation': 'Reduce bids by 15-20%',
                    'reason': 'High cost per click'
                })
            elif cpc < 0.5 and impressions < 5000:
                recommendations['bid_adjustments'].append({
                    'campaign': campaign_name,
                    'current_cpc': round(cpc, 2),
                    'recommendation': 'Increase bids by 20-30%',
                    'reason': 'Low cost per click with low impressions'
                })
        
        # Budget recommendations
        total_spend = sum(float(c.get('cost', 0)) for c in campaigns)
        high_performers = [c for c in campaigns if float(c.get('acos', 100)) < 30 and float(c.get('sales', 0)) > 50]
        low_performers = [c for c in campaigns if float(c.get('acos', 100)) > 60]
        
        for campaign in high_performers:
            recommendations['budget_recommendations'].append({
                'campaign': campaign.get('campaign_name'),
                'action': 'Increase Budget',
                'current_budget': campaign.get('daily_budget', 'Unknown'),
                'recommended_increase': '50-100%',
                'reason': 'High performance, low ACOS'
            })
        
        for campaign in low_performers:
            recommendations['budget_recommendations'].append({
                'campaign': campaign.get('campaign_name'),
                'action': 'Reduce Budget',
                'current_budget': campaign.get('daily_budget', 'Unknown'),
                'recommended_decrease': '30-50%',
                'reason': 'Poor performance, high ACOS'
            })
        
        # Round summary values
        recommendations['summary']['potential_savings'] = round(recommendations['summary']['potential_savings'], 2)
        recommendations['summary']['potential_revenue_increase'] = round(recommendations['summary']['potential_revenue_increase'], 2)
        
        return recommendations
        
    except Exception as e:
        return {
            'summary': {
                'error': f'Failed to generate recommendations: {str(e)}',
                'total_campaigns': len(campaigns),
                'recommendations_count': 0
            },
            'campaign_recommendations': [],
            'bid_adjustments': [],
            'budget_recommendations': [],
            'negative_keywords': [],
            'scaling_opportunities': []
        }

