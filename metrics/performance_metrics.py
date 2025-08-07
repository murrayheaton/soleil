"""
Performance Metrics Collection and Analysis for SOLEil Multi-Agent System

This module tracks and analyzes performance metrics for both the application
and the multi-agent development system.
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
from functools import wraps


@dataclass
class MetricPoint:
    """Single metric measurement point"""
    timestamp: datetime
    name: str
    value: float
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentMetrics:
    """Metrics for individual agent performance"""
    agent_name: str
    task_count: int
    success_rate: float
    avg_completion_time: float  # seconds
    error_count: int
    lines_of_code_produced: int
    test_coverage_achieved: float
    pr_acceptance_rate: float


@dataclass
class SystemMetrics:
    """Overall system performance metrics"""
    total_prps_completed: int
    avg_prp_completion_time: float  # hours
    development_velocity: float  # story points per week
    bug_escape_rate: float  # bugs found in production
    system_uptime: float  # percentage
    api_response_time_p50: float  # milliseconds
    api_response_time_p95: float
    api_response_time_p99: float
    database_query_time_avg: float
    cache_hit_rate: float


class PerformanceTracker:
    """Main performance tracking system"""
    
    def __init__(self, metrics_dir: Path = Path("./metrics/data")):
        self.metrics_dir = metrics_dir
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.current_metrics: List[MetricPoint] = []
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        
    def track_metric(self, name: str, value: float, tags: Dict[str, str] = None, metadata: Dict = None):
        """Record a single metric point"""
        metric = MetricPoint(
            timestamp=datetime.now(),
            name=name,
            value=value,
            tags=tags or {},
            metadata=metadata
        )
        self.current_metrics.append(metric)
        
    def track_agent_task(self, agent_name: str, task_id: str, success: bool, duration: float, loc: int = 0):
        """Track agent task completion"""
        self.track_metric(
            name="agent.task.completion",
            value=duration,
            tags={
                "agent": agent_name,
                "task_id": task_id,
                "success": str(success)
            },
            metadata={"lines_of_code": loc}
        )
        
    def track_api_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Track API request performance"""
        self.track_metric(
            name="api.request.duration",
            value=duration_ms,
            tags={
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code),
                "success": str(200 <= status_code < 300)
            }
        )
        
    def track_database_query(self, query_type: str, table: str, duration_ms: float, rows_affected: int = 0):
        """Track database query performance"""
        self.track_metric(
            name="db.query.duration",
            value=duration_ms,
            tags={
                "type": query_type,
                "table": table
            },
            metadata={"rows_affected": rows_affected}
        )
        
    def calculate_agent_metrics(self, agent_name: str, time_window: timedelta = timedelta(days=7)) -> AgentMetrics:
        """Calculate metrics for a specific agent"""
        cutoff_time = datetime.now() - time_window
        agent_metrics = [
            m for m in self.current_metrics
            if m.tags.get("agent") == agent_name and m.timestamp > cutoff_time
        ]
        
        if not agent_metrics:
            return AgentMetrics(
                agent_name=agent_name,
                task_count=0,
                success_rate=0.0,
                avg_completion_time=0.0,
                error_count=0,
                lines_of_code_produced=0,
                test_coverage_achieved=0.0,
                pr_acceptance_rate=0.0
            )
        
        task_metrics = [m for m in agent_metrics if m.name == "agent.task.completion"]
        successful_tasks = [m for m in task_metrics if m.tags.get("success") == "True"]
        
        return AgentMetrics(
            agent_name=agent_name,
            task_count=len(task_metrics),
            success_rate=len(successful_tasks) / len(task_metrics) if task_metrics else 0,
            avg_completion_time=statistics.mean([m.value for m in task_metrics]) if task_metrics else 0,
            error_count=len(task_metrics) - len(successful_tasks),
            lines_of_code_produced=sum(
                m.metadata.get("lines_of_code", 0) for m in task_metrics if m.metadata
            ),
            test_coverage_achieved=self._get_latest_coverage(agent_name),
            pr_acceptance_rate=self._calculate_pr_acceptance_rate(agent_name)
        )
    
    def calculate_system_metrics(self, time_window: timedelta = timedelta(days=7)) -> SystemMetrics:
        """Calculate overall system metrics"""
        cutoff_time = datetime.now() - time_window
        recent_metrics = [m for m in self.current_metrics if m.timestamp > cutoff_time]
        
        # API metrics
        api_metrics = [m for m in recent_metrics if m.name == "api.request.duration"]
        api_times = [m.value for m in api_metrics]
        
        # Database metrics
        db_metrics = [m for m in recent_metrics if m.name == "db.query.duration"]
        db_times = [m.value for m in db_metrics]
        
        # PRP metrics
        prp_metrics = [m for m in recent_metrics if m.name == "prp.completion"]
        
        return SystemMetrics(
            total_prps_completed=len(prp_metrics),
            avg_prp_completion_time=statistics.mean([m.value for m in prp_metrics]) if prp_metrics else 0,
            development_velocity=self._calculate_velocity(time_window),
            bug_escape_rate=self._calculate_bug_escape_rate(time_window),
            system_uptime=self._calculate_uptime(time_window),
            api_response_time_p50=self._percentile(api_times, 50) if api_times else 0,
            api_response_time_p95=self._percentile(api_times, 95) if api_times else 0,
            api_response_time_p99=self._percentile(api_times, 99) if api_times else 0,
            database_query_time_avg=statistics.mean(db_times) if db_times else 0,
            cache_hit_rate=self._calculate_cache_hit_rate(recent_metrics)
        )
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        # Calculate metrics for all agents
        agents = ["orchestrator", "planning", "frontend", "backend", "database", 
                 "security", "unit_test", "integration_test", "e2e_test", "devops"]
        
        agent_reports = {}
        for agent in agents:
            agent_reports[agent] = asdict(self.calculate_agent_metrics(agent))
        
        system_metrics = asdict(self.calculate_system_metrics())
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "agent_metrics": agent_reports,
            "system_metrics": system_metrics,
            "performance_trends": self._calculate_trends(),
            "recommendations": self._generate_recommendations(agent_reports, system_metrics)
        }
        
        # Save report
        report_file = self.metrics_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _get_latest_coverage(self, agent_name: str) -> float:
        """Get latest test coverage for agent"""
        coverage_metrics = [
            m for m in self.current_metrics
            if m.name == "test.coverage" and m.tags.get("agent") == agent_name
        ]
        return coverage_metrics[-1].value if coverage_metrics else 0.0
    
    def _calculate_pr_acceptance_rate(self, agent_name: str) -> float:
        """Calculate PR acceptance rate for agent"""
        pr_metrics = [
            m for m in self.current_metrics
            if m.name == "pr.review" and m.tags.get("agent") == agent_name
        ]
        if not pr_metrics:
            return 0.0
        accepted = sum(1 for m in pr_metrics if m.tags.get("accepted") == "True")
        return accepted / len(pr_metrics)
    
    def _calculate_velocity(self, time_window: timedelta) -> float:
        """Calculate development velocity in story points per week"""
        cutoff_time = datetime.now() - time_window
        completed_stories = [
            m for m in self.current_metrics
            if m.name == "story.completed" and m.timestamp > cutoff_time
        ]
        total_points = sum(m.value for m in completed_stories)
        weeks = time_window.days / 7
        return total_points / weeks if weeks > 0 else 0
    
    def _calculate_bug_escape_rate(self, time_window: timedelta) -> float:
        """Calculate rate of bugs found in production"""
        cutoff_time = datetime.now() - time_window
        production_bugs = [
            m for m in self.current_metrics
            if m.name == "bug.production" and m.timestamp > cutoff_time
        ]
        total_deployments = len([
            m for m in self.current_metrics
            if m.name == "deployment.production" and m.timestamp > cutoff_time
        ])
        return len(production_bugs) / total_deployments if total_deployments > 0 else 0
    
    def _calculate_uptime(self, time_window: timedelta) -> float:
        """Calculate system uptime percentage"""
        total_seconds = time_window.total_seconds()
        downtime_metrics = [
            m for m in self.current_metrics
            if m.name == "system.downtime" and m.timestamp > datetime.now() - time_window
        ]
        total_downtime = sum(m.value for m in downtime_metrics)
        return ((total_seconds - total_downtime) / total_seconds * 100) if total_seconds > 0 else 100
    
    def _calculate_cache_hit_rate(self, metrics: List[MetricPoint]) -> float:
        """Calculate cache hit rate"""
        cache_metrics = [m for m in metrics if m.name.startswith("cache.")]
        if not cache_metrics:
            return 0.0
        hits = sum(1 for m in cache_metrics if m.tags.get("hit") == "True")
        return hits / len(cache_metrics)
    
    def _calculate_trends(self) -> Dict[str, str]:
        """Calculate performance trends"""
        # This would compare current metrics with historical data
        return {
            "velocity": "increasing",
            "quality": "stable",
            "performance": "improving",
            "reliability": "stable"
        }
    
    def _generate_recommendations(self, agent_metrics: Dict, system_metrics: Dict) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check API performance
        if system_metrics["api_response_time_p95"] > 500:
            recommendations.append("API p95 response time exceeds 500ms - consider caching or query optimization")
        
        # Check database performance
        if system_metrics["database_query_time_avg"] > 100:
            recommendations.append("Database queries averaging >100ms - review indexes and query patterns")
        
        # Check cache effectiveness
        if system_metrics["cache_hit_rate"] < 0.8:
            recommendations.append("Cache hit rate below 80% - review caching strategy")
        
        # Check agent performance
        for agent_name, metrics in agent_metrics.items():
            if metrics["success_rate"] < 0.9:
                recommendations.append(f"{agent_name} success rate below 90% - review error logs")
            if metrics["test_coverage_achieved"] < 0.8:
                recommendations.append(f"{agent_name} test coverage below 80% - add more tests")
        
        return recommendations


