"""
Analytics data models
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel
from enum import Enum

class MetricType(Enum):
    """Types of metrics"""
    COUNT = "count"
    PERCENTAGE = "percentage"
    RATE = "rate"
    TREND = "trend"
    DISTRIBUTION = "distribution"

class TimeRange(Enum):
    """Time range options"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class ChartType(Enum):
    """Chart types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"

class MetricData(BaseModel):
    """Individual metric data"""
    name: str
    value: float
    metric_type: MetricType
    unit: Optional[str] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    color: Optional[str] = None

class ChartData(BaseModel):
    """Chart data structure"""
    title: str
    chart_type: ChartType
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None

class AnalyticsData(BaseModel):
    """Complete analytics data"""
    timestamp: datetime
    time_range: TimeRange
    metrics: List[MetricData]
    charts: List[ChartData]
    summary: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ContentAnalytics(BaseModel):
    """Content-specific analytics"""
    total_messages: int
    pending_messages: int
    approved_messages: int
    rejected_messages: int
    posted_messages: int
    failed_messages: int
    
    # AI Analysis stats
    ai_analyzed_count: int
    ai_approval_rate: float
    ai_rejection_rate: float
    
    # Content stats
    avg_message_length: float
    most_common_words: List[Dict[str, Any]]
    content_categories: Dict[str, int]
    
    # Performance stats
    avg_processing_time: float
    success_rate: float
    error_rate: float

class UserEngagement(BaseModel):
    """User engagement analytics"""
    total_submissions: int
    daily_submissions: int
    weekly_submissions: int
    monthly_submissions: int
    
    # Peak times
    peak_hour: int
    peak_day: str
    submission_patterns: Dict[str, int]
    
    # Geographic data (if available)
    top_locations: List[Dict[str, Any]]
    timezone_distribution: Dict[str, int]

class SystemPerformance(BaseModel):
    """System performance metrics"""
    uptime_percentage: float
    avg_response_time: float
    error_count: int
    success_count: int
    
    # Resource usage
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    
    # Database performance
    db_query_time: float
    db_connections: int
    cache_hit_rate: float

class ModerationAnalytics(BaseModel):
    """Moderation analytics"""
    total_moderated: int
    auto_approved: int
    auto_rejected: int
    manual_reviewed: int
    
    # AI Performance
    ai_accuracy: float
    false_positives: int
    false_negatives: int
    
    # Moderation patterns
    common_rejection_reasons: List[Dict[str, Any]]
    moderation_trends: Dict[str, Any]
    
    # Response times
    avg_moderation_time: float
    peak_moderation_load: int
