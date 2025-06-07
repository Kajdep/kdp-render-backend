from flask import Blueprint, request, jsonify, send_file, make_response
import json
import csv
import io
from datetime import datetime
from src.models.user import db, Report, CampaignData, AnalysisSession
from src.services.report_processor import ReportProcessor

export_bp = Blueprint('export', __name__)

@export_bp.route('/<int:report_id>/csv', methods=['GET'])
def export_csv(report_id):
    """Export report analysis as CSV"""
    try:
        # Get report and campaign data
        report = Report.query.get_or_404(report_id)
        campaign_data = CampaignData.query.filter_by(report_id=report_id).all()
        
        if not campaign_data:
            return jsonify({'error': 'No data found for this report'}), 404
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Campaign ID', 'Campaign Name', 'Date', 'Impressions', 'Clicks', 
            'CTR (%)', 'CPC ($)', 'Spend ($)', 'Sales ($)', 'ACOS (%)', 
            'ROAS', 'Orders', 'Units', 'Conversion Rate (%)'
        ]
        writer.writerow(headers)
        
        # Write data rows
        for data in campaign_data:
            row = [
                data.amazon_campaign_id,
                data.campaign_name,
                data.date.isoformat() if data.date else '',
                data.impressions or 0,
                data.clicks or 0,
                round(data.ctr, 2) if data.ctr else 0,
                round(data.cpc, 2) if data.cpc else 0,
                round(data.spend, 2) if data.spend else 0,
                round(data.sales, 2) if data.sales else 0,
                round(data.acos, 2) if data.acos else 0,
                round(data.roas, 2) if data.roas else 0,
                data.orders or 0,
                data.units or 0,
                round(data.conversion_rate, 2) if data.conversion_rate else 0
            ]
            writer.writerow(row)
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="{report.filename}_analysis.csv"'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export CSV: {str(e)}'}), 500

@export_bp.route('/<int:report_id>/analysis-csv', methods=['GET'])
def export_analysis_csv(report_id):
    """Export comprehensive analysis as CSV"""
    try:
        # Get analytics
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        # Create CSV with analysis summary
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Performance Summary Section
        writer.writerow(['PERFORMANCE SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        
        performance = analytics['performance_summary']
        writer.writerow(['Total Spend', f"${performance['total_spend']:.2f}"])
        writer.writerow(['Total Sales', f"${performance['total_sales']:.2f}"])
        writer.writerow(['Total Impressions', f"{performance['total_impressions']:,}"])
        writer.writerow(['Total Clicks', f"{performance['total_clicks']:,}"])
        writer.writerow(['Overall ACOS', f"{performance['overall_acos']:.2f}%"])
        writer.writerow(['Overall ROAS', f"{performance['overall_roas']:.2f}x"])
        writer.writerow(['Overall CTR', f"{performance['overall_ctr']:.2f}%"])
        writer.writerow(['Overall CPC', f"${performance['overall_cpc']:.2f}"])
        writer.writerow(['Conversion Rate', f"{performance['conversion_rate']:.2f}%"])
        writer.writerow([])  # Empty row
        
        # Campaign Analysis Section
        writer.writerow(['TOP PERFORMING CAMPAIGNS'])
        writer.writerow(['Campaign Name', 'ACOS (%)', 'ROAS', 'Spend ($)', 'Sales ($)'])
        
        for campaign_id, campaign_data in analytics['campaign_analysis']['top_performers'][:10]:
            writer.writerow([
                campaign_data['name'],
                f"{campaign_data['acos']:.2f}",
                f"{campaign_data['roas']:.2f}",
                f"{campaign_data['total_spend']:.2f}",
                f"{campaign_data['total_sales']:.2f}"
            ])
        
        writer.writerow([])  # Empty row
        
        # Recommendations Section
        writer.writerow(['OPTIMIZATION RECOMMENDATIONS'])
        writer.writerow(['Priority', 'Type', 'Title', 'Description'])
        
        for i, rec in enumerate(analytics['recommendations'], 1):
            writer.writerow([
                rec.get('priority', 'medium'),
                rec.get('type', ''),
                rec.get('title', ''),
                rec.get('description', '')
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="analysis_summary_{report_id}.csv"'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export analysis CSV: {str(e)}'}), 500

@export_bp.route('/<int:report_id>/json', methods=['GET'])
def export_json(report_id):
    """Export complete analysis as JSON"""
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
            'export_info': {
                'exported_at': datetime.utcnow().isoformat(),
                'report_id': report_id,
                'export_type': 'complete_analysis',
                'version': '1.0'
            },
            'analysis': analysis_data
        }
        
        # Create response
        response = make_response(json.dumps(export_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename="complete_analysis_{report_id}.json"'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export JSON: {str(e)}'}), 500

@export_bp.route('/<int:report_id>/recommendations-csv', methods=['GET'])
def export_recommendations_csv(report_id):
    """Export optimization recommendations as CSV"""
    try:
        # Get optimization recommendations
        from src.routes.optimization import get_optimization_recommendations
        
        # This is a bit hacky, but we'll call the optimization endpoint internally
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        # Create CSV with recommendations
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'Recommendation Type', 'Priority', 'Campaign', 'Action', 
            'Reason', 'Expected Impact', 'Current Metrics'
        ])
        
        # Campaign recommendations
        for rec in analytics['recommendations']:
            writer.writerow([
                rec.get('type', ''),
                rec.get('priority', ''),
                rec.get('title', ''),
                rec.get('description', ''),
                '',  # reason
                '',  # expected impact
                ''   # current metrics
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="recommendations_{report_id}.csv"'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export recommendations: {str(e)}'}), 500