# Decorators for automatic performance tracking
def track_performance(metric_name: str):
    """Decorator to automatically track function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000  # Convert to ms
                tracker = PerformanceTracker()
                tracker.track_metric(
                    name=f"function.{metric_name}.duration",
                    value=duration,
                    tags={"function": func.__name__, "success": "True"}
                )
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                tracker = PerformanceTracker()
                tracker.track_metric(
                    name=f"function.{metric_name}.duration",
                    value=duration,
                    tags={"function": func.__name__, "success": "False", "error": str(e)}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                tracker = PerformanceTracker()
                tracker.track_metric(
                    name=f"function.{metric_name}.duration",
                    value=duration,
                    tags={"function": func.__name__, "success": "True"}
                )
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                tracker = PerformanceTracker()
                tracker.track_metric(
                    name=f"function.{metric_name}.duration",
                    value=duration,
                    tags={"function": func.__name__, "success": "False", "error": str(e)}
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Example usage
if __name__ == "__main__":
    tracker = PerformanceTracker()
    
    # Simulate some metrics
    tracker.track_agent_task("backend", "task_001", True, 120.5, 250)
    tracker.track_api_request("/api/bands", "GET", 200, 45.3)
    tracker.track_database_query("SELECT", "bands", 12.5, 10)
    
    # Generate report
    report = tracker.generate_performance_report()
    print(json.dumps(report, indent=2, default=str))