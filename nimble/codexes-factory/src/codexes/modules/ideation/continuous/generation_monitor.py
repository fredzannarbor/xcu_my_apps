"""
Generation monitoring system for continuous ideation workflows.
Provides monitoring, alerting, and performance tracking.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfiguration:
    """Configuration for generation monitoring."""
    check_interval: int = 60  # seconds between checks
    performance_window: int = 3600  # seconds for performance calculations
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "failure_rate": 0.3,  # Alert if failure rate > 30%
        "generation_delay": 1800,  # Alert if no generation for 30 minutes
        "memory_usage": 0.8,  # Alert if memory usage > 80%
        "error_count": 10  # Alert if more than 10 errors
    })
    enable_alerts: bool = True
    alert_callback: Optional[Callable] = None


class GenerationMonitor:
    """Monitors continuous generation performance and health."""
    
    def __init__(self, config: Optional[MonitoringConfiguration] = None):
        """Initialize the generation monitor."""
        self.config = config or MonitoringConfiguration()
        self.monitoring_data: Dict[str, List[Dict[str, Any]]] = {}
        self.alerts: List[Dict[str, Any]] = []
        logger.info("GenerationMonitor initialized")
    
    def record_generation_event(self, session_id: str, event_type: str, 
                              event_data: Dict[str, Any]):
        """Record a generation event for monitoring."""
        if session_id not in self.monitoring_data:
            self.monitoring_data[session_id] = []
        
        event = {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "data": event_data
        }
        
        self.monitoring_data[session_id].append(event)
        
        # Clean up old events
        self._cleanup_old_events(session_id)
        
        logger.debug(f"Recorded {event_type} event for session {session_id}")
    
    def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get performance metrics for a session."""
        if session_id not in self.monitoring_data:
            return {"error": "No monitoring data for session"}
        
        events = self.monitoring_data[session_id]
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.config.performance_window)
        
        # Filter events within performance window
        recent_events = [e for e in events if e["timestamp"] >= window_start]
        
        if not recent_events:
            return {"error": "No recent events"}
        
        # Calculate metrics
        generation_events = [e for e in recent_events if e["event_type"] == "generation_completed"]
        error_events = [e for e in recent_events if e["event_type"] == "generation_failed"]
        
        total_generations = len(generation_events)
        total_errors = len(error_events)
        
        success_rate = (total_generations / (total_generations + total_errors)) if (total_generations + total_errors) > 0 else 0
        failure_rate = 1 - success_rate
        
        # Calculate generation rate (generations per hour)
        window_hours = self.config.performance_window / 3600
        generation_rate = total_generations / window_hours if window_hours > 0 else 0
        
        # Calculate average generation time
        generation_times = []
        for event in generation_events:
            if "generation_time" in event["data"]:
                generation_times.append(event["data"]["generation_time"])
        
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0
        
        # Time since last generation
        last_generation = None
        if generation_events:
            last_generation = max(generation_events, key=lambda e: e["timestamp"])["timestamp"]
        
        time_since_last = None
        if last_generation:
            time_since_last = (current_time - last_generation).total_seconds()
        
        return {
            "session_id": session_id,
            "performance_window_hours": window_hours,
            "total_generations": total_generations,
            "total_errors": total_errors,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "generation_rate_per_hour": generation_rate,
            "average_generation_time": avg_generation_time,
            "time_since_last_generation": time_since_last,
            "last_generation": last_generation.isoformat() if last_generation else None
        }
    
    def check_alerts(self, session_id: str) -> List[Dict[str, Any]]:
        """Check for alert conditions and return any alerts."""
        alerts = []
        
        try:
            metrics = self.get_performance_metrics(session_id)
            
            if "error" in metrics:
                return alerts
            
            # Check failure rate
            if metrics["failure_rate"] > self.config.alert_thresholds["failure_rate"]:
                alerts.append({
                    "type": "high_failure_rate",
                    "severity": "warning",
                    "message": f"High failure rate: {metrics['failure_rate']:.2%}",
                    "session_id": session_id,
                    "timestamp": datetime.now()
                })
            
            # Check generation delay
            if (metrics["time_since_last_generation"] and 
                metrics["time_since_last_generation"] > self.config.alert_thresholds["generation_delay"]):
                alerts.append({
                    "type": "generation_delay",
                    "severity": "warning",
                    "message": f"No generation for {metrics['time_since_last_generation']:.0f} seconds",
                    "session_id": session_id,
                    "timestamp": datetime.now()
                })
            
            # Check error count
            if metrics["total_errors"] > self.config.alert_thresholds["error_count"]:
                alerts.append({
                    "type": "high_error_count",
                    "severity": "error",
                    "message": f"High error count: {metrics['total_errors']} errors",
                    "session_id": session_id,
                    "timestamp": datetime.now()
                })
            
            # Store alerts
            self.alerts.extend(alerts)
            
            # Trigger alert callback if configured
            if alerts and self.config.alert_callback:
                for alert in alerts:
                    self.config.alert_callback(alert)
            
        except Exception as e:
            logger.error(f"Error checking alerts for session {session_id}: {e}")
        
        return alerts
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        total_sessions = len(self.monitoring_data)
        
        if total_sessions == 0:
            return {
                "status": "no_data",
                "total_sessions": 0,
                "healthy_sessions": 0,
                "warning_sessions": 0,
                "error_sessions": 0
            }
        
        healthy_sessions = 0
        warning_sessions = 0
        error_sessions = 0
        
        for session_id in self.monitoring_data:
            alerts = self.check_alerts(session_id)
            
            if not alerts:
                healthy_sessions += 1
            elif any(alert["severity"] == "error" for alert in alerts):
                error_sessions += 1
            else:
                warning_sessions += 1
        
        # Determine overall status
        if error_sessions > 0:
            overall_status = "error"
        elif warning_sessions > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "total_sessions": total_sessions,
            "healthy_sessions": healthy_sessions,
            "warning_sessions": warning_sessions,
            "error_sessions": error_sessions,
            "total_alerts": len(self.alerts)
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return sorted(self.alerts, key=lambda a: a["timestamp"], reverse=True)[:limit]
    
    def clear_alerts(self, session_id: Optional[str] = None):
        """Clear alerts for a session or all alerts."""
        if session_id:
            self.alerts = [a for a in self.alerts if a.get("session_id") != session_id]
        else:
            self.alerts.clear()
        
        logger.info(f"Cleared alerts for session: {session_id or 'all'}")
    
    def _cleanup_old_events(self, session_id: str):
        """Clean up old monitoring events."""
        if session_id not in self.monitoring_data:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=self.config.performance_window * 2)
        
        # Keep only recent events
        self.monitoring_data[session_id] = [
            event for event in self.monitoring_data[session_id]
            if event["timestamp"] >= cutoff_time
        ]
    
    def export_monitoring_data(self, session_id: str) -> Dict[str, Any]:
        """Export monitoring data for a session."""
        if session_id not in self.monitoring_data:
            return {"error": "No monitoring data for session"}
        
        return {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "events": [
                {
                    "timestamp": event["timestamp"].isoformat(),
                    "event_type": event["event_type"],
                    "data": event["data"]
                }
                for event in self.monitoring_data[session_id]
            ],
            "performance_metrics": self.get_performance_metrics(session_id),
            "recent_alerts": [
                alert for alert in self.alerts 
                if alert.get("session_id") == session_id
            ]
        }