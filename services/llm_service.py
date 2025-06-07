import os
import json
import requests
from typing import Dict, List, Optional

class LLMService:
    """Service for AI-powered analysis using OpenRouter API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/llama-3.1-8b-instruct:free"):
        """
        Initialize LLM service with OpenRouter API
        
        Args:
            api_key: OpenRouter API key (if None, uses environment variable)
            model: Model to use (defaults to free Llama model)
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
    def _make_request(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Make request to OpenRouter API"""
        if not self.api_key:
            # Return mock response if no API key provided
            return self._get_mock_response(messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kdp-advertising-tool.com",
            "X-Title": "KDP Advertising Tool"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"OpenRouter API error: {e}")
            return self._get_mock_response(messages)
    
    def _get_mock_response(self, messages: List[Dict]) -> str:
        """Generate mock response when API is not available"""
        last_message = messages[-1]['content'].lower()
        
        if 'campaign performance' in last_message or 'analyze' in last_message:
            return json.dumps({
                "insights": [
                    "Your advertising campaigns show mixed performance with opportunities for optimization",
                    "High ACOS campaigns need immediate attention to reduce wasted spend",
                    "Consider reallocating budget from underperforming to high-converting campaigns",
                    "Keyword targeting could be refined to improve click-through rates"
                ],
                "recommendations": [
                    "Reduce bids on campaigns with ACOS above 40%",
                    "Increase budget for campaigns with ACOS below 25%",
                    "Add negative keywords to improve targeting efficiency",
                    "Test new keyword variations for top-performing campaigns"
                ],
                "priority_actions": [
                    "Review and optimize high-spend, low-performance campaigns",
                    "Scale successful campaigns with good ROAS",
                    "Implement negative keyword strategy"
                ]
            })
        
        elif 'keyword' in last_message:
            return json.dumps({
                "negative_keywords": ["free", "cheap", "used", "download", "pdf"],
                "expansion_opportunities": [
                    "Add long-tail keywords related to your book's specific topic",
                    "Include problem-solving keywords your book addresses",
                    "Consider seasonal or trending keywords in your genre"
                ],
                "bid_suggestions": "Focus on exact match keywords with proven conversion rates"
            })
        
        else:
            return json.dumps({
                "analysis": "Campaign analysis completed successfully",
                "insights": ["Performance metrics indicate room for optimization"],
                "recommendations": ["Consider adjusting bids and targeting"]
            })
    
    def analyze_campaign_performance(self, campaign_data: Dict) -> Dict:
        """Analyze campaign performance and provide insights"""
        
        prompt = f"""
        Analyze this Amazon KDP advertising campaign performance data and provide actionable insights:
        
        Campaign Metrics:
        - Total Spend: ${campaign_data.get('total_spend', 0):.2f}
        - Total Sales: ${campaign_data.get('total_sales', 0):.2f}
        - ACOS: {campaign_data.get('acos', 0):.1f}%
        - Total Impressions: {campaign_data.get('total_impressions', 0):,}
        - Total Clicks: {campaign_data.get('total_clicks', 0):,}
        - CTR: {campaign_data.get('ctr', 0):.2f}%
        - Number of Campaigns: {campaign_data.get('campaigns_count', 0)}
        
        Please provide:
        1. Key insights about performance
        2. Specific recommendations for improvement
        3. Priority actions to take
        
        Focus on practical, actionable advice for KDP self-publishers. Return response as JSON with 'insights', 'recommendations', and 'priority_actions' arrays.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert Amazon KDP advertising consultant. Provide clear, actionable advice for self-publishers to optimize their advertising campaigns."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._make_request(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # If response is not valid JSON, wrap it
            return {
                "insights": [response],
                "recommendations": ["Review campaign performance and adjust bids accordingly"],
                "priority_actions": ["Optimize high-spend campaigns"]
            }
    
    def analyze_competitive_landscape(self, campaign_data: Dict) -> Dict:
        """Analyze competitive landscape and market positioning"""
        
        prompt = f"""
        Based on this KDP advertising performance data, analyze the competitive landscape:
        
        Performance Data:
        - Total Spend: ${campaign_data.get('total_spend', 0):.2f}
        - Total Sales: ${campaign_data.get('total_sales', 0):.2f}
        - Average ACOS: {campaign_data.get('avg_acos', 0):.1f}%
        - Number of Campaigns: {campaign_data.get('campaigns_count', 0)}
        
        Provide insights on:
        1. Market competitiveness indicators
        2. Positioning recommendations
        3. Competitive advantages to leverage
        
        Return as JSON with 'market_analysis', 'positioning_advice', and 'competitive_strategy' arrays.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert in Amazon marketplace competition analysis for book publishers."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._make_request(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "market_analysis": [response],
                "positioning_advice": ["Focus on unique value proposition"],
                "competitive_strategy": ["Differentiate through targeted keywords"]
            }
    
    def generate_keyword_recommendations(self, keyword_data: List[Dict]) -> Dict:
        """Generate keyword optimization recommendations"""
        
        # Prepare keyword performance summary
        total_spend = sum(kw.get('spend', 0) for kw in keyword_data)
        total_sales = sum(kw.get('sales', 0) for kw in keyword_data)
        
        prompt = f"""
        Analyze these keyword performance metrics for Amazon KDP advertising:
        
        Keyword Performance Summary:
        - Total Keywords: {len(keyword_data)}
        - Total Spend: ${total_spend:.2f}
        - Total Sales: ${total_sales:.2f}
        - Average ACOS: {(total_spend/total_sales*100) if total_sales > 0 else 0:.1f}%
        
        Top Keywords by Spend:
        {json.dumps(keyword_data[:5], indent=2)}
        
        Provide:
        1. Keyword optimization recommendations
        2. Negative keyword suggestions
        3. New keyword expansion ideas
        
        Return as JSON with 'optimization_tips', 'negative_keywords', and 'expansion_ideas' arrays.
        """
        
        messages = [
            {"role": "system", "content": "You are a keyword optimization expert for Amazon book advertising."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._make_request(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "optimization_tips": [response],
                "negative_keywords": ["free", "cheap", "used"],
                "expansion_ideas": ["Add long-tail keywords", "Include genre-specific terms"]
            }
    
    def generate_optimization_recommendations(self, report_data: Dict) -> Dict:
        """Generate comprehensive optimization recommendations"""
        
        prompt = f"""
        Create comprehensive optimization recommendations for this Amazon KDP advertising report:
        
        Report Summary:
        - Total Spend: ${report_data.get('total_spend', 0):.2f}
        - Total Sales: ${report_data.get('total_sales', 0):.2f}
        - ACOS: {report_data.get('acos', 0):.1f}%
        - Campaigns: {report_data.get('campaigns', 0)}
        - Date Range: {report_data.get('date_range', 'Unknown')}
        
        Provide detailed recommendations in these categories:
        1. Bid adjustments
        2. Budget reallocation
        3. Keyword optimization
        4. Campaign structure improvements
        5. Performance monitoring
        
        Return as JSON with arrays for each category.
        """
        
        messages = [
            {"role": "system", "content": "You are a comprehensive Amazon advertising optimization expert specializing in book marketing."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._make_request(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "bid_adjustments": [response],
                "budget_reallocation": ["Reallocate from low to high performers"],
                "keyword_optimization": ["Add negative keywords"],
                "campaign_improvements": ["Optimize campaign structure"],
                "monitoring": ["Track performance weekly"]
            }

# Available free models on OpenRouter
FREE_MODELS = {
    "meta-llama/llama-3.1-8b-instruct:free": "Llama 3.1 8B (Free)",
    "microsoft/phi-3-mini-128k-instruct:free": "Phi-3 Mini (Free)",
    "google/gemma-2-9b-it:free": "Gemma 2 9B (Free)",
    "qwen/qwen-2-7b-instruct:free": "Qwen2 7B (Free)",
    "huggingfaceh4/zephyr-7b-beta:free": "Zephyr 7B (Free)"
}

# Recommended paid models for better performance
PREMIUM_MODELS = {
    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
    "openai/gpt-4o": "GPT-4o",
    "google/gemini-pro-1.5": "Gemini Pro 1.5",
    "meta-llama/llama-3.1-70b-instruct": "Llama 3.1 70B"
}

