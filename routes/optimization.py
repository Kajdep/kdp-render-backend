from flask import Blueprint, request, jsonify
import json
from datetime import datetime
from src.models.user import db, Report, User, CampaignData
from src.services.llm_service import LLMService
from src.services.report_processor import ReportProcessor

optimization_bp = Blueprint('optimization', __name__)

@optimization_bp.route('/<int:report_id>', methods=['GET'])
def get_optimization_recommendations(report_id):
    """Get comprehensive optimization recommendations for a report"""
    try:
        # Get the report
        report = Report.query.get_or_404(report_id)
        
        # Initialize services
        processor = ReportProcessor()
        llm_service = LLMService()
        
        # Get analytics for optimization
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        # Get user for LLM optimization
        user = User.query.get(report.user_id)
        
        # Generate optimization recommendations
        optimization_data = {
            'report_id': report_id,
            'report_name': report.filename,
            'current_performance': analytics['performance_summary'],
            'campaign_recommendations': _generate_campaign_recommendations(analytics['campaign_analysis']),
            'bid_recommendations': _generate_bid_recommendations(analytics['campaign_analysis']),
            'budget_recommendations': _generate_budget_recommendations(analytics['campaign_analysis']),
            'keyword_recommendations': _generate_keyword_recommendations(report_id),
            'ai_optimization_insights': llm_service.generate_optimization_recommendations(
                analytics,
                user.openrouter_api_key if user else None,
                user.preferred_model if user else None
            ),
            'priority_actions': _generate_priority_actions(analytics),
            'expected_impact': _calculate_expected_impact(analytics),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(optimization_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate optimization recommendations: {str(e)}'}), 500

@optimization_bp.route('/<int:report_id>/campaigns', methods=['GET'])
def get_campaign_optimization(report_id):
    """Get campaign-specific optimization recommendations"""
    try:
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        campaign_optimizations = []
        
        for campaign_id, campaign_data in analytics['campaign_analysis']['campaign_details'].items():
            optimization = {
                'campaign_id': campaign_id,
                'campaign_name': campaign_data['name'],
                'current_metrics': {
                    'acos': campaign_data['acos'],
                    'roas': campaign_data['roas'],
                    'ctr': campaign_data['ctr'],
                    'cpc': campaign_data['cpc'],
                    'spend': campaign_data['total_spend'],
                    'sales': campaign_data['total_sales']
                },
                'recommendations': _get_campaign_specific_recommendations(campaign_data),
                'priority': _calculate_campaign_priority(campaign_data)
            }
            campaign_optimizations.append(optimization)
        
        # Sort by priority
        campaign_optimizations.sort(key=lambda x: x['priority'], reverse=True)
        
        return jsonify({
            'campaign_optimizations': campaign_optimizations,
            'summary': {
                'total_campaigns': len(campaign_optimizations),
                'high_priority': len([c for c in campaign_optimizations if c['priority'] > 7]),
                'medium_priority': len([c for c in campaign_optimizations if 4 <= c['priority'] <= 7]),
                'low_priority': len([c for c in campaign_optimizations if c['priority'] < 4])
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get campaign optimization: {str(e)}'}), 500

@optimization_bp.route('/<int:report_id>/bids', methods=['GET'])
def get_bid_recommendations(report_id):
    """Get bid optimization recommendations"""
    try:
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        bid_recommendations = []
        
        for campaign_id, campaign_data in analytics['campaign_analysis']['campaign_details'].items():
            bid_rec = _generate_bid_recommendation(campaign_data)
            if bid_rec:
                bid_recommendations.append(bid_rec)
        
        return jsonify({
            'bid_recommendations': bid_recommendations,
            'summary': {
                'increase_bids': len([b for b in bid_recommendations if b['action'] == 'increase']),
                'decrease_bids': len([b for b in bid_recommendations if b['action'] == 'decrease']),
                'maintain_bids': len([b for b in bid_recommendations if b['action'] == 'maintain'])
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get bid recommendations: {str(e)}'}), 500

@optimization_bp.route('/<int:report_id>/keywords', methods=['GET'])
def get_keyword_optimization(report_id):
    """Get keyword optimization recommendations"""
    try:
        # Get keyword data from the database
        keyword_data = db.session.query(
            CampaignData.amazon_campaign_id,
            CampaignData.campaign_name,
            CampaignData.spend,
            CampaignData.sales,
            CampaignData.impressions,
            CampaignData.clicks,
            CampaignData.acos
        ).filter_by(report_id=report_id).all()
        
        keyword_recommendations = []
        
        for data in keyword_data:
            # Generate keyword recommendations based on performance
            if data.acos > 50:  # High ACOS
                keyword_recommendations.append({
                    'campaign_id': data.amazon_campaign_id,
                    'campaign_name': data.campaign_name,
                    'recommendation_type': 'negative_keywords',
                    'action': 'Add negative keywords for high-cost, low-converting search terms',
                    'priority': 'high',
                    'expected_impact': 'Reduce ACOS by 15-25%',
                    'current_acos': data.acos
                })
            
            if data.impressions < 100:  # Low impressions
                keyword_recommendations.append({
                    'campaign_id': data.amazon_campaign_id,
                    'campaign_name': data.campaign_name,
                    'recommendation_type': 'keyword_expansion',
                    'action': 'Add more relevant keywords to increase visibility',
                    'priority': 'medium',
                    'expected_impact': 'Increase impressions by 50-100%',
                    'current_impressions': data.impressions
                })
            
            if data.sales > data.spend * 3:  # High ROAS
                keyword_recommendations.append({
                    'campaign_id': data.amazon_campaign_id,
                    'campaign_name': data.campaign_name,
                    'recommendation_type': 'keyword_scaling',
                    'action': 'Scale successful keywords with higher bids',
                    'priority': 'high',
                    'expected_impact': 'Increase sales by 20-40%',
                    'current_roas': data.sales / data.spend if data.spend > 0 else 0
                })
        
        return jsonify({
            'keyword_recommendations': keyword_recommendations,
            'summary': {
                'total_recommendations': len(keyword_recommendations),
                'negative_keywords': len([k for k in keyword_recommendations if k['recommendation_type'] == 'negative_keywords']),
                'keyword_expansion': len([k for k in keyword_recommendations if k['recommendation_type'] == 'keyword_expansion']),
                'keyword_scaling': len([k for k in keyword_recommendations if k['recommendation_type'] == 'keyword_scaling'])
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get keyword optimization: {str(e)}'}), 500

@optimization_bp.route('/<int:report_id>/simulate', methods=['POST'])
def simulate_optimization(report_id):
    """Simulate the impact of optimization changes"""
    try:
        data = request.get_json()
        changes = data.get('changes', {})
        
        # Get current analytics
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        current_performance = analytics['performance_summary']
        
        # Simulate changes
        simulated_performance = _simulate_changes(current_performance, changes)
        
        # Calculate impact
        impact = {
            'spend_change': simulated_performance['total_spend'] - current_performance['total_spend'],
            'sales_change': simulated_performance['total_sales'] - current_performance['total_sales'],
            'acos_change': simulated_performance['overall_acos'] - current_performance['overall_acos'],
            'roas_change': simulated_performance['overall_roas'] - current_performance['overall_roas'],
            'profit_change': (simulated_performance['total_sales'] - simulated_performance['total_spend']) - 
                           (current_performance['total_sales'] - current_performance['total_spend'])
        }
        
        return jsonify({
            'current_performance': current_performance,
            'simulated_performance': simulated_performance,
            'impact': impact,
            'changes_applied': changes,
            'simulation_date': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to simulate optimization: {str(e)}'}), 500

def _generate_campaign_recommendations(campaign_analysis):
    """Generate campaign-level recommendations"""
    recommendations = []
    
    # Analyze top performers
    for campaign_id, campaign_data in campaign_analysis['top_performers'][:3]:
        recommendations.append({
            'campaign_id': campaign_id,
            'campaign_name': campaign_data['name'],
            'type': 'scale_winner',
            'action': 'Increase budget by 25-50%',
            'reason': f'Excellent ROAS of {campaign_data["roas"]:.2f}x',
            'priority': 'high',
            'expected_impact': 'Increase profitable sales'
        })
    
    # Analyze worst performers
    for campaign_id, campaign_data in campaign_analysis['worst_performers'][:3]:
        if campaign_data['acos'] > 50:
            recommendations.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_data['name'],
                'type': 'optimize_or_pause',
                'action': 'Reduce bids by 20% or pause if no improvement',
                'reason': f'High ACOS of {campaign_data["acos"]:.1f}%',
                'priority': 'high',
                'expected_impact': 'Reduce wasted spend'
            })
    
    return recommendations

def _generate_bid_recommendations(campaign_analysis):
    """Generate bid adjustment recommendations"""
    recommendations = []
    
    for campaign_id, campaign_data in campaign_analysis['campaign_details'].items():
        bid_rec = _generate_bid_recommendation(campaign_data)
        if bid_rec:
            recommendations.append(bid_rec)
    
    return recommendations

def _generate_bid_recommendation(campaign_data):
    """Generate bid recommendation for a single campaign"""
    acos = campaign_data['acos']
    roas = campaign_data['roas']
    ctr = campaign_data['ctr']
    
    if roas > 3 and acos < 30:
        return {
            'campaign_id': campaign_data.get('campaign_id', 'unknown'),
            'campaign_name': campaign_data['name'],
            'action': 'increase',
            'percentage': 15,
            'reason': 'High ROAS and low ACOS - scale opportunity',
            'current_metrics': {'acos': acos, 'roas': roas, 'ctr': ctr}
        }
    elif acos > 50:
        return {
            'campaign_id': campaign_data.get('campaign_id', 'unknown'),
            'campaign_name': campaign_data['name'],
            'action': 'decrease',
            'percentage': 25,
            'reason': 'High ACOS - reduce spend',
            'current_metrics': {'acos': acos, 'roas': roas, 'ctr': ctr}
        }
    elif 30 <= acos <= 50 and roas >= 2:
        return {
            'campaign_id': campaign_data.get('campaign_id', 'unknown'),
            'campaign_name': campaign_data['name'],
            'action': 'maintain',
            'percentage': 0,
            'reason': 'Balanced performance - monitor closely',
            'current_metrics': {'acos': acos, 'roas': roas, 'ctr': ctr}
        }
    
    return None

def _generate_budget_recommendations(campaign_analysis):
    """Generate budget optimization recommendations"""
    recommendations = []
    
    # Recommend budget increases for top performers
    for campaign_id, campaign_data in campaign_analysis['top_performers'][:5]:
        if campaign_data['roas'] > 2.5:
            recommendations.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_data['name'],
                'action': 'increase_budget',
                'percentage': 30,
                'reason': f'High ROAS of {campaign_data["roas"]:.2f}x',
                'current_spend': campaign_data['total_spend']
            })
    
    # Recommend budget decreases for poor performers
    for campaign_id, campaign_data in campaign_analysis['worst_performers'][:3]:
        if campaign_data['acos'] > 60:
            recommendations.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_data['name'],
                'action': 'decrease_budget',
                'percentage': 50,
                'reason': f'Very high ACOS of {campaign_data["acos"]:.1f}%',
                'current_spend': campaign_data['total_spend']
            })
    
    return recommendations

def _generate_keyword_recommendations(report_id):
    """Generate keyword-specific recommendations"""
    # This would typically analyze keyword-level data
    # For now, return general keyword recommendations
    return [
        {
            'type': 'negative_keywords',
            'action': 'Add negative keywords for irrelevant search terms',
            'priority': 'high',
            'expected_impact': 'Reduce ACOS by 10-20%'
        },
        {
            'type': 'long_tail_keywords',
            'action': 'Add long-tail keywords for better targeting',
            'priority': 'medium',
            'expected_impact': 'Improve conversion rates'
        },
        {
            'type': 'competitor_keywords',
            'action': 'Research and add competitor keywords',
            'priority': 'medium',
            'expected_impact': 'Increase market share'
        }
    ]

def _generate_priority_actions(analytics):
    """Generate prioritized action items"""
    actions = []
    
    performance = analytics['performance_summary']
    
    # High ACOS alert
    if performance['overall_acos'] > 40:
        actions.append({
            'priority': 1,
            'action': 'Reduce high ACOS campaigns',
            'description': f'Overall ACOS is {performance["overall_acos"]:.1f}% - focus on reducing spend on underperforming campaigns',
            'impact': 'high'
        })
    
    # Low ROAS alert
    if performance['overall_roas'] < 2:
        actions.append({
            'priority': 2,
            'action': 'Improve ROAS',
            'description': f'Overall ROAS is {performance["overall_roas"]:.2f}x - optimize targeting and bids',
            'impact': 'high'
        })
    
    # Scale winners
    if len(analytics['campaign_analysis']['top_performers']) > 0:
        actions.append({
            'priority': 3,
            'action': 'Scale top performing campaigns',
            'description': 'Increase budgets for campaigns with ROAS > 3x',
            'impact': 'medium'
        })
    
    return actions

def _calculate_expected_impact(analytics):
    """Calculate expected impact of optimizations"""
    current_performance = analytics['performance_summary']
    
    # Conservative estimates
    potential_acos_reduction = min(current_performance['overall_acos'] * 0.2, 10)  # 20% reduction or 10 points max
    potential_roas_increase = current_performance['overall_roas'] * 0.15  # 15% increase
    
    return {
        'acos_improvement': potential_acos_reduction,
        'roas_improvement': potential_roas_increase,
        'estimated_monthly_savings': current_performance['total_spend'] * 0.1,  # 10% spend reduction
        'estimated_sales_increase': current_performance['total_sales'] * 0.15,  # 15% sales increase
        'confidence_level': 'medium'
    }

def _get_campaign_specific_recommendations(campaign_data):
    """Get specific recommendations for a campaign"""
    recommendations = []
    
    acos = campaign_data['acos']
    roas = campaign_data['roas']
    ctr = campaign_data['ctr']
    
    if acos > 50:
        recommendations.append({
            'type': 'reduce_bids',
            'description': 'Reduce bids by 20-30% to lower ACOS',
            'priority': 'high'
        })
    
    if ctr < 0.5:
        recommendations.append({
            'type': 'improve_targeting',
            'description': 'Review and improve keyword targeting for better CTR',
            'priority': 'medium'
        })
    
    if roas > 3:
        recommendations.append({
            'type': 'scale_campaign',
            'description': 'Increase budget to scale this high-performing campaign',
            'priority': 'high'
        })
    
    return recommendations

def _calculate_campaign_priority(campaign_data):
    """Calculate optimization priority for a campaign (1-10 scale)"""
    acos = campaign_data['acos']
    roas = campaign_data['roas']
    spend = campaign_data['total_spend']
    
    priority = 5  # Base priority
    
    # High spend campaigns get higher priority
    if spend > 1000:
        priority += 2
    elif spend > 500:
        priority += 1
    
    # High ACOS increases priority
    if acos > 60:
        priority += 3
    elif acos > 40:
        priority += 2
    elif acos > 30:
        priority += 1
    
    # High ROAS for scaling
    if roas > 4:
        priority += 2
    elif roas > 3:
        priority += 1
    
    return min(priority, 10)

def _simulate_changes(current_performance, changes):
    """Simulate the impact of proposed changes"""
    simulated = current_performance.copy()
    
    # Apply bid changes
    if 'bid_adjustment' in changes:
        bid_change = changes['bid_adjustment'] / 100  # Convert percentage to decimal
        
        # Estimate impact (simplified model)
        simulated['total_spend'] *= (1 + bid_change * 0.8)  # Spend changes less than bid
        simulated['total_clicks'] *= (1 + bid_change * 0.6)  # Clicks increase with higher bids
        simulated['total_sales'] *= (1 + bid_change * 0.4)   # Sales increase but less than clicks
    
    # Apply budget changes
    if 'budget_adjustment' in changes:
        budget_change = changes['budget_adjustment'] / 100
        simulated['total_spend'] *= (1 + budget_change)
        simulated['total_sales'] *= (1 + budget_change * 0.7)  # Sales don't scale linearly
    
    # Recalculate derived metrics
    if simulated['total_sales'] > 0:
        simulated['overall_acos'] = (simulated['total_spend'] / simulated['total_sales']) * 100
    if simulated['total_spend'] > 0:
        simulated['overall_roas'] = simulated['total_sales'] / simulated['total_spend']
    
    return simulated