@export_bp.route('/<int:report_id>/summary-report', methods=['GET'])
def export_summary_report(report_id):
    """Export a comprehensive summary report"""
    try:
        # Get report and analytics
        report = Report.query.get_or_404(report_id)
        processor = ReportProcessor()
        analytics = processor.get_report_analytics(report_id)
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        # Create comprehensive text report
        output = io.StringIO()
        
        # Header
        output.write("="*60 + "\n")
        output.write("AMAZON KDP ADVERTISING ANALYSIS REPORT\n")
        output.write("="*60 + "\n\n")
        
        output.write(f"Report: {report.filename}\n")
        output.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
        if report.date_range_start and report.date_range_end:
            output.write(f"Data Period: {report.date_range_start} to {report.date_range_end}\n")
        output.write("\n")
        
        # Performance Summary
        output.write("PERFORMANCE SUMMARY\n")
        output.write("-"*30 + "\n")
        
        perf = analytics['performance_summary']
        output.write(f"Total Spend: ${perf['total_spend']:,.2f}\n")
        output.write(f"Total Sales: ${perf['total_sales']:,.2f}\n")
        output.write(f"Total Impressions: {perf['total_impressions']:,}\n")
        output.write(f"Total Clicks: {perf['total_clicks']:,}\n")
        output.write(f"Overall ACOS: {perf['overall_acos']:.2f}%\n")
        output.write(f"Overall ROAS: {perf['overall_roas']:.2f}x\n")
        output.write(f"Overall CTR: {perf['overall_ctr']:.2f}%\n")
        output.write(f"Overall CPC: ${perf['overall_cpc']:.2f}\n")
        output.write(f"Conversion Rate: {perf['conversion_rate']:.2f}%\n\n")
        
        # Campaign Analysis
        output.write("CAMPAIGN ANALYSIS\n")
        output.write("-"*30 + "\n")
        
        camp_analysis = analytics['campaign_analysis']
        output.write(f"Total Campaigns: {camp_analysis['total_campaigns']}\n\n")
        
        output.write("Top Performing Campaigns:\n")
        for i, (campaign_id, campaign_data) in enumerate(camp_analysis['top_performers'][:5], 1):
            output.write(f"{i}. {campaign_data['name']}\n")
            output.write(f"   ACOS: {campaign_data['acos']:.2f}% | ROAS: {campaign_data['roas']:.2f}x\n")
            output.write(f"   Spend: ${campaign_data['total_spend']:.2f} | Sales: ${campaign_data['total_sales']:.2f}\n\n")
        
        # Recommendations
        output.write("OPTIMIZATION RECOMMENDATIONS\n")
        output.write("-"*30 + "\n")
        
        for i, rec in enumerate(analytics['recommendations'], 1):
            output.write(f"{i}. {rec.get('title', 'Recommendation')}\n")
            output.write(f"   Priority: {rec.get('priority', 'medium').upper()}\n")
            output.write(f"   Description: {rec.get('description', '')}\n")
            if 'affected_campaigns' in rec:
                output.write(f"   Affected Campaigns: {rec['affected_campaigns']}\n")
            output.write("\n")
        
        # Trend Analysis
        if 'trend_analysis' in analytics:
            output.write("TREND ANALYSIS\n")
            output.write("-"*30 + "\n")
            trend = analytics['trend_analysis']
            output.write(f"Trend Direction: {trend.get('trend_direction', 'unknown').upper()}\n")
            output.write(f"Daily Performance Data Points: {len(trend.get('daily_performance', {}))}\n\n")
        
        # Footer
        output.write("="*60 + "\n")
        output.write("Generated by KDP Advertising Tool\n")
        output.write("For more detailed analysis, visit the web application\n")
        output.write("="*60 + "\n")
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename="summary_report_{report_id}.txt"'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export summary report: {str(e)}'}), 500

@export_bp.route('/formats', methods=['GET'])
def get_export_formats():
    """Get available export formats"""
    return jsonify({
        'formats': [
            {
                'id': 'csv',
                'name': 'Campaign Data (CSV)',
                'description': 'Raw campaign data in CSV format',
                'file_extension': '.csv',
                'mime_type': 'text/csv'
            },
            {
                'id': 'analysis-csv',
                'name': 'Analysis Summary (CSV)',
                'description': 'Performance summary and top campaigns',
                'file_extension': '.csv',
                'mime_type': 'text/csv'
            },
            {
                'id': 'json',
                'name': 'Complete Analysis (JSON)',
                'description': 'Full analysis data in JSON format',
                'file_extension': '.json',
                'mime_type': 'application/json'
            },
            {
                'id': 'recommendations-csv',
                'name': 'Recommendations (CSV)',
                'description': 'Optimization recommendations',
                'file_extension': '.csv',
                'mime_type': 'text/csv'
            },
            {
                'id': 'summary-report',
                'name': 'Summary Report (TXT)',
                'description': 'Comprehensive text report',
                'file_extension': '.txt',
                'mime_type': 'text/plain'
            }
        ]
    })

@export_bp.route('/bulk', methods=['POST'])
def bulk_export():
    """Export multiple reports in a single archive"""
    try:
        data = request.get_json()
        report_ids = data.get('report_ids', [])
        export_format = data.get('format', 'csv')
        
        if not report_ids:
            return jsonify({'error': 'No report IDs provided'}), 400
        
        # For now, return individual download links
        # In a full implementation, this would create a ZIP archive
        download_links = []
        
        for report_id in report_ids:
            report = Report.query.get(report_id)
            if report:
                download_links.append({
                    'report_id': report_id,
                    'report_name': report.filename,
                    'download_url': f'/api/export/{report_id}/{export_format}'
                })
        
        return jsonify({
            'bulk_export_id': f'bulk_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
            'download_links': download_links,
            'total_reports': len(download_links)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create bulk export: {str(e)}'}), 500

