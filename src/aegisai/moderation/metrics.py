"""
Cost and latency tracking utilities for moderation operations.

This module provides helpers to track API costs and latency for optimization analysis.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class OperationMetrics:
    """Tracks metrics for a single operation."""
    operation_name: str
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    tokens_used: int = 0
    api_calls: int = 0
    cost_usd: float = 0.0
    error: Optional[str] = None
    
    @property
    def latency_ms(self) -> float:
        """Latency in milliseconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000
    
    @property
    def cost_per_token(self) -> float:
        """Cost per token in USD."""
        if self.tokens_used == 0:
            return 0.0
        return self.cost_usd / self.tokens_used


class MetricsCollector:
    """Collects metrics across multiple operations."""
    
    def __init__(self):
        self.operations: Dict[str, list[OperationMetrics]] = {}
        self.current_operation: Optional[OperationMetrics] = None
    
    @contextmanager
    def track_operation(self, name: str):
        """Context manager to track an operation's metrics."""
        op = OperationMetrics(operation_name=name)
        self.current_operation = op
        
        try:
            yield op
        except Exception as e:
            op.error = str(e)
            raise
        finally:
            op.end_time = time.perf_counter()
            if name not in self.operations:
                self.operations[name] = []
            self.operations[name].append(op)
            self.current_operation = None
            self._log_operation(op)
    
    def _log_operation(self, op: OperationMetrics):
        """Log operation metrics."""
        logger.info(
            f"[Metrics] {op.operation_name}: "
            f"latency={op.latency_ms:.2f}ms, "
            f"tokens={op.tokens_used}, "
            f"cost=${op.cost_usd:.6f}, "
            f"api_calls={op.api_calls}"
        )
        if op.error:
            logger.error(f"[Metrics] {op.operation_name} error: {op.error}")
    
    def get_summary(self) -> Dict[str, Dict]:
        """Get summary statistics for all operations."""
        summary = {}
        for name, ops in self.operations.items():
            if not ops:
                continue
            
            latencies = [op.latency_ms for op in ops if op.end_time is not None]
            total_cost = sum(op.cost_usd for op in ops)
            total_tokens = sum(op.tokens_used for op in ops)
            total_api_calls = sum(op.api_calls for op in ops)
            errors = sum(1 for op in ops if op.error)
            
            summary[name] = {
                "count": len(ops),
                "total_cost_usd": total_cost,
                "total_tokens": total_tokens,
                "total_api_calls": total_api_calls,
                "errors": errors,
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
                "p95_latency_ms": self._percentile(latencies, 0.95) if latencies else 0.0,
                "p99_latency_ms": self._percentile(latencies, 0.99) if latencies else 0.0,
            }
        
        return summary
    
    @staticmethod
    def _percentile(values: list[float], pct: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        k = max(0, min(len(sorted_values) - 1, int(pct * len(sorted_values))))
        return sorted_values[k]
    
    def log_summary(self):
        """Log summary statistics."""
        summary = self.get_summary()
        logger.info("=== Metrics Summary ===")
        for name, stats in summary.items():
            logger.info(
                f"{name}: "
                f"count={stats['count']}, "
                f"total_cost=${stats['total_cost_usd']:.4f}, "
                f"avg_latency={stats['avg_latency_ms']:.2f}ms, "
                f"p95_latency={stats['p95_latency_ms']:.2f}ms, "
                f"errors={stats['errors']}"
            )


# Global metrics collector instance
_global_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _global_collector


def track_operation(name: str):
    """Convenience function to track an operation."""
    return _global_collector.track_operation(name)

