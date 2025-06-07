"""
Supabase data service for reports and analysis
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from src.config.supabase import SupabaseConfig

class SupabaseDataService:
    """Data service using Supabase for reports and analysis"""
    
    def __init__(self):
        self.client = SupabaseConfig.get_client()
    
    def create_report(self, user_id: int, filename: str, file_type: str) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new report record
        
        Args:
            user_id: User's ID
            filename: Name of uploaded file
            file_type: Type of file (csv, xlsx, etc.)
            
        Returns:
            Tuple of (success, message, report_id)
        """
        try:
            report_data = {
                'user_id': user_id,
                'filename': filename,
                'file_type': file_type,
                'upload_date': datetime.now().isoformat(),
                'processed': False,
                'processing_status': 'pending'
            }
            
            result = self.client.table('reports').insert(report_data).execute()
            
            if result.data:
                report_id = result.data[0]['id']
                return True, "Report created successfully", report_id
            else:
                return False, "Failed to create report", None
                
        except Exception as e:
            return False, f"Report creation failed: {str(e)}", None
    
    def update_report_processing(self, report_id: int, status: str, error_message: str = None, 
                               processed_data: Dict = None) -> bool:
        """
        Update report processing status
        
        Args:
            report_id: Report ID
            status: Processing status (processing, completed, failed)
            error_message: Error message if failed
            processed_data: Processed report data
            
        Returns:
            Success status
        """
        try:
            update_data = {
                'processing_status': status,
                'processed': status == 'completed'
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            if processed_data:
                # Update report summary data
                update_data.update({
                    'date_range_start': processed_data.get('date_range_start'),
                    'date_range_end': processed_data.get('date_range_end'),
                    'total_spend': processed_data.get('total_spend'),
                    'total_sales': processed_data.get('total_sales'),
                    'acos': processed_data.get('acos'),
                    'total_impressions': processed_data.get('total_impressions'),
                    'total_clicks': processed_data.get('total_clicks')
                })
            
            result = self.client.table('reports').update(update_data).eq('id', report_id).execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"Failed to update report processing: {str(e)}")
            return False
    
    def save_campaign_data(self, report_id: int, campaigns: List[Dict]) -> bool:
        """
        Save campaign data to database
        
        Args:
            report_id: Report ID
            campaigns: List of campaign data dictionaries
            
        Returns:
            Success status
        """
        try:
            # Prepare campaign data for insertion
            campaign_records = []
            for campaign in campaigns:
                record = {
                    'report_id': report_id,
                    'campaign_name': campaign.get('campaign_name'),
                    'campaign_id': campaign.get('campaign_id'),
                    'campaign_type': campaign.get('campaign_type'),
                    'targeting_type': campaign.get('targeting_type'),
                    'state': campaign.get('state'),
                    'daily_budget': campaign.get('daily_budget'),
                    'start_date': campaign.get('start_date'),
                    'end_date': campaign.get('end_date'),
                    'impressions': campaign.get('impressions'),
                    'clicks': campaign.get('clicks'),
                    'cost': campaign.get('cost'),
                    'sales': campaign.get('sales'),
                    'orders': campaign.get('orders'),
                    'acos': campaign.get('acos'),
                    'roas': campaign.get('roas'),
                    'ctr': campaign.get('ctr'),
                    'cpc': campaign.get('cpc'),
                    'cvr': campaign.get('cvr')
                }
                campaign_records.append(record)
            
            # Insert campaign data in batches
            batch_size = 100
            for i in range(0, len(campaign_records), batch_size):
                batch = campaign_records[i:i + batch_size]
                result = self.client.table('campaign_data').insert(batch).execute()
                if not result.data:
                    return False
            
            return True
            
        except Exception as e:
            print(f"Failed to save campaign data: {str(e)}")
            return False
    
    def save_analysis_session(self, report_id: int, user_id: int, analysis_type: str,
                            ai_model: str, analysis_results: Dict, recommendations: Dict,
                            performance_summary: Dict) -> Tuple[bool, Optional[int]]:
        """
        Save analysis session results
        
        Args:
            report_id: Report ID
            user_id: User ID
            analysis_type: Type of analysis performed
            ai_model: AI model used for analysis
            analysis_results: Analysis results data
            recommendations: Optimization recommendations
            performance_summary: Performance summary data
            
        Returns:
            Tuple of (success, session_id)
        """
        try:
            session_data = {
                'report_id': report_id,
                'user_id': user_id,
                'session_date': datetime.now().isoformat(),
                'analysis_type': analysis_type,
                'ai_model_used': ai_model,
                'analysis_results': analysis_results,
                'recommendations': recommendations,
                'performance_summary': performance_summary
            }
            
            result = self.client.table('analysis_sessions').insert(session_data).execute()
            
            if result.data:
                session_id = result.data[0]['id']
                return True, session_id
            else:
                return False, None
                
        except Exception as e:
            print(f"Failed to save analysis session: {str(e)}")
            return False, None
    
    def get_user_reports(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get user's reports
        
        Args:
            user_id: User ID
            limit: Maximum number of reports to return
            
        Returns:
            List of report dictionaries
        """
        try:
            result = self.client.table('reports').select('*').eq('user_id', user_id).order('upload_date', desc=True).limit(limit).execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Failed to get user reports: {str(e)}")
            return []
    
    def get_report_details(self, report_id: int, user_id: int) -> Optional[Dict]:
        """
        Get detailed report information
        
        Args:
            report_id: Report ID
            user_id: User ID (for security)
            
        Returns:
            Report details dictionary or None
        """
        try:
            result = self.client.table('reports').select('*').eq('id', report_id).eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"Failed to get report details: {str(e)}")
            return None
    
    def get_campaign_data(self, report_id: int) -> List[Dict]:
        """
        Get campaign data for a report
        
        Args:
            report_id: Report ID
            
        Returns:
            List of campaign data dictionaries
        """
        try:
            result = self.client.table('campaign_data').select('*').eq('report_id', report_id).execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Failed to get campaign data: {str(e)}")
            return []
    
    def get_analysis_sessions(self, report_id: int) -> List[Dict]:
        """
        Get analysis sessions for a report
        
        Args:
            report_id: Report ID
            
        Returns:
            List of analysis session dictionaries
        """
        try:
            result = self.client.table('analysis_sessions').select('*').eq('report_id', report_id).order('session_date', desc=True).execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Failed to get analysis sessions: {str(e)}")
            return []
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Get user statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user statistics
        """
        try:
            # Get report count
            reports_result = self.client.table('reports').select('id', count='exact').eq('user_id', user_id).execute()
            total_reports = reports_result.count if reports_result.count else 0
            
            # Get processed reports count
            processed_result = self.client.table('reports').select('id', count='exact').eq('user_id', user_id).eq('processed', True).execute()
            processed_reports = processed_result.count if processed_result.count else 0
            
            # Get analysis sessions count
            sessions_result = self.client.table('analysis_sessions').select('id', count='exact').eq('user_id', user_id).execute()
            total_sessions = sessions_result.count if sessions_result.count else 0
            
            return {
                'total_reports': total_reports,
                'processed_reports': processed_reports,
                'total_sessions': total_sessions,
                'success_rate': (processed_reports / total_reports * 100) if total_reports > 0 else 0
            }
            
        except Exception as e:
            print(f"Failed to get user stats: {str(e)}")
            return {
                'total_reports': 0,
                'processed_reports': 0,
                'total_sessions': 0,
                'success_rate': 0
            }

