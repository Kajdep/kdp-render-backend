"""
Export routes using Supabase
"""
from flask import Blueprint, request, jsonify, make_response
import csv
import json
from io import StringIO
from src.services.supabase_data import SupabaseDataService
from src.routes.auth_supabase import require_auth

export_bp = Blueprint('export', __name__)
data_service = SupabaseDataService()

@export_bp.route('/<int:report_id>/campaigns', methods=['GET'])
@require_auth
def export_campaign_data(report_id):
    """Export campaign data as CSV"""
    try:
        user_id = request.current_user['id']
        
        # Verify user owns the report
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get campaign data
        campaigns = data_service.get_campaign_data(report_id)
        if not campaigns:
            return jsonify({'error': 'No campaign data found'}), 404
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [
            'Campaign Name', 'Campaign ID', 'Campaign Type', 'Targeting Type',
            'State', 'Daily Budget', 'Start Date', 'End Date',
            'Impressions', 'Clicks', 'Cost', 'Sales', 'Orders',
            'ACOS', 'ROAS', 'CTR', 'CPC', 'CVR'
        ]
        writer.writerow(headers)
        
        # Write data
        for campaign in campaigns:
            row = [
                campaign.get('campaign_name', ''),
                campaign.get('campaign_id', ''),
                campaign.get('campaign_type', ''),
                campaign.get('targeting_type', ''),
                campaign.get('state', ''),
                campaign.get('daily_budget', ''),
                campaign.get('start_date', ''),
                campaign.get('end_date', ''),
                campaign.get('impressions', 0),
                campaign.get('clicks', 0),
                campaign.get('cost', 0),
                campaign.get('sales', 0),
                campaign.get('orders', 0),
                campaign.get('acos', 0),
                campaign.get('roas', 0),
                campaign.get('ctr', 0),
                campaign.get('cpc', 0),
                campaign.get('cvr', 0)
            ]
            writer.writerow(row)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=campaign_data_{report_id}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@export_bp.route('/<int:report_id>/analysis', methods=['GET'])
@require_auth
def export_analysis_data(report_id):
    """Export analysis data as JSON"""
    try:
        user_id = request.current_user['id']
        
        # Verify user owns the report
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get analysis sessions
        sessions = data_service.get_analysis_sessions(report_id)
        if not sessions:
            return jsonify({'error': 'No analysis data found'}), 404
        
        # Get campaign data
        campaigns = data_service.get_campaign_data(report_id)
        
        # Prepare export data
        export_data = {
            'report_info': {
                'id': report['id'],
                'filename': report['filename'],
                'upload_date': report['upload_date'],
                'date_range_start': report.get('date_range_start'),
                'date_range_end': report.get('date_range_end'),
                'total_spend': float(report.get('total_spend', 0)) if report.get('total_spend') else 0,
                'total_sales': float(report.get('total_sales', 0)) if report.get('total_sales') else 0,
                'acos': float(report.get('acos', 0)) if report.get('acos') else 0
            },
            'campaigns': campaigns,
            'analysis_sessions': sessions
        }
        
        # Create response
        response = make_response(json.dumps(export_data, indent=2, default=str))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=analysis_data_{report_id}.json'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@export_bp.route('/<int:report_id>/recommendations', methods=['GET'])
