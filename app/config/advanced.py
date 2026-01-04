"""
Advanced Configuration for InstaSpotter
High-level settings and feature toggles
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import time

class AdvancedSettings(BaseModel):
    """Advanced configuration settings"""
    
    # Feature Flags
    features: Dict[str, bool] = {
        "ai_moderation": True,
        "auto_posting": True,
        "analytics": True,
        "notifications": True,
        "bulk_operations": True,
        "export_data": True,
        "real_time_updates": True,
        "advanced_search": True,
        "content_preview": True,
        "media_management": True,
        "user_management": False,
        "api_access": True,
        "webhook_integration": False,
        "slack_integration": False,
        "email_notifications": False,
        "backup_automation": True,
        "performance_monitoring": True,
        "security_scanning": True,
        "rate_limiting": True,
        "caching": True
    }
    
    # UI/UX Settings
    ui: Dict[str, Any] = {
        "theme": "dark",
        "color_scheme": "blue",
        "animations": True,
        "auto_refresh": True,
        "refresh_interval": 30,  # seconds
        "items_per_page": 10,
        "show_advanced_options": True,
        "compact_mode": False,
        "sidebar_collapsed": False,
        "notifications_enabled": True,
        "sound_effects": False
    }
    
    # Performance Settings
    performance: Dict[str, Any] = {
        "cache_ttl": 300,  # seconds
        "max_concurrent_requests": 100,
        "database_pool_size": 20,
        "max_memory_usage": 80,  # percentage
        "enable_compression": True,
        "optimize_images": True,
        "lazy_loading": True,
        "preload_critical_data": True,
        "background_processing": True,
        "async_operations": True
    }
    
    # Security Settings
    security: Dict[str, Any] = {
        "session_timeout": 3600,  # seconds
        "max_login_attempts": 5,
        "password_min_length": 8,
        "require_2fa": False,
        "ip_whitelist": [],
        "rate_limit_per_minute": 100,
        "enable_csrf_protection": True,
        "secure_cookies": True,
        "content_security_policy": True,
        "audit_logging": True
    }
    
    # Content Settings
    content: Dict[str, Any] = {
        "max_message_length": 500,
        "min_message_length": 10,
        "allowed_file_types": ["jpg", "jpeg", "png", "gif"],
        "max_file_size": 10485760,  # 10MB
        "auto_resize_images": True,
        "image_quality": "high",
        "watermark_enabled": False,
        "content_filtering": True,
        "profanity_filter": True,
        "spam_detection": True
    }
    
    # AI Settings
    ai: Dict[str, Any] = {
        "moderation_enabled": True,
        "confidence_threshold": 0.7,
        "auto_approve_threshold": 0.9,
        "auto_reject_threshold": 0.3,
        "learning_enabled": True,
        "feedback_loop": True,
        "custom_rules": [],
        "language_detection": True,
        "sentiment_analysis": True,
        "content_classification": True
    }
    
    # Social Media Settings
    social: Dict[str, Any] = {
        "instagram_api_version": "v1",
        "story_duration": 24,  # hours
        "auto_delete_after_posting": False,
        "posting_schedule": "20:00",  # 8 PM
        "batch_posting": True,
        "engagement_tracking": True,
        "hashtag_auto_add": True,
        "location_tagging": False,
        "mention_handling": True
    }
    
    # Analytics Settings
    analytics: Dict[str, Any] = {
        "track_user_behavior": True,
        "track_performance_metrics": True,
        "track_content_metrics": True,
        "track_engagement_metrics": True,
        "data_retention_days": 365,
        "privacy_mode": False,
        "anonymize_data": True,
        "export_formats": ["csv", "json", "xlsx"],
        "real_time_dashboard": True,
        "custom_reports": True
    }
    
    # Notification Settings
    notifications: Dict[str, Any] = {
        "email_enabled": False,
        "slack_enabled": False,
        "webhook_enabled": False,
        "browser_notifications": True,
        "sound_notifications": False,
        "notification_types": [
            "new_message",
            "moderation_complete",
            "posting_success",
            "posting_failed",
            "system_alert",
            "maintenance"
        ],
        "notification_channels": ["dashboard", "email", "slack"],
        "quiet_hours": {"start": "22:00", "end": "08:00"}
    }
    
    # Backup Settings
    backup: Dict[str, Any] = {
        "enabled": True,
        "frequency": "daily",
        "retention_days": 30,
        "compression": True,
        "encryption": True,
        "cloud_storage": False,
        "local_storage": True,
        "auto_cleanup": True,
        "backup_database": True,
        "backup_media": True,
        "backup_config": True
    }
    
    # Monitoring Settings
    monitoring: Dict[str, Any] = {
        "health_checks": True,
        "performance_monitoring": True,
        "error_tracking": True,
        "uptime_monitoring": True,
        "resource_monitoring": True,
        "alert_thresholds": {
            "cpu_usage": 80,
            "memory_usage": 85,
            "disk_usage": 90,
            "error_rate": 5,
            "response_time": 2000
        },
        "log_level": "INFO",
        "log_retention_days": 30,
        "metrics_collection": True
    }

# Global advanced settings instance
advanced_settings = AdvancedSettings()

def get_advanced_settings() -> AdvancedSettings:
    """Get current advanced settings"""
    return advanced_settings

def update_advanced_settings(settings_dict: Dict[str, Any]) -> AdvancedSettings:
    """Update advanced settings"""
    global advanced_settings
    advanced_settings = AdvancedSettings(**settings_dict)
    return advanced_settings

def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled"""
    return advanced_settings.features.get(feature, False)

def get_ui_setting(key: str, default: Any = None) -> Any:
    """Get a UI setting value"""
    return advanced_settings.ui.get(key, default)

def get_performance_setting(key: str, default: Any = None) -> Any:
    """Get a performance setting value"""
    return advanced_settings.performance.get(key, default)

def get_security_setting(key: str, default: Any = None) -> Any:
    """Get a security setting value"""
    return advanced_settings.security.get(key, default)

def get_content_setting(key: str, default: Any = None) -> Any:
    """Get a content setting value"""
    return advanced_settings.content.get(key, default)

def get_ai_setting(key: str, default: Any = None) -> Any:
    """Get an AI setting value"""
    return advanced_settings.ai.get(key, default)

def get_social_setting(key: str, default: Any = None) -> Any:
    """Get a social media setting value"""
    return advanced_settings.social.get(key, default)

def get_analytics_setting(key: str, default: Any = None) -> Any:
    """Get an analytics setting value"""
    return advanced_settings.analytics.get(key, default)

def get_notification_setting(key: str, default: Any = None) -> Any:
    """Get a notification setting value"""
    return advanced_settings.notifications.get(key, default)

def get_backup_setting(key: str, default: Any = None) -> Any:
    """Get a backup setting value"""
    return advanced_settings.backup.get(key, default)

def get_monitoring_setting(key: str, default: Any = None) -> Any:
    """Get a monitoring setting value"""
    return advanced_settings.monitoring.get(key, default)
