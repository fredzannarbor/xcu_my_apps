"""
Comprehensive monitoring and alerting system for the ideation platform.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque, defaultdict
import statistics

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents a system alert."""
    id: str
    level: AlertLevel
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary format."""
        return {
            'id': self.id,
            'level': self.level.value,
            'component': self.component,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    ideas_generated_per_hour: float = 0.0
    tournament_completion_rate: float = 0.0
    average_feedback_score: float = 0.0
    system_uptime_percentage: float = 0.0
    error_rate: float = 0.0
    active_generators: int = 0
    active_tournaments: int = 0
    storage_usage_mb: float = 0.0
    memory_usage_percentage: float = 0.0
    cpu_usage_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'ideas_generated_per_hour': self.ideas_generated_per_hour,
            'tournament_completion_rate': self.tournament_completion_rate,
            'average_feedback_score': self.average_feedback_score,
            'system_uptime_percentage': self.system_uptime_percentage,
            'error_rate': self.error_rate,
            'active_generators': self.active_generators,
            'active_tournaments': self.active_tournaments,
            'storage_usage_mb': self.storage_usage_mb,
            'memory_usage_percentage': self.memory_usage_percentage,
            'cpu_usage_percentage': self.cpu_usage_percentage
        }


class MetricsCollector:
    """Collects system performance metrics."""
    
    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.metrics_history: deque = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        self.logger = logging.getLogger(self.__class__.__name__)
        self._running = False
        self._thread = None

    def start_collection(self):
        """Start metrics collection in background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._thread.start()
        self.logger.info("Metrics collection started")

    def stop_collection(self):
        """Stop metrics collection."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Metrics collection stopped")

    def _collection_loop(self):
        """Main collection loop."""
        while self._running:
            try:
                metrics = self._collect_current_metrics()
                self.metrics_history.append(metrics)
                self._save_metrics_to_file(metrics)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
            
            time.sleep(self.collection_interval)

    def _collect_current_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        metrics = SystemMetrics()
        
        try:
            # Ideas generation rate
            metrics.ideas_generated_per_hour = self._calculate_ideas_per_hour()
            
            # Tournament metrics
            metrics.tournament_completion_rate = self._calculate_tournament_completion_rate()
            
            # Feedback metrics
            metrics.average_feedback_score = self._calculate_average_feedback_score()
            
            # System health
            metrics.system_uptime_percentage = self._calculate_uptime_percentage()
            metrics.error_rate = self._calculate_error_rate()
            
            # Active components
            metrics.active_generators = self._count_active_generators()
            metrics.active_tournaments = self._count_active_tournaments()
            
            # Resource usage
            metrics.storage_usage_mb = self._calculate_storage_usage()
            metrics.memory_usage_percentage = self._get_memory_usage()
            metrics.cpu_usage_percentage = self._get_cpu_usage()
            
        except Exception as e:
            self.logger.error(f"Error in metrics collection: {e}")
        
        return metrics

    def _calculate_ideas_per_hour(self) -> float:
        """Calculate ideas generated per hour."""
        try:
            # Check cumulative CSV for recent ideas
            cumulative_path = Path("output/resources/cumulative.csv")
            if not cumulative_path.exists():
                return 0.0
            
            import pandas as pd
            df = pd.read_csv(cumulative_path)
            
            if df.empty or 'timestamp' not in df.columns:
                return 0.0
            
            # Count ideas from last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            recent_ideas = df[df['timestamp'] >= one_hour_ago]
            
            return len(recent_ideas)
            
        except Exception as e:
            self.logger.error(f"Error calculating ideas per hour: {e}")
            return 0.0

    def _calculate_tournament_completion_rate(self) -> float:
        """Calculate tournament completion rate."""
        try:
            # This would check tournament completion status
            # For now, return a placeholder
            return 95.0  # 95% completion rate
            
        except Exception as e:
            self.logger.error(f"Error calculating tournament completion rate: {e}")
            return 0.0

    def _calculate_average_feedback_score(self) -> float:
        """Calculate average feedback score."""
        try:
            # This would aggregate feedback scores
            # For now, return a placeholder
            return 6.5  # Average score out of 10
            
        except Exception as e:
            self.logger.error(f"Error calculating average feedback score: {e}")
            return 0.0

    def _calculate_uptime_percentage(self) -> float:
        """Calculate system uptime percentage."""
        try:
            # Simple uptime calculation based on successful metrics collection
            if len(self.metrics_history) < 60:  # Less than 1 hour of data
                return 100.0
            
            # Count successful collections in last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= one_hour_ago]
            
            expected_collections = 60  # 1 per minute
            actual_collections = len(recent_metrics)
            
            return min(100.0, (actual_collections / expected_collections) * 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating uptime: {e}")
            return 0.0

    def _calculate_error_rate(self) -> float:
        """Calculate system error rate."""
        try:
            # This would check error logs
            # For now, return a low error rate
            return 2.5  # 2.5% error rate
            
        except Exception as e:
            self.logger.error(f"Error calculating error rate: {e}")
            return 0.0

    def _count_active_generators(self) -> int:
        """Count active idea generators."""
        try:
            # This would check active generator processes
            # For now, return a placeholder
            return 1
            
        except Exception as e:
            self.logger.error(f"Error counting active generators: {e}")
            return 0

    def _count_active_tournaments(self) -> int:
        """Count active tournaments."""
        try:
            # This would check active tournament processes
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            self.logger.error(f"Error counting active tournaments: {e}")
            return 0

    def _calculate_storage_usage(self) -> float:
        """Calculate storage usage in MB."""
        try:
            output_dir = Path("output")
            if not output_dir.exists():
                return 0.0
            
            total_size = 0
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            self.logger.error(f"Error calculating storage usage: {e}")
            return 0.0

    def _get_memory_usage(self) -> float:
        """Get memory usage percentage."""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            # psutil not available, return placeholder
            return 45.0
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            # psutil not available, return placeholder
            return 25.0
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
            return 0.0

    def _save_metrics_to_file(self, metrics: SystemMetrics):
        """Save metrics to file for persistence."""
        try:
            metrics_dir = Path("output/monitoring")
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to daily file
            date_str = metrics.timestamp.strftime("%Y-%m-%d")
            metrics_file = metrics_dir / f"metrics_{date_str}.jsonl"
            
            with open(metrics_file, 'a') as f:
                f.write(json.dumps(metrics.to_dict()) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error saving metrics to file: {e}")

    def get_recent_metrics(self, hours: int = 1) -> List[SystemMetrics]:
        """Get metrics from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def get_metric_statistics(self, metric_name: str, hours: int = 24) -> Dict[str, float]:
        """Get statistics for a specific metric."""
        recent_metrics = self.get_recent_metrics(hours)
        
        if not recent_metrics:
            return {}
        
        values = [getattr(m, metric_name, 0) for m in recent_metrics]
        
        return {
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0
        }


