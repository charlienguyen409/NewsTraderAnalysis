"""
Performance metrics collection and analysis utilities
"""
import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np
import json


@dataclass
class PerformanceMetric:
    """Single performance metric measurement"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseTimeMetric:
    """HTTP response time metric"""
    url: str
    method: str
    response_time: float
    status_code: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


@dataclass
class ResourceUsageMetric:
    """System resource usage metric"""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PerformanceCollector:
    """Collect and analyze performance metrics"""
    
    def __init__(self):
        self.response_times: List[ResponseTimeMetric] = []
        self.resource_usage: List[ResourceUsageMetric] = []
        self.custom_metrics: List[PerformanceMetric] = []
        self._start_time = None
        self._initial_disk_io = None
        self._initial_network_io = None
        
    def start_collection(self):
        """Start collecting performance metrics"""
        self._start_time = time.time()
        # Get initial I/O counters
        try:
            self._initial_disk_io = psutil.disk_io_counters()
            self._initial_network_io = psutil.net_io_counters()
        except:
            self._initial_disk_io = None
            self._initial_network_io = None
    
    def stop_collection(self):
        """Stop collecting performance metrics"""
        self._start_time = None
    
    def record_response_time(self, url: str, method: str, response_time: float, 
                           status_code: int, error: str = None):
        """Record an HTTP response time measurement"""
        metric = ResponseTimeMetric(
            url=url,
            method=method,
            response_time=response_time,
            status_code=status_code,
            error=error
        )
        self.response_times.append(metric)
    
    def record_resource_usage(self):
        """Record current system resource usage"""
        try:
            # Get current resource usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Calculate I/O deltas
            disk_io_read_mb = 0
            disk_io_write_mb = 0
            network_io_sent_mb = 0
            network_io_recv_mb = 0
            
            if self._initial_disk_io:
                current_disk_io = psutil.disk_io_counters()
                if current_disk_io:
                    disk_io_read_mb = (current_disk_io.read_bytes - self._initial_disk_io.read_bytes) / (1024 * 1024)
                    disk_io_write_mb = (current_disk_io.write_bytes - self._initial_disk_io.write_bytes) / (1024 * 1024)
            
            if self._initial_network_io:
                current_network_io = psutil.net_io_counters()
                if current_network_io:
                    network_io_sent_mb = (current_network_io.bytes_sent - self._initial_network_io.bytes_sent) / (1024 * 1024)
                    network_io_recv_mb = (current_network_io.bytes_recv - self._initial_network_io.bytes_recv) / (1024 * 1024)
            
            metric = ResourceUsageMetric(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=memory.used / (1024 * 1024),
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                network_io_sent_mb=network_io_sent_mb,
                network_io_recv_mb=network_io_recv_mb
            )
            self.resource_usage.append(metric)
            
        except Exception as e:
            print(f"Error recording resource usage: {e}")
    
    def record_custom_metric(self, name: str, value: float, unit: str, metadata: Dict[str, Any] = None):
        """Record a custom performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        self.custom_metrics.append(metric)
    
    def get_response_time_stats(self, url_pattern: str = None) -> Dict[str, float]:
        """Get response time statistics"""
        response_times = self.response_times
        
        if url_pattern:
            response_times = [rt for rt in response_times if url_pattern in rt.url]
        
        if not response_times:
            return {}
        
        times = [rt.response_time for rt in response_times]
        
        return {
            "count": len(times),
            "mean": np.mean(times),
            "median": np.median(times),
            "min": np.min(times),
            "max": np.max(times),
            "p95": np.percentile(times, 95),
            "p99": np.percentile(times, 99),
            "std": np.std(times)
        }
    
    def get_error_rate(self, url_pattern: str = None) -> float:
        """Calculate error rate for HTTP requests"""
        response_times = self.response_times
        
        if url_pattern:
            response_times = [rt for rt in response_times if url_pattern in rt.url]
        
        if not response_times:
            return 0.0
        
        error_count = len([rt for rt in response_times if rt.status_code >= 400 or rt.error])
        return (error_count / len(response_times)) * 100
    
    def get_throughput(self, url_pattern: str = None) -> float:
        """Calculate requests per second"""
        response_times = self.response_times
        
        if url_pattern:
            response_times = [rt for rt in response_times if url_pattern in rt.url]
        
        if not response_times or not self._start_time:
            return 0.0
        
        duration = time.time() - self._start_time
        return len(response_times) / duration if duration > 0 else 0.0
    
    def get_resource_stats(self) -> Dict[str, Dict[str, float]]:
        """Get resource usage statistics"""
        if not self.resource_usage:
            return {}
        
        cpu_values = [ru.cpu_percent for ru in self.resource_usage]
        memory_values = [ru.memory_mb for ru in self.resource_usage]
        
        return {
            "cpu": {
                "mean": np.mean(cpu_values),
                "max": np.max(cpu_values),
                "min": np.min(cpu_values),
                "p95": np.percentile(cpu_values, 95)
            },
            "memory": {
                "mean": np.mean(memory_values),
                "max": np.max(memory_values),
                "min": np.min(memory_values),
                "p95": np.percentile(memory_values, 95)
            }
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        return {
            "test_duration": time.time() - self._start_time if self._start_time else 0,
            "response_time_stats": self.get_response_time_stats(),
            "error_rate": self.get_error_rate(),
            "throughput_rps": self.get_throughput(),
            "resource_stats": self.get_resource_stats(),
            "total_requests": len(self.response_times),
            "total_errors": len([rt for rt in self.response_times if rt.status_code >= 400 or rt.error]),
            "custom_metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "metadata": metric.metadata
                }
                for metric in self.custom_metrics
            ]
        }
    
    def export_to_json(self, filename: str):
        """Export all metrics to JSON file"""
        data = {
            "response_times": [
                {
                    "url": rt.url,
                    "method": rt.method,
                    "response_time": rt.response_time,
                    "status_code": rt.status_code,
                    "timestamp": rt.timestamp.isoformat(),
                    "error": rt.error
                }
                for rt in self.response_times
            ],
            "resource_usage": [
                {
                    "cpu_percent": ru.cpu_percent,
                    "memory_percent": ru.memory_percent,
                    "memory_mb": ru.memory_mb,
                    "disk_io_read_mb": ru.disk_io_read_mb,
                    "disk_io_write_mb": ru.disk_io_write_mb,
                    "network_io_sent_mb": ru.network_io_sent_mb,
                    "network_io_recv_mb": ru.network_io_recv_mb,
                    "timestamp": ru.timestamp.isoformat()
                }
                for ru in self.resource_usage
            ],
            "report": self.generate_report()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


class PerformanceMonitor:
    """Background performance monitoring"""
    
    def __init__(self, collector: PerformanceCollector, interval: float = 1.0):
        self.collector = collector
        self.interval = interval
        self.running = False
        self._task = None
    
    async def start(self):
        """Start background monitoring"""
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop background monitoring"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                self.collector.record_resource_usage()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.interval)


# Singleton instance
performance_collector = PerformanceCollector()