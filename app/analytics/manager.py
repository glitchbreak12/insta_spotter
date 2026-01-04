"""
Analytics Manager
Handles analytics data collection and processing
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.database import SpottedMessage, MessageStatus
from .models import (
    AnalyticsData, ChartData, MetricData, ContentAnalytics, 
    UserEngagement, SystemPerformance, ModerationAnalytics,
    MetricType, ChartType, TimeRange
)

class AnalyticsManager:
    """Manages analytics data collection and processing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_content_analytics(self, days: int = 30) -> ContentAnalytics:
        """Get content analytics for the specified period"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Basic counts
        total_messages = self.db.query(SpottedMessage).filter(
            SpottedMessage.created_at >= start_date
        ).count()
        
        pending_messages = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.status == MessageStatus.PENDING
            )
        ).count()
        
        approved_messages = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.status == MessageStatus.APPROVED
            )
        ).count()
        
        rejected_messages = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.status == MessageStatus.REJECTED
            )
        ).count()
        
        posted_messages = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.status == MessageStatus.POSTED
            )
        ).count()
        
        failed_messages = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.status == MessageStatus.FAILED
            )
        ).count()
        
        # AI Analysis stats
        ai_analyzed_count = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.gemini_analysis.isnot(None)
            )
        ).count()
        
        ai_approval_rate = (approved_messages / ai_analyzed_count * 100) if ai_analyzed_count > 0 else 0
        ai_rejection_rate = (rejected_messages / ai_analyzed_count * 100) if ai_analyzed_count > 0 else 0
        
        # Content stats
        messages_with_text = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.text.isnot(None)
            )
        ).all()
        
        avg_message_length = sum(len(msg.text) for msg in messages_with_text) / len(messages_with_text) if messages_with_text else 0
        
        # Most common words (simplified)
        all_text = " ".join(msg.text for msg in messages_with_text)
        words = all_text.lower().split()
        word_count = {}
        for word in words:
            if len(word) > 3:  # Filter short words
                word_count[word] = word_count.get(word, 0) + 1
        
        most_common_words = [
            {"word": word, "count": count} 
            for word, count in sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Performance stats (simplified)
        success_rate = (posted_messages / total_messages * 100) if total_messages > 0 else 0
        error_rate = (failed_messages / total_messages * 100) if total_messages > 0 else 0
        
        return ContentAnalytics(
            total_messages=total_messages,
            pending_messages=pending_messages,
            approved_messages=approved_messages,
            rejected_messages=rejected_messages,
            posted_messages=posted_messages,
            failed_messages=failed_messages,
            ai_analyzed_count=ai_analyzed_count,
            ai_approval_rate=ai_approval_rate,
            ai_rejection_rate=ai_rejection_rate,
            avg_message_length=avg_message_length,
            most_common_words=most_common_words,
            content_categories={},  # Could be implemented with content classification
            avg_processing_time=0.0,  # Would need to track processing times
            success_rate=success_rate,
            error_rate=error_rate
        )
    
    def get_user_engagement(self, days: int = 30) -> UserEngagement:
        """Get user engagement analytics"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Submission counts
        total_submissions = self.db.query(SpottedMessage).filter(
            SpottedMessage.created_at >= start_date
        ).count()
        
        daily_submissions = self.db.query(SpottedMessage).filter(
            SpottedMessage.created_at >= start_date - timedelta(days=1)
        ).count()
        
        weekly_submissions = self.db.query(SpottedMessage).filter(
            SpottedMessage.created_at >= start_date - timedelta(days=7)
        ).count()
        
        monthly_submissions = self.db.query(SpottedMessage).filter(
            SpottedMessage.created_at >= start_date - timedelta(days=30)
        ).count()
        
        # Peak times analysis
        messages = self.db.query(SpottedMessage).filter(
            SpottedMessage.created_at >= start_date
        ).all()
        
        hour_counts = {}
        day_counts = {}
        
        for msg in messages:
            hour = msg.created_at.hour
            day = msg.created_at.strftime('%A')
            
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
            day_counts[day] = day_counts.get(day, 0) + 1
        
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 0
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else "Monday"
        
        return UserEngagement(
            total_submissions=total_submissions,
            daily_submissions=daily_submissions,
            weekly_submissions=weekly_submissions,
            monthly_submissions=monthly_submissions,
            peak_hour=peak_hour,
            peak_day=peak_day,
            submission_patterns=hour_counts,
            top_locations=[],  # Would need location data
            timezone_distribution={}  # Would need timezone data
        )
    
    def get_moderation_analytics(self, days: int = 30) -> ModerationAnalytics:
        """Get moderation analytics"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Basic moderation counts
        total_moderated = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.gemini_analysis.isnot(None)
            )
        ).count()
        
        auto_approved = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.status == MessageStatus.APPROVED,
                SpottedMessage.gemini_analysis.isnot(None)
            )
        ).count()
        
        auto_rejected = self.db.query(SpottedMessage).filter(
            and_(
                SpottedMessage.created_at >= start_date,
                SpottedMessage.status == MessageStatus.REJECTED,
                SpottedMessage.gemini_analysis.isnot(None)
            )
        ).count()
        
        manual_reviewed = total_moderated - auto_approved - auto_rejected
        
        # AI Performance (simplified)
        ai_accuracy = (auto_approved + auto_rejected) / total_moderated * 100 if total_moderated > 0 else 0
        
        return ModerationAnalytics(
            total_moderated=total_moderated,
            auto_approved=auto_approved,
            auto_rejected=auto_rejected,
            manual_reviewed=manual_reviewed,
            ai_accuracy=ai_accuracy,
            false_positives=0,  # Would need to track corrections
            false_negatives=0,  # Would need to track corrections
            common_rejection_reasons=[],  # Would need to analyze rejection reasons
            moderation_trends={},  # Would need trend analysis
            avg_moderation_time=0.0,  # Would need to track processing times
            peak_moderation_load=0  # Would need to track load
        )
    
    def get_dashboard_metrics(self, days: int = 30) -> List[MetricData]:
        """Get key metrics for dashboard"""
        content_analytics = self.get_content_analytics(days)
        user_engagement = self.get_user_engagement(days)
        moderation_analytics = self.get_moderation_analytics(days)
        
        metrics = [
            MetricData(
                name="Total Messages",
                value=content_analytics.total_messages,
                metric_type=MetricType.COUNT,
                color="#00aaff"
            ),
            MetricData(
                name="Success Rate",
                value=content_analytics.success_rate,
                metric_type=MetricType.PERCENTAGE,
                unit="%",
                color="#10b981"
            ),
            MetricData(
                name="AI Analyzed",
                value=content_analytics.ai_analyzed_count,
                metric_type=MetricType.COUNT,
                color="#8b5cf6"
            ),
            MetricData(
                name="Daily Submissions",
                value=user_engagement.daily_submissions,
                metric_type=MetricType.COUNT,
                color="#f59e0b"
            ),
            MetricData(
                name="AI Accuracy",
                value=moderation_analytics.ai_accuracy,
                metric_type=MetricType.PERCENTAGE,
                unit="%",
                color="#06b6d4"
            )
        ]
        
        return metrics
    
    def get_chart_data(self, chart_type: str, days: int = 30) -> ChartData:
        """Get chart data for specific chart type"""
        if chart_type == "activity":
            return self._get_activity_chart(days)
        elif chart_type == "moderation":
            return self._get_moderation_chart(days)
        elif chart_type == "distribution":
            return self._get_distribution_chart(days)
        else:
            return self._get_activity_chart(days)
    
    def _get_activity_chart(self, days: int) -> ChartData:
        """Get activity chart data"""
        # Get daily message counts for the last N days
        labels = []
        data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = self.db.query(SpottedMessage).filter(
                and_(
                    SpottedMessage.created_at >= day_start,
                    SpottedMessage.created_at < day_end
                )
            ).count()
            
            labels.insert(0, day_start.strftime('%m/%d'))
            data.insert(0, count)
        
        return ChartData(
            title="Daily Activity",
            chart_type=ChartType.LINE,
            labels=labels,
            datasets=[{
                "label": "Messages",
                "data": data,
                "borderColor": "#00aaff",
                "backgroundColor": "rgba(0, 170, 255, 0.1)",
                "fill": True
            }]
        )
    
    def _get_moderation_chart(self, days: int) -> ChartData:
        """Get moderation chart data"""
        content_analytics = self.get_content_analytics(days)
        
        return ChartData(
            title="Moderation Distribution",
            chart_type=ChartType.DOUGHNUT,
            labels=["Approved", "Rejected", "Pending", "Failed"],
            datasets=[{
                "data": [
                    content_analytics.approved_messages,
                    content_analytics.rejected_messages,
                    content_analytics.pending_messages,
                    content_analytics.failed_messages
                ],
                "backgroundColor": [
                    "#10b981",
                    "#ef4444",
                    "#f59e0b",
                    "#6b7280"
                ]
            }]
        )
    
    def _get_distribution_chart(self, days: int) -> ChartData:
        """Get content distribution chart data"""
        # Get hourly distribution for the last N days
        labels = [f"{i:02d}:00" for i in range(24)]
        data = [0] * 24
        
        start_date = datetime.now() - timedelta(days=days)
        messages = self.db.query(SpottedMessage).filter(
            SpottedMessage.created_at >= start_date
        ).all()
        
        for msg in messages:
            hour = msg.created_at.hour
            data[hour] += 1
        
        return ChartData(
            title="Hourly Distribution",
            chart_type=ChartType.BAR,
            labels=labels,
            datasets=[{
                "label": "Messages",
                "data": data,
                "backgroundColor": "#00aaff",
                "borderColor": "#0066cc"
            }]
        )
    
    def get_comprehensive_analytics(self, days: int = 30) -> AnalyticsData:
        """Get comprehensive analytics data"""
        metrics = self.get_dashboard_metrics(days)
        charts = [
            self.get_chart_data("activity", days),
            self.get_chart_data("moderation", days),
            self.get_chart_data("distribution", days)
        ]
        
        content_analytics = self.get_content_analytics(days)
        user_engagement = self.get_user_engagement(days)
        moderation_analytics = self.get_moderation_analytics(days)
        
        summary = {
            "content": content_analytics.dict(),
            "engagement": user_engagement.dict(),
            "moderation": moderation_analytics.dict()
        }
        
        return AnalyticsData(
            timestamp=datetime.now(),
            time_range=TimeRange.DAY,
            metrics=metrics,
            charts=charts,
            summary=summary
        )
