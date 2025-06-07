import csv
import json
from datetime import datetime, timedelta
import re
import os
from typing import Dict, List, Optional, Tuple
from src.models.user import db, Report, CampaignData, Keyword, KeywordData

class ReportProcessor:
    """Enhanced report processor for Amazon advertising data"""
    
    def __init__(self):
        self.supported_formats = {
            'sponsored_products_campaign': self._process_sponsored_products_campaign,
            'sponsored_products_keyword': self._process_sponsored_products_keyword,
            'sponsored_brands_campaign': self._process_sponsored_brands_campaign,
            'sponsored_brands_keyword': self._process_sponsored_brands_keyword,
            'sponsored_display_campaign': self._process_sponsored_display_campaign,
            'search_term': self._process_search_term_report
        }
    
    def process_report(self, file_path: str, report_id: int) -> Dict:
        """Process uploaded report file and extract data"""
        try:
            # Detect report type from filename and content
            report_type = self._detect_report_type(file_path)
            
            if report_type not in self.supported_formats:
                raise ValueError(f"Unsupported report type: {report_type}")
            
            # Process the specific report type
            processor = self.supported_formats[report_type]
            result = processor(file_path, report_id)
            
            # Add metadata
            result['report_type'] = report_type
            result['processed_at'] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to process report: {str(e)}")
    
    def _detect_report_type(self, file_path: str) -> str:
        """Detect report type from filename and content"""
        filename = os.path.basename(file_path).lower()
        
        # Check filename patterns
        if 'sponsored_products' in filename and 'campaign' in filename:
            return 'sponsored_products_campaign'
        elif 'sponsored_products' in filename and ('keyword' in filename or 'targeting' in filename):
            return 'sponsored_products_keyword'
        elif 'sponsored_brands' in filename and 'campaign' in filename:
            return 'sponsored_brands_campaign'
        elif 'sponsored_brands' in filename and ('keyword' in filename or 'targeting' in filename):
            return 'sponsored_brands_keyword'
        elif 'sponsored_display' in filename:
            return 'sponsored_display_campaign'
        elif 'search_term' in filename or 'search-term' in filename:
            return 'search_term'
        
        # If filename doesn't match, check content headers
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader, [])
                headers_lower = [h.lower().strip() for h in headers]
                
                # Check for specific column patterns
                if 'campaign name' in headers_lower and 'impressions' in headers_lower:
                    if 'keyword' in headers_lower or 'targeting' in headers_lower:
                        return 'sponsored_products_keyword'
                    else:
                        return 'sponsored_products_campaign'
                elif 'search term' in headers_lower:
                    return 'search_term'
                
        except Exception:
            pass
        
        # Default to sponsored products campaign
        return 'sponsored_products_campaign'
    
    def _process_sponsored_products_campaign(self, file_path: str, report_id: int) -> Dict:
        """Process Sponsored Products campaign report"""
        campaigns_processed = 0
        total_spend = 0
        total_sales = 0
        total_impressions = 0
        total_clicks = 0
        date_range_start = None
        date_range_end = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Clean and normalize column names
                    row = {k.strip().lower(): v.strip() for k, v in row.items()}
                    
                    # Extract campaign data
                    campaign_data = self._extract_campaign_data(row)
                    if not campaign_data:
                        continue
                    
                    # Save to database
                    db_campaign_data = CampaignData(
                        report_id=report_id,
                        amazon_campaign_id=campaign_data['campaign_id'],
                        campaign_name=campaign_data['campaign_name'],
                        date=campaign_data['date'],
                        impressions=campaign_data['impressions'],
                        clicks=campaign_data['clicks'],
                        ctr=campaign_data['ctr'],
                        cpc=campaign_data['cpc'],
                        spend=campaign_data['spend'],
                        sales=campaign_data['sales'],
                        acos=campaign_data['acos'],
                        roas=campaign_data['roas'],
                        orders=campaign_data['orders'],
                        units=campaign_data['units'],
                        conversion_rate=campaign_data['conversion_rate']
                    )
                    
                    db.session.add(db_campaign_data)
                    
                    # Aggregate totals
                    campaigns_processed += 1
                    total_spend += campaign_data['spend']
                    total_sales += campaign_data['sales']
                    total_impressions += campaign_data['impressions']
                    total_clicks += campaign_data['clicks']
                    
                    # Track date range
                    if not date_range_start or campaign_data['date'] < date_range_start:
                        date_range_start = campaign_data['date']
                    if not date_range_end or campaign_data['date'] > date_range_end:
                        date_range_end = campaign_data['date']
                
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error processing campaign data: {str(e)}")
        
        return {
            'campaigns_processed': campaigns_processed,
            'total_spend': total_spend,
            'total_sales': total_sales,
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'date_range_start': date_range_start,
            'date_range_end': date_range_end,
            'acos': (total_spend / total_sales * 100) if total_sales > 0 else 0
        }
    
    def _process_sponsored_products_keyword(self, file_path: str, report_id: int) -> Dict:
        """Process Sponsored Products keyword report"""
        keywords_processed = 0
        total_spend = 0
        total_sales = 0
        total_impressions = 0
        total_clicks = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    row = {k.strip().lower(): v.strip() for k, v in row.items()}
                    
                    keyword_data = self._extract_keyword_data(row)
                    if not keyword_data:
                        continue
                    
                    # Save keyword data
                    db_keyword_data = KeywordData(
                        keyword_id=None,  # Will be linked later if needed
                        report_id=report_id,
                        date=keyword_data['date'],
                        impressions=keyword_data['impressions'],
                        clicks=keyword_data['clicks'],
                        ctr=keyword_data['ctr'],
                        cpc=keyword_data['cpc'],
                        spend=keyword_data['spend'],
                        sales=keyword_data['sales'],
                        acos=keyword_data['acos'],
                        orders=keyword_data['orders'],
                        units=keyword_data['units']
                    )
                    
                    db.session.add(db_keyword_data)
                    
                    keywords_processed += 1
                    total_spend += keyword_data['spend']
                    total_sales += keyword_data['sales']
                    total_impressions += keyword_data['impressions']
                    total_clicks += keyword_data['clicks']
                
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error processing keyword data: {str(e)}")
        
        return {
            'keywords_processed': keywords_processed,
            'total_spend': total_spend,
            'total_sales': total_sales,
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'acos': (total_spend / total_sales * 100) if total_sales > 0 else 0
        }
    
    def _process_sponsored_brands_campaign(self, file_path: str, report_id: int) -> Dict:
        """Process Sponsored Brands campaign report"""
        return self._process_sponsored_products_campaign(file_path, report_id)
    
    def _process_sponsored_brands_keyword(self, file_path: str, report_id: int) -> Dict:
        """Process Sponsored Brands keyword report"""
        return self._process_sponsored_products_keyword(file_path, report_id)
    
    def _process_sponsored_display_campaign(self, file_path: str, report_id: int) -> Dict:
        """Process Sponsored Display campaign report"""
        return self._process_sponsored_products_campaign(file_path, report_id)
    
    def _process_search_term_report(self, file_path: str, report_id: int) -> Dict:
        """Process Search Term report"""
        search_terms_processed = 0
        total_spend = 0
        total_sales = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    row = {k.strip().lower(): v.strip() for k, v in row.items()}
                    
                    # Process search term data (similar to keyword data)
                    search_term_data = self._extract_search_term_data(row)
                    if not search_term_data:
                        continue
                    
                    search_terms_processed += 1
                    total_spend += search_term_data.get('spend', 0)
                    total_sales += search_term_data.get('sales', 0)
                
        except Exception as e:
            raise Exception(f"Error processing search term data: {str(e)}")
        
        return {
            'search_terms_processed': search_terms_processed,
            'total_spend': total_spend,
            'total_sales': total_sales,
            'acos': (total_spend / total_sales * 100) if total_sales > 0 else 0
        }
    
    def _extract_campaign_data(self, row: Dict) -> Optional[Dict]:
        """Extract campaign data from CSV row"""
        try:
            # Map common column variations
            column_mappings = {
                'campaign_id': ['campaign id', 'campaignid', 'campaign'],
                'campaign_name': ['campaign name', 'campaignname', 'campaign'],
                'date': ['date', 'day', 'report date'],
                'impressions': ['impressions', 'impr'],
                'clicks': ['clicks', 'click'],
                'spend': ['spend', 'cost', 'total spend'],
                'sales': ['sales', 'attributed sales 7d', 'attributed sales 14d', 'attributed sales 30d'],
                'orders': ['orders', 'attributed orders 7d', 'attributed orders 14d', 'attributed orders 30d'],
                'units': ['units', 'attributed units 7d', 'attributed units 14d', 'attributed units 30d']
            }
            
            # Extract values using mappings
            data = {}
            for field, possible_columns in column_mappings.items():
                value = None
                for col in possible_columns:
                    if col in row and row[col]:
                        value = row[col]
                        break
                
                if field == 'date':
                    data[field] = self._parse_date(value) if value else datetime.utcnow().date()
                elif field in ['campaign_id', 'campaign_name']:
                    data[field] = str(value) if value else ''
                else:
                    data[field] = self._parse_number(value)
            
            # Calculate derived metrics
            data['ctr'] = (data['clicks'] / data['impressions'] * 100) if data['impressions'] > 0 else 0
            data['cpc'] = (data['spend'] / data['clicks']) if data['clicks'] > 0 else 0
            data['acos'] = (data['spend'] / data['sales'] * 100) if data['sales'] > 0 else 0
            data['roas'] = (data['sales'] / data['spend']) if data['spend'] > 0 else 0
            data['conversion_rate'] = (data['orders'] / data['clicks'] * 100) if data['clicks'] > 0 else 0
            
            # Validate required fields
            if not data['campaign_name']:
                return None
            
            return data
            
        except Exception as e:
            print(f"Error extracting campaign data: {e}")
            return None
    
    def _extract_keyword_data(self, row: Dict) -> Optional[Dict]:
        """Extract keyword data from CSV row"""
        try:
            column_mappings = {
                'keyword': ['keyword', 'targeting', 'keyword text'],
                'match_type': ['match type', 'matchtype', 'targeting type'],
                'date': ['date', 'day', 'report date'],
                'impressions': ['impressions', 'impr'],
                'clicks': ['clicks', 'click'],
                'spend': ['spend', 'cost'],
                'sales': ['sales', 'attributed sales 7d', 'attributed sales 14d', 'attributed sales 30d'],
                'orders': ['orders', 'attributed orders 7d', 'attributed orders 14d', 'attributed orders 30d'],
                'units': ['units', 'attributed units 7d', 'attributed units 14d', 'attributed units 30d']
            }
            
            data = {}
            for field, possible_columns in column_mappings.items():
                value = None
                for col in possible_columns:
                    if col in row and row[col]:
                        value = row[col]
                        break
                
                if field == 'date':
                    data[field] = self._parse_date(value) if value else datetime.utcnow().date()
                elif field in ['keyword', 'match_type']:
                    data[field] = str(value) if value else ''
                else:
                    data[field] = self._parse_number(value)
            
            # Calculate derived metrics
            data['ctr'] = (data['clicks'] / data['impressions'] * 100) if data['impressions'] > 0 else 0
            data['cpc'] = (data['spend'] / data['clicks']) if data['clicks'] > 0 else 0
            data['acos'] = (data['spend'] / data['sales'] * 100) if data['sales'] > 0 else 0
            
            return data
            
        except Exception as e:
            print(f"Error extracting keyword data: {e}")
            return None
    
    def _extract_search_term_data(self, row: Dict) -> Optional[Dict]:
        """Extract search term data from CSV row"""
        try:
            column_mappings = {
                'search_term': ['search term', 'customer search term'],
                'keyword': ['keyword', 'targeting'],
                'match_type': ['match type', 'matchtype'],
                'impressions': ['impressions', 'impr'],
                'clicks': ['clicks', 'click'],
                'spend': ['spend', 'cost'],
                'sales': ['sales', 'attributed sales 7d', 'attributed sales 14d', 'attributed sales 30d'],
                'orders': ['orders', 'attributed orders 7d', 'attributed orders 14d', 'attributed orders 30d']
            }
            
            data = {}
            for field, possible_columns in column_mappings.items():
                value = None
                for col in possible_columns:
                    if col in row and row[col]:
                        value = row[col]
                        break
                
                if field in ['search_term', 'keyword', 'match_type']:
                    data[field] = str(value) if value else ''
                else:
                    data[field] = self._parse_number(value)
            
            return data
            
        except Exception as e:
            print(f"Error extracting search term data: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse date string in various formats"""
        if not date_str:
            return datetime.utcnow().date()
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%d-%m-%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # If no format matches, return current date
        return datetime.utcnow().date()
    
    def _parse_number(self, value: str) -> float:
        """Parse numeric value from string"""
        if not value or value.lower() in ['', 'n/a', 'null', 'none', '--']:
            return 0.0
        
        # Remove currency symbols, commas, and percentage signs
        cleaned = re.sub(r'[,$%]', '', str(value))
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def get_report_analytics(self, report_id: int) -> Dict:
        """Generate advanced analytics for a report"""
        try:
            # Get campaign data
            campaign_data = CampaignData.query.filter_by(report_id=report_id).all()
            
            if not campaign_data:
                return {'error': 'No campaign data found'}
            
            # Calculate analytics
            analytics = {
                'performance_summary': self._calculate_performance_summary(campaign_data),
                'campaign_analysis': self._analyze_campaigns(campaign_data),
                'trend_analysis': self._analyze_trends(campaign_data),
                'efficiency_metrics': self._calculate_efficiency_metrics(campaign_data),
                'recommendations': self._generate_recommendations(campaign_data)
            }
            
            return analytics
            
        except Exception as e:
            return {'error': f'Failed to generate analytics: {str(e)}'}
    
    def _calculate_performance_summary(self, campaign_data: List) -> Dict:
        """Calculate overall performance summary"""
        total_spend = sum(c.spend for c in campaign_data)
        total_sales = sum(c.sales for c in campaign_data)
        total_impressions = sum(c.impressions for c in campaign_data)
        total_clicks = sum(c.clicks for c in campaign_data)
        total_orders = sum(c.orders for c in campaign_data)
        
        return {
            'total_spend': total_spend,
            'total_sales': total_sales,
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_orders': total_orders,
            'overall_acos': (total_spend / total_sales * 100) if total_sales > 0 else 0,
            'overall_roas': (total_sales / total_spend) if total_spend > 0 else 0,
            'overall_ctr': (total_clicks / total_impressions * 100) if total_impressions > 0 else 0,
            'overall_cpc': (total_spend / total_clicks) if total_clicks > 0 else 0,
            'conversion_rate': (total_orders / total_clicks * 100) if total_clicks > 0 else 0
        }
    
    def _analyze_campaigns(self, campaign_data: List) -> Dict:
        """Analyze individual campaign performance"""
        campaigns = {}
        
        for data in campaign_data:
            campaign_id = data.amazon_campaign_id
            if campaign_id not in campaigns:
                campaigns[campaign_id] = {
                    'name': data.campaign_name,
                    'total_spend': 0,
                    'total_sales': 0,
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'total_orders': 0,
                    'days': 0
                }
            
            campaigns[campaign_id]['total_spend'] += data.spend
            campaigns[campaign_id]['total_sales'] += data.sales
            campaigns[campaign_id]['total_impressions'] += data.impressions
            campaigns[campaign_id]['total_clicks'] += data.clicks
            campaigns[campaign_id]['total_orders'] += data.orders
            campaigns[campaign_id]['days'] += 1
        
        # Calculate metrics for each campaign
        for campaign_id, campaign in campaigns.items():
            campaign['acos'] = (campaign['total_spend'] / campaign['total_sales'] * 100) if campaign['total_sales'] > 0 else 0
            campaign['roas'] = (campaign['total_sales'] / campaign['total_spend']) if campaign['total_spend'] > 0 else 0
            campaign['ctr'] = (campaign['total_clicks'] / campaign['total_impressions'] * 100) if campaign['total_impressions'] > 0 else 0
            campaign['cpc'] = (campaign['total_spend'] / campaign['total_clicks']) if campaign['total_clicks'] > 0 else 0
            campaign['conversion_rate'] = (campaign['total_orders'] / campaign['total_clicks'] * 100) if campaign['total_clicks'] > 0 else 0
        
        # Sort by performance
        top_performers = sorted(campaigns.items(), key=lambda x: x[1]['roas'], reverse=True)[:5]
        worst_performers = sorted(campaigns.items(), key=lambda x: x[1]['acos'], reverse=True)[:5]
        
        return {
            'total_campaigns': len(campaigns),
            'top_performers': top_performers,
            'worst_performers': worst_performers,
            'campaign_details': campaigns
        }
    
    def _analyze_trends(self, campaign_data: List) -> Dict:
        """Analyze performance trends over time"""
        daily_data = {}
        
        for data in campaign_data:
            date_str = data.date.isoformat()
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'spend': 0,
                    'sales': 0,
                    'impressions': 0,
                    'clicks': 0,
                    'orders': 0
                }
            
            daily_data[date_str]['spend'] += data.spend
            daily_data[date_str]['sales'] += data.sales
            daily_data[date_str]['impressions'] += data.impressions
            daily_data[date_str]['clicks'] += data.clicks
            daily_data[date_str]['orders'] += data.orders
        
        # Calculate daily metrics
        for date_str, data in daily_data.items():
            data['acos'] = (data['spend'] / data['sales'] * 100) if data['sales'] > 0 else 0
            data['roas'] = (data['sales'] / data['spend']) if data['spend'] > 0 else 0
            data['ctr'] = (data['clicks'] / data['impressions'] * 100) if data['impressions'] > 0 else 0
        
        return {
            'daily_performance': daily_data,
            'trend_direction': self._calculate_trend_direction(daily_data)
        }
    
    def _calculate_efficiency_metrics(self, campaign_data: List) -> Dict:
        """Calculate efficiency and optimization metrics"""
        # Group by campaign for efficiency analysis
        campaign_efficiency = {}
        
        for data in campaign_data:
            campaign_id = data.amazon_campaign_id
            if campaign_id not in campaign_efficiency:
                campaign_efficiency[campaign_id] = {
                    'name': data.campaign_name,
                    'efficiency_score': 0,
                    'optimization_potential': 0,
                    'waste_score': 0
                }
            
            # Calculate efficiency metrics (simplified)
            acos = data.acos if data.acos else 0
            roas = data.roas if data.roas else 0
            
            # Efficiency score based on ROAS and ACOS
            efficiency = (roas * 10) - (acos / 10) if roas > 0 else 0
            campaign_efficiency[campaign_id]['efficiency_score'] = max(efficiency, 0)
        
        return {
            'campaign_efficiency': campaign_efficiency,
            'overall_efficiency': sum(c['efficiency_score'] for c in campaign_efficiency.values()) / len(campaign_efficiency) if campaign_efficiency else 0
        }
    
    def _generate_recommendations(self, campaign_data: List) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Analyze for high ACOS campaigns
        high_acos_campaigns = [c for c in campaign_data if c.acos and c.acos > 50]
        if high_acos_campaigns:
            recommendations.append({
                'type': 'high_acos_alert',
                'priority': 'high',
                'title': 'High ACOS Campaigns Detected',
                'description': f'{len(high_acos_campaigns)} campaigns have ACOS above 50%. Consider reducing bids or pausing underperforming keywords.',
                'affected_campaigns': len(high_acos_campaigns)
            })
        
        # Analyze for low impression campaigns
        low_impression_campaigns = [c for c in campaign_data if c.impressions < 100]
        if low_impression_campaigns:
            recommendations.append({
                'type': 'low_impressions',
                'priority': 'medium',
                'title': 'Low Impression Campaigns',
                'description': f'{len(low_impression_campaigns)} campaigns have very low impressions. Consider increasing bids or expanding keyword targeting.',
                'affected_campaigns': len(low_impression_campaigns)
            })
        
        # Analyze for high performing campaigns
        high_roas_campaigns = [c for c in campaign_data if c.roas and c.roas > 3]
        if high_roas_campaigns:
            recommendations.append({
                'type': 'scale_opportunity',
                'priority': 'high',
                'title': 'Scaling Opportunity',
                'description': f'{len(high_roas_campaigns)} campaigns have excellent ROAS (>3x). Consider increasing budgets to scale these winners.',
                'affected_campaigns': len(high_roas_campaigns)
            })
        
        return recommendations
    
    def _calculate_trend_direction(self, daily_data: Dict) -> str:
        """Calculate overall trend direction"""
        if len(daily_data) < 2:
            return 'insufficient_data'
        
        dates = sorted(daily_data.keys())
        recent_acos = daily_data[dates[-1]]['acos']
        older_acos = daily_data[dates[0]]['acos']
        
        if recent_acos < older_acos * 0.9:
            return 'improving'
        elif recent_acos > older_acos * 1.1:
            return 'declining'
        else:
            return 'stable'

