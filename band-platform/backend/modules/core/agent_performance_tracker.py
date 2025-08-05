"""
Agent Performance Tracking System
Monitors and analyzes agent performance metrics
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio
import json
import statistics
from enum import Enum

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MetricType(str, Enum):
    """Types of metrics tracked."""
    TASK_COMPLETION_TIME = "task_completion_time"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    RESOURCE_USAGE = "resource_usage"
    AVAILABILITY = "availability"
    QUALITY_SCORE = "quality_score"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentPerformanceSnapshot:
    """Point-in-time performance snapshot."""
    agent_id: str
    timestamp: datetime
    metrics: Dict[MetricType, float]
    active_tasks: int
    error_count: int
    success_count: int
    avg_response_time: float
    health_score: float  # 0-100


class AgentMetrics(Base):
    """Database model for agent metrics."""
    __tablename__ = 'agent_metrics'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, index=True)
    metric_type = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)


class AgentPerformanceHistory(Base):
    """Database model for performance history."""
    __tablename__ = 'agent_performance_history'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    snapshot = Column(JSON)
    health_score = Column(Float)
    flagged = Column(Boolean, default=False)


class PerformanceTracker:
    """Tracks and analyzes agent performance."""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_thresholds = self._setup_alert_thresholds()
        self.performance_baselines = {}
        
    def _setup_alert_thresholds(self) -> Dict[MetricType, Dict]:
        """Setup default alert thresholds."""
        return {
            MetricType.ERROR_RATE: {"warning": 0.05, "critical": 0.10},
            MetricType.RESPONSE_TIME: {"warning": 2.0, "critical": 5.0},  # seconds
            MetricType.AVAILABILITY: {"warning": 0.95, "critical": 0.90},
            MetricType.QUALITY_SCORE: {"warning": 0.80, "critical": 0.60},
            MetricType.TASK_COMPLETION_TIME: {"warning": 300, "critical": 600}  # seconds
        }
    
    async def record_metric(
        self, 
        agent_id: str, 
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict] = None
    ):
        """Record a performance metric."""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        
        # Add to buffer
        self.metrics_buffer[f"{agent_id}:{metric_type}"].append(metric)
        
        # Persist to database if available
        if self.db_session:
            db_metric = AgentMetrics(
                agent_id=agent_id,
                metric_type=metric_type.value,
                value=value,
                metadata=metadata
            )
            self.db_session.add(db_metric)
            await self._async_commit()
    
    async def record_task_completion(
        self,
        agent_id: str,
        task_id: str,
        duration_seconds: float,
        success: bool,
        metadata: Optional[Dict] = None
    ):
        """Record task completion metrics."""
        # Record completion time
        await self.record_metric(
            agent_id=agent_id,
            metric_type=MetricType.TASK_COMPLETION_TIME,
            value=duration_seconds,
            metadata={"task_id": task_id, "success": success, **(metadata or {})}
        )
        
        # Update error rate
        error_rate = await self.calculate_error_rate(agent_id)
        await self.record_metric(
            agent_id=agent_id,
            metric_type=MetricType.ERROR_RATE,
            value=error_rate
        )
    
    async def record_response_time(
        self,
        agent_id: str,
        operation: str,
        response_time_ms: float
    ):
        """Record response time for an operation."""
        await self.record_metric(
            agent_id=agent_id,
            metric_type=MetricType.RESPONSE_TIME,
            value=response_time_ms / 1000,  # Convert to seconds
            metadata={"operation": operation}
        )
    
    async def calculate_error_rate(self, agent_id: str) -> float:
        """Calculate current error rate for an agent."""
        metrics = self.metrics_buffer[f"{agent_id}:{MetricType.TASK_COMPLETION_TIME}"]
        if not metrics:
            return 0.0
        
        recent_tasks = list(metrics)[-100:]  # Last 100 tasks
        failures = sum(1 for m in recent_tasks if not m.metadata.get('success', True))
        return failures / len(recent_tasks)
    
    async def calculate_availability(
        self,
        agent_id: str,
        time_window: timedelta = timedelta(hours=1)
    ) -> float:
        """Calculate agent availability over time window."""
        # This would integrate with health checks
        # For now, return based on recent activity
        cutoff = datetime.utcnow() - time_window
        recent_metrics = [
            m for m in self.metrics_buffer[f"{agent_id}:{MetricType.RESPONSE_TIME}"]
            if m.timestamp > cutoff
        ]
        
        if not recent_metrics:
            return 0.0
        
        # Simple availability: ratio of successful responses
        total_time = time_window.total_seconds()
        active_time = len(recent_metrics) * 5  # Assume 5 second intervals
        return min(active_time / total_time, 1.0)
    
    async def calculate_throughput(
        self,
        agent_id: str,
        time_window: timedelta = timedelta(minutes=5)
    ) -> float:
        """Calculate tasks per minute."""
        cutoff = datetime.utcnow() - time_window
        recent_tasks = [
            m for m in self.metrics_buffer[f"{agent_id}:{MetricType.TASK_COMPLETION_TIME}"]
            if m.timestamp > cutoff
        ]
        
        if not recent_tasks:
            return 0.0
        
        minutes = time_window.total_seconds() / 60
        return len(recent_tasks) / minutes
    
    async def calculate_health_score(self, agent_id: str) -> float:
        """Calculate overall health score (0-100)."""
        scores = []
        
        # Error rate score (inverted)
        error_rate = await self.calculate_error_rate(agent_id)
        error_score = max(0, 100 * (1 - error_rate * 10))  # 10% error = 0 score
        scores.append(error_score)
        
        # Response time score
        response_times = [
            m.value for m in self.metrics_buffer[f"{agent_id}:{MetricType.RESPONSE_TIME}"]
        ]
        if response_times:
            avg_response = statistics.mean(response_times[-100:])
            response_score = max(0, 100 * (1 - avg_response / 5))  # 5s = 0 score
            scores.append(response_score)
        
        # Availability score
        availability = await self.calculate_availability(agent_id)
        scores.append(availability * 100)
        
        # Throughput score (normalized)
        throughput = await self.calculate_throughput(agent_id)
        throughput_score = min(100, throughput * 10)  # 10 tasks/min = 100 score
        scores.append(throughput_score)
        
        return statistics.mean(scores) if scores else 50.0
    
    async def get_performance_snapshot(self, agent_id: str) -> AgentPerformanceSnapshot:
        """Get current performance snapshot."""
        response_times = [
            m.value for m in self.metrics_buffer[f"{agent_id}:{MetricType.RESPONSE_TIME}"]
        ]
        
        tasks = list(self.metrics_buffer[f"{agent_id}:{MetricType.TASK_COMPLETION_TIME}"])
        success_count = sum(1 for m in tasks if m.metadata.get('success', True))
        error_count = len(tasks) - success_count
        
        snapshot = AgentPerformanceSnapshot(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            metrics={
                MetricType.ERROR_RATE: await self.calculate_error_rate(agent_id),
                MetricType.RESPONSE_TIME: statistics.mean(response_times[-100:]) if response_times else 0,
                MetricType.THROUGHPUT: await self.calculate_throughput(agent_id),
                MetricType.AVAILABILITY: await self.calculate_availability(agent_id)
            },
            active_tasks=0,  # Would need to integrate with AgentCoordinator
            error_count=error_count,
            success_count=success_count,
            avg_response_time=statistics.mean(response_times[-100:]) if response_times else 0,
            health_score=await self.calculate_health_score(agent_id)
        )
        
        # Store snapshot
        if self.db_session:
            db_snapshot = AgentPerformanceHistory(
                agent_id=agent_id,
                snapshot=snapshot.__dict__,
                health_score=snapshot.health_score,
                flagged=snapshot.health_score < 70
            )
            self.db_session.add(db_snapshot)
            await self._async_commit()
        
        return snapshot
    
    async def check_alerts(self, agent_id: str) -> List[Dict]:
        """Check for performance alerts."""
        alerts = []
        
        for metric_type, thresholds in self.alert_thresholds.items():
            current_value = await self._get_current_metric_value(agent_id, metric_type)
            if current_value is None:
                continue
            
            # Check thresholds
            if metric_type == MetricType.AVAILABILITY:
                # Lower is worse for availability
                if current_value < thresholds["critical"]:
                    alerts.append({
                        "level": "critical",
                        "metric": metric_type.value,
                        "value": current_value,
                        "threshold": thresholds["critical"],
                        "message": f"{metric_type.value} below critical threshold"
                    })
                elif current_value < thresholds["warning"]:
                    alerts.append({
                        "level": "warning",
                        "metric": metric_type.value,
                        "value": current_value,
                        "threshold": thresholds["warning"],
                        "message": f"{metric_type.value} below warning threshold"
                    })
            else:
                # Higher is worse for other metrics
                if current_value > thresholds["critical"]:
                    alerts.append({
                        "level": "critical",
                        "metric": metric_type.value,
                        "value": current_value,
                        "threshold": thresholds["critical"],
                        "message": f"{metric_type.value} above critical threshold"
                    })
                elif current_value > thresholds["warning"]:
                    alerts.append({
                        "level": "warning",
                        "metric": metric_type.value,
                        "value": current_value,
                        "threshold": thresholds["warning"],
                        "message": f"{metric_type.value} above warning threshold"
                    })
        
        return alerts
    
    async def get_performance_trends(
        self,
        agent_id: str,
        metric_type: MetricType,
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict:
        """Get performance trends over time."""
        cutoff = datetime.utcnow() - time_window
        metrics = [
            m for m in self.metrics_buffer[f"{agent_id}:{metric_type}"]
            if m.timestamp > cutoff
        ]
        
        if not metrics:
            return {"trend": "unknown", "data_points": 0}
        
        # Calculate trend
        values = [m.value for m in metrics]
        timestamps = [(m.timestamp - cutoff).total_seconds() for m in metrics]
        
        # Simple linear regression
        if len(values) > 1:
            n = len(values)
            sum_x = sum(timestamps)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(timestamps, values))
            sum_x2 = sum(x * x for x in timestamps)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Determine trend
            if abs(slope) < 0.001:
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "data_points": len(values),
            "current_value": values[-1],
            "average": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    async def compare_agents(
        self,
        agent_ids: List[str],
        metric_type: MetricType
    ) -> Dict[str, Dict]:
        """Compare performance across multiple agents."""
        comparisons = {}
        
        for agent_id in agent_ids:
            current_value = await self._get_current_metric_value(agent_id, metric_type)
            trend = await self.get_performance_trends(agent_id, metric_type)
            
            comparisons[agent_id] = {
                "current_value": current_value,
                "trend": trend["trend"],
                "average": trend.get("average", current_value),
                "health_score": await self.calculate_health_score(agent_id)
            }
        
        # Add rankings
        sorted_agents = sorted(
            comparisons.items(),
            key=lambda x: x[1]["current_value"] or float('inf')
        )
        
        for rank, (agent_id, _) in enumerate(sorted_agents, 1):
            comparisons[agent_id]["rank"] = rank
        
        return comparisons
    
    async def generate_performance_report(self, agent_id: str) -> Dict:
        """Generate comprehensive performance report."""
        snapshot = await self.get_performance_snapshot(agent_id)
        alerts = await self.check_alerts(agent_id)
        
        trends = {}
        for metric_type in MetricType:
            trends[metric_type.value] = await self.get_performance_trends(
                agent_id, metric_type
            )
        
        return {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": snapshot.health_score,
            "snapshot": {
                "metrics": {k.value: v for k, v in snapshot.metrics.items()},
                "active_tasks": snapshot.active_tasks,
                "error_count": snapshot.error_count,
                "success_count": snapshot.success_count,
                "avg_response_time": snapshot.avg_response_time
            },
            "trends": trends,
            "alerts": alerts,
            "recommendations": await self._generate_recommendations(
                snapshot, trends, alerts
            )
        }
    
    async def _get_current_metric_value(
        self,
        agent_id: str,
        metric_type: MetricType
    ) -> Optional[float]:
        """Get current value for a metric."""
        if metric_type == MetricType.ERROR_RATE:
            return await self.calculate_error_rate(agent_id)
        elif metric_type == MetricType.AVAILABILITY:
            return await self.calculate_availability(agent_id)
        elif metric_type == MetricType.THROUGHPUT:
            return await self.calculate_throughput(agent_id)
        else:
            metrics = self.metrics_buffer[f"{agent_id}:{metric_type}"]
            if metrics:
                return metrics[-1].value
        return None
    
    async def _generate_recommendations(
        self,
        snapshot: AgentPerformanceSnapshot,
        trends: Dict,
        alerts: List[Dict]
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Check health score
        if snapshot.health_score < 70:
            recommendations.append(
                "Agent health score is low. Consider reviewing recent errors and response times."
            )
        
        # Check error rate
        if snapshot.metrics.get(MetricType.ERROR_RATE, 0) > 0.05:
            recommendations.append(
                "Error rate is elevated. Review error logs and consider adding error handling."
            )
        
        # Check response time
        if snapshot.avg_response_time > 2.0:
            recommendations.append(
                "Response times are high. Consider optimizing algorithms or adding caching."
            )
        
        # Check trends
        for metric, trend_data in trends.items():
            if trend_data.get("trend") == "increasing" and metric in [
                MetricType.ERROR_RATE.value,
                MetricType.RESPONSE_TIME.value,
                MetricType.TASK_COMPLETION_TIME.value
            ]:
                recommendations.append(
                    f"{metric} is trending upward. Monitor closely and investigate root cause."
                )
        
        # Check for critical alerts
        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        if critical_alerts:
            recommendations.append(
                f"Critical alerts detected for {len(critical_alerts)} metrics. Immediate action required."
            )
        
        return recommendations
    
    async def _async_commit(self):
        """Async database commit."""
        if self.db_session:
            # In real implementation, this would be properly async
            self.db_session.commit()