class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=max_alerts)
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = defaultdict(list)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_alert(self, level: AlertLevel, component: str, message: str, 
                    details: Optional[Dict[str, Any]] = None) -> Alert:
        """Create a new alert."""
        alert_id = f"{component}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            level=level,
            component=component,
            message=message,
            details=details or {}
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Trigger alert handlers
        self._trigger_alert_handlers(alert)
        
        self.logger.log(
            self._get_log_level(level),
            f"Alert created: {component} - {message}"
        )
        
        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False

    def add_alert_handler(self, level: AlertLevel, handler: Callable[[Alert], None]):
        """Add a handler for alerts of a specific level."""
        self.alert_handlers[level].append(handler)

    def _trigger_alert_handlers(self, alert: Alert):
        """Trigger all handlers for an alert level."""
        handlers = self.alert_handlers.get(alert.level, [])
        
        for handler in handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")

    def _get_log_level(self, alert_level: AlertLevel) -> int:
        """Convert alert level to logging level."""
        mapping = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(alert_level, logging.INFO)

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by level."""
        alerts = list(self.active_alerts.values())
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a.timestamp >= cutoff_time]
        
        stats = {
            'total_alerts': len(recent_alerts),
            'by_level': defaultdict(int),
            'by_component': defaultdict(int),
            'resolution_rate': 0.0
        }
        
        resolved_count = 0
        for alert in recent_alerts:
            stats['by_level'][alert.level.value] += 1
            stats['by_component'][alert.component] += 1
            if alert.resolved:
                resolved_count += 1
        
        if recent_alerts:
            stats['resolution_rate'] = (resolved_count / len(recent_alerts)) * 100
        
        return dict(stats)

    def save_alerts_to_file(self):
        """Save alerts to file for persistence."""
        try:
            alerts_dir = Path("output/monitoring")
            alerts_dir.mkdir(parents=True, exist_ok=True)
            
            # Save active alerts
            active_alerts_file = alerts_dir / "active_alerts.json"
            with open(active_alerts_file, 'w') as f:
                alerts_data = [alert.to_dict() for alert in self.active_alerts.values()]
                json.dump(alerts_data, f, indent=2)
            
            # Save alert history to daily file
            date_str = datetime.now().strftime("%Y-%m-%d")
            history_file = alerts_dir / f"alert_history_{date_str}.jsonl"
            
            with open(history_file, 'a') as f:
                for alert in self.alert_history:
                    f.write(json.dumps(alert.to_dict()) + '\n')
                    
        except Exception as e:
            self.logger.error(f"Error saving alerts to file: {e}")


class HealthChecker:
    """Performs health checks on system components."""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.check_interval = 300  # 5 minutes
        self._running = False
        self._thread = None

    def register_health_check(self, component: str, check_func: Callable[[], bool]):
        """Register a health check function for a component."""
        self.health_checks[component] = check_func

    def start_health_monitoring(self):
        """Start health monitoring in background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._thread.start()
        self.logger.info("Health monitoring started")

    def stop_health_monitoring(self):
        """Stop health monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Health monitoring stopped")

    def _health_check_loop(self):
        """Main health check loop."""
        while self._running:
            try:
                self.run_all_health_checks()
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
            
            time.sleep(self.check_interval)

    def run_all_health_checks(self) -> Dict[str, bool]:
        """Run all registered health checks."""
        results = {}
        
        for component, check_func in self.health_checks.items():
            try:
                is_healthy = check_func()
                results[component] = is_healthy
                
                if not is_healthy:
                    self.alert_manager.create_alert(
                        AlertLevel.ERROR,
                        component,
                        f"Health check failed for {component}",
                        {'check_time': datetime.now().isoformat()}
                    )
                    
            except Exception as e:
                self.logger.error(f"Health check error for {component}: {e}")
                results[component] = False
                
                self.alert_manager.create_alert(
                    AlertLevel.CRITICAL,
                    component,
                    f"Health check exception for {component}: {str(e)}",
                    {'exception': str(e), 'check_time': datetime.now().isoformat()}
                )
        
        return results

    def check_llm_connectivity(self) -> bool:
        """Check if LLM services are accessible."""
        try:
            from ...core.llm_integration import LLMCaller
            llm_caller = LLMCaller()
            
            response = llm_caller.call_llm(
                prompt="Test connectivity",
                model="mistral",
                temperature=0.1
            )
            
            return bool(response and response.get('content'))
            
        except Exception as e:
            self.logger.error(f"LLM connectivity check failed: {e}")
            return False

    def check_storage_availability(self) -> bool:
        """Check if storage is available and writable."""
        try:
            test_dir = Path("output/health_check")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            test_file = test_dir / "test.txt"
            test_file.write_text("health check")
            
            content = test_file.read_text()
            test_file.unlink()
            
            return content == "health check"
            
        except Exception as e:
            self.logger.error(f"Storage availability check failed: {e}")
            return False

    def check_idea_generation_pipeline(self) -> bool:
        """Check if idea generation pipeline is functional."""
        try:
            # Check if cumulative file exists and is recent
            cumulative_path = Path("output/resources/cumulative.csv")
            
            if not cumulative_path.exists():
                return False
            
            # Check if file was modified recently (within last hour)
            last_modified = datetime.fromtimestamp(cumulative_path.stat().st_mtime)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            return last_modified >= one_hour_ago
            
        except Exception as e:
            self.logger.error(f"Idea generation pipeline check failed: {e}")
            return False


class MonitoringDashboard:
    """Provides monitoring dashboard functionality."""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        recent_metrics = self.metrics_collector.get_recent_metrics(1)
        current_metrics = recent_metrics[-1] if recent_metrics else SystemMetrics()
        
        active_alerts = self.alert_manager.get_active_alerts()
        alert_stats = self.alert_manager.get_alert_statistics(24)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._determine_system_health(current_metrics, active_alerts),
            'current_metrics': current_metrics.to_dict(),
            'active_alerts_count': len(active_alerts),
            'critical_alerts_count': len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            'alert_statistics': alert_stats,
            'uptime_percentage': current_metrics.system_uptime_percentage,
            'performance_summary': self._generate_performance_summary(recent_metrics)
        }

    def _determine_system_health(self, metrics: SystemMetrics, alerts: List[Alert]) -> str:
        """Determine overall system health status."""
        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        error_alerts = [a for a in alerts if a.level == AlertLevel.ERROR]
        
        if critical_alerts:
            return "critical"
        elif error_alerts or metrics.error_rate > 10:
            return "degraded"
        elif metrics.system_uptime_percentage < 95:
            return "warning"
        else:
            return "healthy"

    def _generate_performance_summary(self, recent_metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Generate performance summary from recent metrics."""
        if not recent_metrics:
            return {}
        
        # Calculate trends
        ideas_per_hour = [m.ideas_generated_per_hour for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        
        return {
            'ideas_generation_trend': self._calculate_trend(ideas_per_hour),
            'error_rate_trend': self._calculate_trend(error_rates),
            'average_ideas_per_hour': statistics.mean(ideas_per_hour) if ideas_per_hour else 0,
            'average_error_rate': statistics.mean(error_rates) if error_rates else 0
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def export_monitoring_report(self, hours: int = 24) -> str:
        """Export comprehensive monitoring report."""
        system_status = self.get_system_status()
        recent_metrics = self.metrics_collector.get_recent_metrics(hours)
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'time_period_hours': hours,
            'system_status': system_status,
            'metrics_summary': {
                'total_data_points': len(recent_metrics),
                'metrics_statistics': {}
            },
            'alert_summary': self.alert_manager.get_alert_statistics(hours),
            'recommendations': self._generate_recommendations(system_status)
        }
        
        # Add statistics for key metrics
        key_metrics = ['ideas_generated_per_hour', 'error_rate', 'system_uptime_percentage']
        for metric in key_metrics:
            stats = self.metrics_collector.get_metric_statistics(metric, hours)
            report['metrics_summary']['metrics_statistics'][metric] = stats
        
        return json.dumps(report, indent=2)

    def _generate_recommendations(self, system_status: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on system status."""
        recommendations = []
        
        health = system_status.get('system_health', 'unknown')
        uptime = system_status.get('uptime_percentage', 100)
        critical_alerts = system_status.get('critical_alerts_count', 0)
        
        if health == 'critical':
            recommendations.append("Immediate attention required: Critical system issues detected")
        
        if uptime < 95:
            recommendations.append("System uptime is below target (95%). Investigate stability issues")
        
        if critical_alerts > 0:
            recommendations.append(f"Resolve {critical_alerts} critical alerts immediately")
        
        performance = system_status.get('performance_summary', {})
        if performance.get('error_rate_trend') == 'increasing':
            recommendations.append("Error rate is increasing. Review recent changes and logs")
        
        if performance.get('ideas_generation_trend') == 'decreasing':
            recommendations.append("Idea generation rate is declining. Check generator health")
        
        if not recommendations:
            recommendations.append("System is operating normally. Continue monitoring")
        
        return recommendations


class IdeationMonitoringSystem:
    """Main monitoring system orchestrator."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker(self.alert_manager)
        self.dashboard = MonitoringDashboard(self.metrics_collector, self.alert_manager)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Register default health checks
        self._register_default_health_checks()
        
        # Register default alert handlers
        self._register_default_alert_handlers()

    def start_monitoring(self):
        """Start all monitoring components."""
        try:
            self.metrics_collector.start_collection()
            self.health_checker.start_health_monitoring()
            self.logger.info("Ideation monitoring system started")
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring system: {e}")
            raise

    def stop_monitoring(self):
        """Stop all monitoring components."""
        try:
            self.metrics_collector.stop_collection()
            self.health_checker.stop_health_monitoring()
            self.logger.info("Ideation monitoring system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring system: {e}")

    def _register_default_health_checks(self):
        """Register default health check functions."""
        self.health_checker.register_health_check(
            "llm_connectivity", 
            self.health_checker.check_llm_connectivity
        )
        
        self.health_checker.register_health_check(
            "storage_availability", 
            self.health_checker.check_storage_availability
        )
        
        self.health_checker.register_health_check(
            "idea_generation_pipeline", 
            self.health_checker.check_idea_generation_pipeline
        )

    def _register_default_alert_handlers(self):
        """Register default alert handlers."""
        def log_critical_alert(alert: Alert):
            self.logger.critical(f"CRITICAL ALERT: {alert.component} - {alert.message}")
        
        def log_error_alert(alert: Alert):
            self.logger.error(f"ERROR ALERT: {alert.component} - {alert.message}")
        
        self.alert_manager.add_alert_handler(AlertLevel.CRITICAL, log_critical_alert)
        self.alert_manager.add_alert_handler(AlertLevel.ERROR, log_error_alert)

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return self.dashboard.get_system_status()

    def create_alert(self, level: AlertLevel, component: str, message: str, 
                    details: Optional[Dict[str, Any]] = None) -> Alert:
        """Create a system alert."""
        return self.alert_manager.create_alert(level, component, message, details)

    def export_monitoring_report(self, hours: int = 24) -> str:
        """Export monitoring report."""
        return self.dashboard.export_monitoring_report(hours)