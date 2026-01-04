"""
Enterprise Configuration for InstaSpotter
Advanced settings and features for enterprise-level deployment
"""

from datetime import time
from typing import Dict, List, Optional
from pydantic import BaseModel

class EnterpriseSettings(BaseModel):
    """Enterprise-level configuration settings"""
    
    # Daily Posting Schedule
    daily_posting_time: time = time(20, 0)  # 8:00 PM
    daily_posting_enabled: bool = True
    
    # Content Management
    max_messages_per_day: int = 50
    auto_approve_threshold: float = 0.8  # AI confidence threshold for auto-approval
    content_moderation_enabled: bool = True
    
    # Analytics and Reporting
    analytics_enabled: bool = True
    detailed_logging: bool = True
    performance_monitoring: bool = True
    
    # Security Features
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    ip_whitelist: List[str] = []
    session_timeout_minutes: int = 60
    
    # Notification Settings
    email_notifications: bool = True
    slack_integration: bool = False
    webhook_urls: List[str] = []
    
    # Backup and Recovery
    auto_backup_enabled: bool = True
    backup_interval_hours: int = 6
    backup_retention_days: int = 30
    
    # Performance Optimization
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    database_pool_size: int = 20
    max_connections: int = 100
    
    # Content Generation
    image_quality: str = "high"  # low, medium, high, ultra
    custom_templates: List[str] = []
    brand_colors: Dict[str, str] = {
        "primary": "#00aaff",
        "secondary": "#0066cc",
        "accent": "#00ccff"
    }
    
    # AI Moderation
    ai_moderation_enabled: bool = True
    ai_confidence_threshold: float = 0.7
    custom_moderation_rules: List[str] = []
    
    # Social Media Integration
    instagram_api_version: str = "v1"
    story_duration_hours: int = 24
    auto_delete_after_posting: bool = False
    
    # Monitoring and Alerts
    health_check_interval: int = 30  # seconds
    alert_on_failures: bool = True
    alert_email: Optional[str] = None
    
    # Advanced Features
    bulk_operations_enabled: bool = True
    export_formats: List[str] = ["csv", "json", "xlsx"]
    api_rate_limits: Dict[str, int] = {
        "messages": 1000,
        "admin": 500,
        "analytics": 200
    }

# Global enterprise settings instance
enterprise_settings = EnterpriseSettings()

def get_enterprise_settings() -> EnterpriseSettings:
    """Get current enterprise settings"""
    return enterprise_settings

def update_enterprise_settings(settings_dict: Dict) -> EnterpriseSettings:
    """Update enterprise settings"""
    global enterprise_settings
    enterprise_settings = EnterpriseSettings(**settings_dict)
    return enterprise_settings

def is_enterprise_feature_enabled(feature: str) -> bool:
    """Check if an enterprise feature is enabled"""
    return getattr(enterprise_settings, feature, False)

def get_daily_posting_schedule() -> time:
    """Get the daily posting time"""
    return enterprise_settings.daily_posting_time

def get_brand_colors() -> Dict[str, str]:
    """Get brand colors for theming"""
    return enterprise_settings.brand_colors

def get_performance_limits() -> Dict[str, int]:
    """Get performance and rate limiting settings"""
    return {
        "max_messages_per_day": enterprise_settings.max_messages_per_day,
        "max_requests_per_minute": enterprise_settings.max_requests_per_minute,
        "database_pool_size": enterprise_settings.database_pool_size,
        "max_connections": enterprise_settings.max_connections
    }
