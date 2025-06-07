from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255))
    subscription_tier = db.Column(db.String(50), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # API Keys for user's own services
    openrouter_api_key = db.Column(db.String(255))  # Encrypted storage
    preferred_model = db.Column(db.String(100), default='meta-llama/llama-3.1-8b-instruct:free')
    
    # User preferences
    timezone = db.Column(db.String(50), default='UTC')
    email_notifications = db.Column(db.Boolean, default=True)
    
    # Relationships
    reports = db.relationship('Report', backref='user', lazy=True, cascade='all, delete-orphan')
    campaigns = db.relationship('Campaign', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'subscription_tier': self.subscription_tier,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferred_model': self.preferred_model,
            'timezone': self.timezone,
            'email_notifications': self.email_notifications,
            'has_openrouter_key': bool(self.openrouter_api_key)
        }

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'sponsored_products', 'sponsored_brands', etc.
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processing_status = db.Column(db.String(50), default='pending')  # 'pending', 'processing', 'completed', 'error'
    error_message = db.Column(db.Text)
    
    # Report metadata
    date_range_start = db.Column(db.Date)
    date_range_end = db.Column(db.Date)
    total_spend = db.Column(db.Float)
    total_sales = db.Column(db.Float)
    acos = db.Column(db.Float)
    total_impressions = db.Column(db.Integer)
    total_clicks = db.Column(db.Integer)
    
    # Relationships
    campaign_data = db.relationship('CampaignData', backref='report', lazy=True, cascade='all, delete-orphan')

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amazon_campaign_id = db.Column(db.String(100), nullable=False)
    campaign_name = db.Column(db.String(255), nullable=False)
    campaign_type = db.Column(db.String(50), nullable=False)  # 'sponsored_products', 'sponsored_brands', etc.
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campaign settings
    daily_budget = db.Column(db.Float)
    targeting_type = db.Column(db.String(50))  # 'manual', 'automatic'
    
    # Relationships
    campaign_data = db.relationship('CampaignData', backref='campaign', lazy=True)
    keywords = db.relationship('Keyword', backref='campaign', lazy=True, cascade='all, delete-orphan')

class CampaignData(db.Model):
    __tablename__ = 'campaign_data'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    
    # Campaign identifiers
    amazon_campaign_id = db.Column(db.String(100), nullable=False)
    campaign_name = db.Column(db.String(255), nullable=False)
    
    # Performance metrics
    date = db.Column(db.Date, nullable=False)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    ctr = db.Column(db.Float, default=0)  # Click-through rate
    cpc = db.Column(db.Float, default=0)  # Cost per click
    spend = db.Column(db.Float, default=0)
    sales = db.Column(db.Float, default=0)
    acos = db.Column(db.Float, default=0)  # Advertising cost of sales
    roas = db.Column(db.Float, default=0)  # Return on ad spend
    orders = db.Column(db.Integer, default=0)
    units = db.Column(db.Integer, default=0)
    conversion_rate = db.Column(db.Float, default=0)

class Keyword(db.Model):
    __tablename__ = 'keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    keyword_text = db.Column(db.String(255), nullable=False)
    match_type = db.Column(db.String(20), nullable=False)  # 'exact', 'phrase', 'broad'
    bid = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')
    
    # Performance data (latest)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    spend = db.Column(db.Float, default=0)
    sales = db.Column(db.Float, default=0)
    acos = db.Column(db.Float, default=0)
    
    # Relationships
    keyword_data = db.relationship('KeywordData', backref='keyword', lazy=True, cascade='all, delete-orphan')

class KeywordData(db.Model):
    __tablename__ = 'keyword_data'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    
    # Performance metrics
    date = db.Column(db.Date, nullable=False)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    ctr = db.Column(db.Float, default=0)
    cpc = db.Column(db.Float, default=0)
    spend = db.Column(db.Float, default=0)
    sales = db.Column(db.Float, default=0)
    acos = db.Column(db.Float, default=0)
    orders = db.Column(db.Integer, default=0)
    units = db.Column(db.Integer, default=0)

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'))
    
    # Recommendation details
    type = db.Column(db.String(50), nullable=False)  # 'keyword_bid', 'budget_adjustment', 'negative_keyword', etc.
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # 'high', 'medium', 'low'
    expected_impact = db.Column(db.String(100))
    
    # Implementation details
    target_entity_type = db.Column(db.String(50))  # 'campaign', 'keyword', 'ad_group'
    target_entity_id = db.Column(db.String(100))
    recommended_action = db.Column(db.JSON)  # Store action details as JSON
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # 'pending', 'implemented', 'dismissed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    implemented_at = db.Column(db.DateTime)
    
    # AI-generated content
    ai_reasoning = db.Column(db.Text)  # LLM explanation of the recommendation

class AnalysisSession(db.Model):
    __tablename__ = 'analysis_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    
    # Session details
    analysis_type = db.Column(db.String(50), nullable=False)  # 'performance', 'optimization', 'competitive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='in_progress')
    
    # Analysis results
    results = db.Column(db.JSON)  # Store analysis results as JSON
    ai_summary = db.Column(db.Text)  # LLM-generated summary
    
    # Relationships
    user = db.relationship('User', backref='analysis_sessions')
    report = db.relationship('Report', backref='analysis_sessions')

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Relationships
    user = db.relationship('User', backref='sessions')

