#!/usr/bin/env python3
"""
Comprehensive Logging and Monitoring System
Structured logging, performance metrics, and health monitoring for Streamlit apps
"""

import logging
import json
import os
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    APP_START = "app_start"
    APP_STOP = "app_stop"
    APP_RESTART = "app_restart"
    HEALTH_CHECK = "health_check"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR_OCCURRED = "error_occurred"
    CONFIG_UPDATE = "config_update"
    PORT_CONFLICT = "port_conflict"


@dataclass
class LogEntry:
    timestamp: str
    level: str
    event_type: str
    app_name: str
    message: str
    details: Dict[str, Any]
    performance_metrics: Optional[Dict[str, float]] = None
    error_info: Optional[Dict[str, str]] = None


@dataclass
class PerformanceMetrics:
    timestamp: str
    app_name: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    response_time_ms: Optional[float] = None
    request_count: Optional[int] = None
    error_count: Optional[int] = None


class StreamlitLogger:
    """Structured logging system for Streamlit app management"""
    
    def __init__(self, log_dir="logs", max_log_size_mb=50, backup_count=5):
        self.log_dir = log_dir
        self.max_log_size_mb = max_log_size_mb
        self.backup_count = backup_count
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup loggers
        self._setup_loggers()
        
        # Initialize database for structured logs
        self._init_log_database()
    
    def _setup_loggers(self):
        """Setup file and console loggers"""
        # Main application logger
        self.app_logger = logging.getLogger('streamlit_app_manager')
        self.app_logger.setLevel(logging.INFO)
        
        # Performance logger
        self.perf_logger = logging.getLogger('streamlit_performance')
        self.perf_logger.setLevel(logging.INFO)
        
        # Error logger
        self.error_logger = logging.getLogger('streamlit_errors')
        self.error_logger.setLevel(logging.WARNING)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        json_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup file handlers with rotation
        from logging.handlers import RotatingFileHandler
        
        # Main log file
        app_handler = RotatingFileHandler(
            os.path.join(self.log_dir, 'streamlit_manager.log'),
            maxBytes=self.max_log_size_mb * 1024 * 1024,
            backupCount=self.backup_count
        )
        app_handler.setFormatter(detailed_formatter)
        self.app_logger.addHandler(app_handler)
        
        # Performance log file
        perf_handler = RotatingFileHandler(
            os.path.join(self.log_dir, 'performance.log'),
            maxBytes=self.max_log_size_mb * 1024 * 1024,
            backupCount=self.backup_count
        )
        perf_handler.setFormatter(json_formatter)
        self.perf_logger.addHandler(perf_handler)
        
        # Error log file
        error_handler = RotatingFileHandler(
            os.path.join(self.log_dir, 'errors.log'),
            maxBytes=self.max_log_size_mb * 1024 * 1024,
            backupCount=self.backup_count
        )
        error_handler.setFormatter(detailed_formatter)
        self.error_logger.addHandler(error_handler)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(detailed_formatter)
        
        self.app_logger.addHandler(console_handler)
        self.error_logger.addHandler(console_handler)
    
    def _init_log_database(self):
        """Initialize SQLite database for structured logging"""
        self.db_path = os.path.join(self.log_dir, 'streamlit_logs.db')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Log entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                event_type TEXT NOT NULL,
                app_name TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                performance_metrics TEXT,
                error_info TEXT
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                app_name TEXT NOT NULL,
                cpu_percent REAL,
                memory_mb REAL,
                memory_percent REAL,
                response_time_ms REAL,
                request_count INTEGER,
                error_count INTEGER
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_timestamp ON log_entries(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_app_name ON log_entries(app_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_event_type ON log_entries(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_app_name ON performance_metrics(app_name)')
        
        conn.commit()
        conn.close()
    
    def log_event(self, level: LogLevel, event_type: EventType, app_name: str, 
                  message: str, details: Dict[str, Any] = None, 
                  performance_metrics: Dict[str, float] = None,
                  error_info: Dict[str, str] = None):
        """Log a structured event"""
        
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            event_type=event_type.value,
            app_name=app_name,
            message=message,
            details=details or {},
            performance_metrics=performance_metrics,
            error_info=error_info
        )
        
        # Log to appropriate file logger
        log_message = f"[{event_type.value}] {app_name}: {message}"
        if details:
            log_message += f" | Details: {json.dumps(details)}"
        
        if level == LogLevel.DEBUG:
            self.app_logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.app_logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.app_logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.error_logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.error_logger.critical(log_message)
        
        # Store in database
        self._store_log_entry(log_entry)
    
    def _store_log_entry(self, log_entry: LogEntry):
        """Store log entry in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO log_entries 
                (timestamp, level, event_type, app_name, message, details, performance_metrics, error_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.timestamp,
                log_entry.level,
                log_entry.event_type,
                log_entry.app_name,
                log_entry.message,
                json.dumps(log_entry.details) if log_entry.details else None,
                json.dumps(log_entry.performance_metrics) if log_entry.performance_metrics else None,
                json.dumps(log_entry.error_info) if log_entry.error_info else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # Fallback to file logging if database fails
            self.error_logger.error(f"Failed to store log entry in database: {e}")
    
    def log_performance_metrics(self, metrics: PerformanceMetrics):
        """Log performance metrics"""
        # Log to performance logger
        perf_data = asdict(metrics)
        self.perf_logger.info(json.dumps(perf_data))
        
        # Store in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics 
                (timestamp, app_name, cpu_percent, memory_mb, memory_percent, 
                 response_time_ms, request_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp,
                metrics.app_name,
                metrics.cpu_percent,
                metrics.memory_mb,
                metrics.memory_percent,
                metrics.response_time_ms,
                metrics.request_count,
                metrics.error_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.error_logger.error(f"Failed to store performance metrics: {e}")
    
    def get_recent_logs(self, hours: int = 24, app_name: str = None, 
                       event_type: str = None, level: str = None) -> List[Dict]:
        """Get recent log entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT timestamp, level, event_type, app_name, message, details, 
                       performance_metrics, error_info
                FROM log_entries 
                WHERE timestamp >= ?
            '''
            params = [(datetime.now() - timedelta(hours=hours)).isoformat()]
            
            if app_name:
                query += ' AND app_name = ?'
                params.append(app_name)
            
            if event_type:
                query += ' AND event_type = ?'
                params.append(event_type)
            
            if level:
                query += ' AND level = ?'
                params.append(level)
            
            query += ' ORDER BY timestamp DESC LIMIT 1000'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            logs = []
            for row in results:
                log_dict = {
                    'timestamp': row[0],
                    'level': row[1],
                    'event_type': row[2],
                    'app_name': row[3],
                    'message': row[4],
                    'details': json.loads(row[5]) if row[5] else {},
                    'performance_metrics': json.loads(row[6]) if row[6] else None,
                    'error_info': json.loads(row[7]) if row[7] else None
                }
                logs.append(log_dict)
            
            conn.close()
            return logs
            
        except Exception as e:
            self.error_logger.error(f"Failed to retrieve logs: {e}")
            return []
    
    def get_performance_summary(self, hours: int = 24, app_name: str = None) -> Dict:
        """Get performance metrics summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT app_name, 
                       AVG(cpu_percent) as avg_cpu,
                       MAX(cpu_percent) as max_cpu,
                       AVG(memory_mb) as avg_memory,
                       MAX(memory_mb) as max_memory,
                       AVG(response_time_ms) as avg_response_time,
                       COUNT(*) as metric_count
                FROM performance_metrics 
                WHERE timestamp >= ?
            '''
            params = [(datetime.now() - timedelta(hours=hours)).isoformat()]
            
            if app_name:
                query += ' AND app_name = ? GROUP BY app_name'
                params.append(app_name)
            else:
                query += ' GROUP BY app_name'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            summary = {}
            for row in results:
                summary[row[0]] = {
                    'avg_cpu_percent': round(row[1] or 0, 2),
                    'max_cpu_percent': round(row[2] or 0, 2),
                    'avg_memory_mb': round(row[3] or 0, 2),
                    'max_memory_mb': round(row[4] or 0, 2),
                    'avg_response_time_ms': round(row[5] or 0, 2),
                    'metric_count': row[6]
                }
            
            conn.close()
            return summary
            
        except Exception as e:
            self.error_logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log entries"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up log entries
            cursor.execute('DELETE FROM log_entries WHERE timestamp < ?', (cutoff_date,))
            log_deleted = cursor.rowcount
            
            # Clean up performance metrics
            cursor.execute('DELETE FROM performance_metrics WHERE timestamp < ?', (cutoff_date,))
            perf_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.app_logger.info(f"Cleaned up {log_deleted} log entries and {perf_deleted} performance metrics older than {days} days")
            
        except Exception as e:
            self.error_logger.error(f"Failed to cleanup old logs: {e}")


class PerformanceMonitor:
    """Monitors performance metrics for Streamlit apps"""
    
    def __init__(self, logger: StreamlitLogger, check_interval: int = 60):
        self.logger = logger
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread = None
        self.app_processes = {}  # app_name -> pid mapping
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.log_event(
            LogLevel.INFO,
            EventType.CONFIG_UPDATE,
            "system",
            f"Performance monitoring started with {self.check_interval}s interval"
        )
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.log_event(
            LogLevel.INFO,
            EventType.CONFIG_UPDATE,
            "system",
            "Performance monitoring stopped"
        )
    
    def register_app_process(self, app_name: str, pid: int):
        """Register an app process for monitoring"""
        self.app_processes[app_name] = pid
        
        self.logger.log_event(
            LogLevel.INFO,
            EventType.APP_START,
            app_name,
            f"Registered process for monitoring",
            details={'pid': pid}
        )
    
    def unregister_app_process(self, app_name: str):
        """Unregister an app process"""
        if app_name in self.app_processes:
            del self.app_processes[app_name]
            
            self.logger.log_event(
                LogLevel.INFO,
                EventType.APP_STOP,
                app_name,
                "Unregistered process from monitoring"
            )
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._collect_performance_metrics()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.log_event(
                    LogLevel.ERROR,
                    EventType.ERROR_OCCURRED,
                    "system",
                    f"Performance monitoring error: {str(e)}",
                    error_info={'error': str(e), 'type': 'monitoring_error'}
                )
                time.sleep(5)  # Brief pause before retrying
    
    def _collect_performance_metrics(self):
        """Collect performance metrics for all registered apps"""
        for app_name, pid in self.app_processes.items():
            try:
                if not psutil.pid_exists(pid):
                    self.logger.log_event(
                        LogLevel.WARNING,
                        EventType.ERROR_OCCURRED,
                        app_name,
                        f"Process {pid} no longer exists",
                        details={'pid': pid}
                    )
                    continue
                
                process = psutil.Process(pid)
                
                # Collect metrics
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_percent = process.memory_percent()
                
                # Create performance metrics object
                metrics = PerformanceMetrics(
                    timestamp=datetime.now().isoformat(),
                    app_name=app_name,
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent
                )
                
                # Log metrics
                self.logger.log_performance_metrics(metrics)
                
                # Check for performance issues
                self._check_performance_thresholds(app_name, metrics)
                
            except psutil.NoSuchProcess:
                self.logger.log_event(
                    LogLevel.WARNING,
                    EventType.ERROR_OCCURRED,
                    app_name,
                    f"Process {pid} terminated",
                    details={'pid': pid}
                )
            except Exception as e:
                self.logger.log_event(
                    LogLevel.ERROR,
                    EventType.ERROR_OCCURRED,
                    app_name,
                    f"Failed to collect metrics: {str(e)}",
                    error_info={'error': str(e), 'pid': pid}
                )
    
    def _check_performance_thresholds(self, app_name: str, metrics: PerformanceMetrics):
        """Check if performance metrics exceed thresholds"""
        # Define thresholds
        cpu_threshold = 80.0  # 80% CPU
        memory_threshold_mb = 1024  # 1GB RAM
        
        if metrics.cpu_percent > cpu_threshold:
            self.logger.log_event(
                LogLevel.WARNING,
                EventType.PERFORMANCE_METRIC,
                app_name,
                f"High CPU usage: {metrics.cpu_percent:.1f}%",
                details={
                    'threshold': cpu_threshold,
                    'actual': metrics.cpu_percent,
                    'metric_type': 'cpu_usage'
                }
            )
        
        if metrics.memory_mb > memory_threshold_mb:
            self.logger.log_event(
                LogLevel.WARNING,
                EventType.PERFORMANCE_METRIC,
                app_name,
                f"High memory usage: {metrics.memory_mb:.1f}MB",
                details={
                    'threshold': memory_threshold_mb,
                    'actual': metrics.memory_mb,
                    'metric_type': 'memory_usage'
                }
            )


class HealthMonitor:
    """Health monitoring system for Streamlit apps"""
    
    def __init__(self, logger: StreamlitLogger):
        self.logger = logger
        self.health_checks = {}  # app_name -> last_check_time
    
    def perform_health_check(self, app_name: str, url: str) -> Dict:
        """Perform health check on an app"""
        start_time = time.time()
        
        try:
            import requests
            
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                self.logger.log_event(
                    LogLevel.INFO,
                    EventType.HEALTH_CHECK,
                    app_name,
                    f"Health check passed",
                    details={
                        'url': url,
                        'status_code': response.status_code,
                        'response_time_ms': response_time
                    },
                    performance_metrics={'response_time_ms': response_time}
                )
                
                self.health_checks[app_name] = datetime.now()
                
                return {
                    'healthy': True,
                    'status_code': response.status_code,
                    'response_time_ms': response_time
                }
            else:
                self.logger.log_event(
                    LogLevel.WARNING,
                    EventType.HEALTH_CHECK,
                    app_name,
                    f"Health check failed with status {response.status_code}",
                    details={
                        'url': url,
                        'status_code': response.status_code,
                        'response_time_ms': response_time
                    },
                    error_info={
                        'error_type': 'http_error',
                        'status_code': str(response.status_code)
                    }
                )
                
                return {
                    'healthy': False,
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            self.logger.log_event(
                LogLevel.ERROR,
                EventType.HEALTH_CHECK,
                app_name,
                f"Health check failed: {str(e)}",
                details={
                    'url': url,
                    'response_time_ms': response_time
                },
                error_info={
                    'error_type': 'connection_error',
                    'error_message': str(e)
                }
            )
            
            return {
                'healthy': False,
                'response_time_ms': response_time,
                'error': str(e)
            }


# Global instances
streamlit_logger = StreamlitLogger()
performance_monitor = PerformanceMonitor(streamlit_logger)
health_monitor = HealthMonitor(streamlit_logger)


# Convenience functions
def log_app_event(level: LogLevel, event_type: EventType, app_name: str, 
                  message: str, **kwargs):
    """Log an app event"""
    streamlit_logger.log_event(level, event_type, app_name, message, **kwargs)


def start_performance_monitoring(check_interval: int = 60):
    """Start performance monitoring"""
    performance_monitor.check_interval = check_interval
    performance_monitor.start_monitoring()


def stop_performance_monitoring():
    """Stop performance monitoring"""
    performance_monitor.stop_monitoring()


def register_app_for_monitoring(app_name: str, pid: int):
    """Register app for performance monitoring"""
    performance_monitor.register_app_process(app_name, pid)


def get_recent_logs(hours: int = 24, **filters) -> List[Dict]:
    """Get recent log entries"""
    return streamlit_logger.get_recent_logs(hours, **filters)


def get_performance_summary(hours: int = 24, app_name: str = None) -> Dict:
    """Get performance summary"""
    return streamlit_logger.get_performance_summary(hours, app_name)


def perform_health_check(app_name: str, url: str) -> Dict:
    """Perform health check"""
    return health_monitor.perform_health_check(app_name, url)


if __name__ == "__main__":
    # Test the logging and monitoring system
    print("Testing Logging and Monitoring System...")
    
    # Test logging
    log_app_event(
        LogLevel.INFO,
        EventType.APP_START,
        "test_app",
        "Test application started",
        details={'port': 8501, 'pid': 12345}
    )
    
    # Test performance monitoring
    start_performance_monitoring(check_interval=5)
    register_app_for_monitoring("test_app", os.getpid())
    
    # Wait a moment
    time.sleep(2)
    
    # Test log retrieval
    recent_logs = get_recent_logs(hours=1)
    print(f"Retrieved {len(recent_logs)} recent log entries")
    
    # Test performance summary
    perf_summary = get_performance_summary(hours=1)
    print(f"Performance summary: {perf_summary}")
    
    # Stop monitoring
    stop_performance_monitoring()
    
    print("Logging and Monitoring System test completed!")