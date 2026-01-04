"""
Analytics System for InstaSpotter
Provides detailed analytics and insights
"""

from .manager import AnalyticsManager
from .models import AnalyticsData, ChartData, MetricData

__all__ = ["AnalyticsManager", "AnalyticsData", "ChartData", "MetricData"]