@require_auth
def export_recommendations(report_id):
    """Export optimization recommendations as CSV"""
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
            return jsonify({'error': 'No optimization data found'}), 404
        
        # Get latest recommendations
        latest_session = optimization_sessions[0]
        recommendations = latest_session.get('recommendations', {})
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write campaign recommendations
        writer.writerow(['Campaign Recommendations'])
        writer.writerow(['Campaign', 'Issue', 'Current Value', 'Recommendation', 'Priority', 'Potential Impact'])
        
        for rec in recommendations.get('campaign_recommendations', []):
            writer.writerow([
                rec.get('campaign', ''),
                rec.get('issue', ''),
                rec.get('current_acos', rec.get('current_impressions', '')),
                rec.get('recommendation', ''),
                rec.get('priority', ''),
                rec.get('potential_savings', rec.get('potential_revenue_increase', ''))
            ])
        
        writer.writerow([])  # Empty row
        
        # Write bid adjustments
        writer.writerow(['Bid Adjustments'])
        writer.writerow(['Campaign', 'Current CPC', 'Recommendation', 'Reason'])
        
        for rec in recommendations.get('bid_adjustments', []):
            writer.writerow([
                rec.get('campaign', ''),
                rec.get('current_cpc', ''),
                rec.get('recommendation', ''),
                rec.get('reason', '')
            ])
        
        writer.writerow([])  # Empty row
        
        # Write budget recommendations
        writer.writerow(['Budget Recommendations'])
        writer.writerow(['Campaign', 'Action', 'Current Budget', 'Recommended Change', 'Reason'])
        
        for rec in recommendations.get('budget_recommendations', []):
            writer.writerow([
                rec.get('campaign', ''),
                rec.get('action', ''),
                rec.get('current_budget', ''),
                rec.get('recommended_increase', rec.get('recommended_decrease', '')),
                rec.get('reason', '')
            ])
        
        writer.writerow([])  # Empty row
        
        # Write scaling opportunities
        writer.writerow(['Scaling Opportunities'])
        writer.writerow(['Campaign', 'Current ACOS', 'Current Sales', 'Recommendation', 'Priority', 'Potential Revenue'])
        
        for rec in recommendations.get('scaling_opportunities', []):
            writer.writerow([
                rec.get('campaign', ''),
                rec.get('current_acos', ''),
                rec.get('current_sales', ''),
                rec.get('recommendation', ''),
                rec.get('priority', ''),
                rec.get('potential_revenue_increase', '')
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=recommendations_{report_id}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@export_bp.route('/<int:report_id>/summary', methods=['GET'])
@require_auth
def export_summary_report(report_id):
    """Export comprehensive summary report as text"""
    try:
        user_id = request.current_user['id']
        
        # Verify user owns the report
        report = data_service.get_report_details(report_id, user_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get all data
        campaigns = data_service.get_campaign_data(report_id)
        sessions = data_service.get_analysis_sessions(report_id)
        
        # Generate summary report
        summary_lines = []
        summary_lines.append("=" * 60)
        summary_lines.append("AMAZON KDP ADVERTISING ANALYSIS REPORT")
        summary_lines.append("=" * 60)
        summary_lines.append("")
        
        # Report info
        summary_lines.append("REPORT INFORMATION")
        summary_lines.append("-" * 20)
        summary_lines.append(f"Filename: {report['filename']}")
        summary_lines.append(f"Upload Date: {report['upload_date']}")
        summary_lines.append(f"Processing Status: {report['processing_status']}")
        summary_lines.append("")
        
        # Performance overview
        if campaigns:
            total_spend = sum(float(c.get('cost', 0)) for c in campaigns)
            total_sales = sum(float(c.get('sales', 0)) for c in campaigns)
            total_impressions = sum(int(c.get('impressions', 0)) for c in campaigns)
            total_clicks = sum(int(c.get('clicks', 0)) for c in campaigns)
            
            summary_lines.append("PERFORMANCE OVERVIEW")
            summary_lines.append("-" * 20)
            summary_lines.append(f"Total Campaigns: {len(campaigns)}")
            summary_lines.append(f"Total Spend: ${total_spend:.2f}")
            summary_lines.append(f"Total Sales: ${total_sales:.2f}")
            summary_lines.append(f"Overall ACOS: {(total_spend/total_sales*100):.2f}%" if total_sales > 0 else "Overall ACOS: N/A")
            summary_lines.append(f"Total Impressions: {total_impressions:,}")
            summary_lines.append(f"Total Clicks: {total_clicks:,}")
            summary_lines.append(f"Average CTR: {(total_clicks/total_impressions*100):.4f}%" if total_impressions > 0 else "Average CTR: N/A")
            summary_lines.append("")
        
        # Analysis sessions
        if sessions:
            summary_lines.append("ANALYSIS SESSIONS")
            summary_lines.append("-" * 20)
            for session in sessions[:5]:  # Show last 5 sessions
                summary_lines.append(f"Date: {session['session_date']}")
                summary_lines.append(f"Type: {session['analysis_type']}")
                summary_lines.append(f"AI Model: {session['ai_model_used']}")
                summary_lines.append("")
        
        # Top recommendations
        optimization_sessions = [s for s in sessions if s.get('analysis_type') == 'optimization']
        if optimization_sessions:
            latest_recommendations = optimization_sessions[0].get('recommendations', {})
            campaign_recs = latest_recommendations.get('campaign_recommendations', [])
            
            if campaign_recs:
                summary_lines.append("TOP RECOMMENDATIONS")
                summary_lines.append("-" * 20)
                for i, rec in enumerate(campaign_recs[:5], 1):
                    summary_lines.append(f"{i}. {rec.get('campaign', 'Unknown Campaign')}")
                    summary_lines.append(f"   Issue: {rec.get('issue', 'N/A')}")
                    summary_lines.append(f"   Recommendation: {rec.get('recommendation', 'N/A')}")
                    summary_lines.append(f"   Priority: {rec.get('priority', 'N/A')}")
                    summary_lines.append("")
        
        summary_lines.append("=" * 60)
        summary_lines.append("Report generated by KDP Advertising Tool")
        summary_lines.append("=" * 60)
        
        # Create response
        summary_text = "\n".join(summary_lines)
        response = make_response(summary_text)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=summary_report_{report_id}.txt'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

