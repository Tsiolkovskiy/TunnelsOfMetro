"""
Performance Profiler and Optimization System
Monitors game performance and identifies bottlenecks
"""

import time
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum


class ProfileCategory(Enum):
    """Categories for performance profiling"""
    RENDERING = "rendering"
    GAME_LOGIC = "game_logic"
    UI_UPDATE = "ui_update"
    SYSTEM_UPDATE = "system_update"
    EVENT_PROCESSING = "event_processing"
    AI_PROCESSING = "ai_processing"
    SAVE_LOAD = "save_load"
    RESOURCE_MANAGEMENT = "resource_management"


@dataclass
class PerformanceMetric:
    """Individual performance measurement"""
    category: ProfileCategory
    operation: str
    duration: float
    timestamp: float
    frame_number: int


class PerformanceProfiler:
    """
    Performance profiling system for game optimization
    
    Features:
    - Real-time performance monitoring
    - Frame rate tracking and analysis
    - Bottleneck identification
    - Memory usage monitoring
    - Performance history and trends
    """
    
    def __init__(self, history_size: int = 1000):
        """
        Initialize performance profiler
        
        Args:
            history_size: Number of measurements to keep in history
        """
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        
        # Performance tracking
        self.metrics: deque = deque(maxlen=history_size)
        self.frame_times: deque = deque(maxlen=history_size)
        self.category_totals: Dict[ProfileCategory, float] = defaultdict(float)
        self.operation_counts: Dict[str, int] = defaultdict(int)
        
        # Frame tracking
        self.current_frame = 0
        self.frame_start_time = 0.0
        self.last_frame_time = 0.0
        
        # Performance targets
        self.target_fps = 30
        self.target_frame_time = 1.0 / self.target_fps
        
        # Profiling state
        self.profiling_enabled = True
        self.active_timers: Dict[str, float] = {}
        
        self.logger.info("Performance profiler initialized")
    
    def start_frame(self):
        """Mark the start of a new frame"""
        current_time = time.perf_counter()
        
        if self.frame_start_time > 0:
            frame_time = current_time - self.frame_start_time
            self.frame_times.append(frame_time)
            self.last_frame_time = frame_time
        
        self.frame_start_time = current_time
        self.current_frame += 1
        
        # Reset category totals for this frame
        self.category_totals.clear()
    
    def start_timer(self, category: ProfileCategory, operation: str) -> str:
        """
        Start timing an operation
        
        Args:
            category: Performance category
            operation: Name of the operation
            
        Returns:
            Timer key for stopping the timer
        """
        if not self.profiling_enabled:
            return ""
        
        timer_key = f"{category.value}:{operation}"
        self.active_timers[timer_key] = time.perf_counter()
        return timer_key
    
    def stop_timer(self, timer_key: str):
        """
        Stop timing an operation and record the metric
        
        Args:
            timer_key: Timer key returned by start_timer
        """
        if not self.profiling_enabled or not timer_key or timer_key not in self.active_timers:
            return
        
        end_time = time.perf_counter()
        start_time = self.active_timers.pop(timer_key)
        duration = end_time - start_time
        
        # Parse timer key
        category_str, operation = timer_key.split(":", 1)
        category = ProfileCategory(category_str)
        
        # Record metric
        metric = PerformanceMetric(
            category=category,
            operation=operation,
            duration=duration,
            timestamp=end_time,
            frame_number=self.current_frame
        )
        
        self.metrics.append(metric)
        self.category_totals[category] += duration
        self.operation_counts[operation] += 1
    
    def time_operation(self, category: ProfileCategory, operation: str):
        """
        Context manager for timing operations
        
        Args:
            category: Performance category
            operation: Name of the operation
        """
        return PerformanceTimer(self, category, operation)
    
    def get_current_fps(self) -> float:
        """Get current FPS based on recent frame times"""
        if not self.frame_times:
            return 0.0
        
        # Use average of last 10 frames for smoother FPS reading
        recent_frames = list(self.frame_times)[-10:]
        avg_frame_time = sum(recent_frames) / len(recent_frames)
        
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return 0.0
    
    def get_average_fps(self, frames: int = 60) -> float:
        """Get average FPS over specified number of frames"""
        if not self.frame_times:
            return 0.0
        
        recent_frames = list(self.frame_times)[-frames:]
        if not recent_frames:
            return 0.0
        
        avg_frame_time = sum(recent_frames) / len(recent_frames)
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return 0.0
    
    def get_frame_time_stats(self) -> Dict[str, float]:
        """Get frame time statistics"""
        if not self.frame_times:
            return {}
        
        frame_times_list = list(self.frame_times)
        
        return {
            "current": self.last_frame_time * 1000,  # Convert to ms
            "average": (sum(frame_times_list) / len(frame_times_list)) * 1000,
            "min": min(frame_times_list) * 1000,
            "max": max(frame_times_list) * 1000,
            "target": self.target_frame_time * 1000
        }
    
    def get_category_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance breakdown by category"""
        if not self.metrics:
            return {}
        
        category_stats = {}
        
        for category in ProfileCategory:
            category_metrics = [m for m in self.metrics if m.category == category]
            
            if category_metrics:
                durations = [m.duration for m in category_metrics]
                category_stats[category.value] = {
                    "total_time": sum(durations) * 1000,  # Convert to ms
                    "average_time": (sum(durations) / len(durations)) * 1000,
                    "call_count": len(category_metrics),
                    "percentage": (sum(durations) / sum(m.duration for m in self.metrics)) * 100
                }
        
        return category_stats
    
    def get_operation_performance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get performance data for individual operations"""
        if not self.metrics:
            return []
        
        # Group metrics by operation
        operation_metrics = defaultdict(list)
        for metric in self.metrics:
            operation_metrics[metric.operation].append(metric.duration)
        
        # Calculate stats for each operation
        operation_stats = []
        for operation, durations in operation_metrics.items():
            total_time = sum(durations)
            operation_stats.append({
                "operation": operation,
                "total_time": total_time * 1000,  # Convert to ms
                "average_time": (total_time / len(durations)) * 1000,
                "call_count": len(durations),
                "percentage": (total_time / sum(m.duration for m in self.metrics)) * 100
            })
        
        # Sort by total time and return top operations
        operation_stats.sort(key=lambda x: x["total_time"], reverse=True)
        return operation_stats[:limit]
    
    def identify_bottlenecks(self, threshold_ms: float = 5.0) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks
        
        Args:
            threshold_ms: Minimum time in milliseconds to consider a bottleneck
            
        Returns:
            List of bottleneck information
        """
        bottlenecks = []
        
        # Check frame time
        current_fps = self.get_current_fps()
        if current_fps < self.target_fps * 0.8:  # 80% of target FPS
            bottlenecks.append({
                "type": "frame_rate",
                "description": f"Low FPS: {current_fps:.1f} (target: {self.target_fps})",
                "severity": "high" if current_fps < self.target_fps * 0.6 else "medium"
            })
        
        # Check category performance
        category_perf = self.get_category_performance()
        for category, stats in category_perf.items():
            if stats["average_time"] > threshold_ms:
                bottlenecks.append({
                    "type": "category",
                    "category": category,
                    "description": f"{category} taking {stats['average_time']:.2f}ms on average",
                    "severity": "high" if stats["average_time"] > threshold_ms * 2 else "medium"
                })
        
        # Check individual operations
        operation_perf = self.get_operation_performance(5)
        for op in operation_perf:
            if op["average_time"] > threshold_ms:
                bottlenecks.append({
                    "type": "operation",
                    "operation": op["operation"],
                    "description": f"{op['operation']} taking {op['average_time']:.2f}ms on average",
                    "severity": "high" if op["average_time"] > threshold_ms * 2 else "medium"
                })
        
        return bottlenecks
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "fps": {
                "current": self.get_current_fps(),
                "average": self.get_average_fps(),
                "target": self.target_fps
            },
            "frame_time": self.get_frame_time_stats(),
            "categories": self.get_category_performance(),
            "top_operations": self.get_operation_performance(5),
            "bottlenecks": self.identify_bottlenecks(),
            "total_frames": self.current_frame,
            "metrics_collected": len(self.metrics)
        }
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        self.metrics.clear()
        self.frame_times.clear()
        self.category_totals.clear()
        self.operation_counts.clear()
        self.current_frame = 0
        self.frame_start_time = 0.0
        self.last_frame_time = 0.0
        self.active_timers.clear()
        
        self.logger.info("Performance metrics reset")
    
    def enable_profiling(self):
        """Enable performance profiling"""
        self.profiling_enabled = True
        self.logger.info("Performance profiling enabled")
    
    def disable_profiling(self):
        """Disable performance profiling"""
        self.profiling_enabled = False
        self.active_timers.clear()
        self.logger.info("Performance profiling disabled")
    
    def log_performance_report(self):
        """Log a detailed performance report"""
        if not self.metrics:
            self.logger.info("No performance data available")
            return
        
        summary = self.get_performance_summary()
        
        self.logger.info("=== Performance Report ===")
        self.logger.info(f"Current FPS: {summary['fps']['current']:.1f}")
        self.logger.info(f"Average FPS: {summary['fps']['average']:.1f}")
        self.logger.info(f"Frame Time: {summary['frame_time']['current']:.2f}ms (avg: {summary['frame_time']['average']:.2f}ms)")
        
        self.logger.info("Top Categories by Time:")
        for category, stats in summary['categories'].items():
            self.logger.info(f"  {category}: {stats['average_time']:.2f}ms avg ({stats['percentage']:.1f}%)")
        
        self.logger.info("Top Operations by Time:")
        for op in summary['top_operations']:
            self.logger.info(f"  {op['operation']}: {op['average_time']:.2f}ms avg")
        
        if summary['bottlenecks']:
            self.logger.warning("Performance Bottlenecks:")
            for bottleneck in summary['bottlenecks']:
                self.logger.warning(f"  {bottleneck['severity'].upper()}: {bottleneck['description']}")


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, profiler: PerformanceProfiler, category: ProfileCategory, operation: str):
        self.profiler = profiler
        self.category = category
        self.operation = operation
        self.timer_key = ""
    
    def __enter__(self):
        self.timer_key = self.profiler.start_timer(self.category, self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.profiler.stop_timer(self.timer_key)


# Global profiler instance
_global_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get the global performance profiler instance"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def profile_operation(category: ProfileCategory, operation: str):
    """Decorator for profiling function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            profiler = get_profiler()
            with profiler.time_operation(category, operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator