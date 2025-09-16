"""
Graph Monitoring and Metrics Service
Tracks performance, health, and usage of the Graphiti knowledge graph
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import logging
from collections import deque
from enum import Enum

from neo4j import AsyncGraphDatabase
import prometheus_client as prom
from ..core.comprehensive_logging import get_logger, get_metrics_logger

logger = get_logger("graph_monitoring")
metrics_logger = get_metrics_logger("graph_monitoring")


# Prometheus metrics
graph_nodes_total = prom.Gauge('graph_nodes_total', 'Total number of nodes in graph', ['node_type'])
graph_edges_total = prom.Gauge('graph_edges_total', 'Total number of edges in graph', ['edge_type'])
graph_query_duration = prom.Histogram('graph_query_duration_seconds', 'Graph query duration', ['query_type'])
graph_query_total = prom.Counter('graph_query_total', 'Total graph queries', ['query_type', 'status'])
graph_operations_total = prom.Counter('graph_operations_total', 'Total graph operations', ['operation', 'status'])
graph_memory_usage = prom.Gauge('graph_memory_usage_bytes', 'Graph database memory usage')
graph_disk_usage = prom.Gauge('graph_disk_usage_bytes', 'Graph database disk usage')


class MetricType(Enum):
    """Types of metrics to track"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class QueryMetric:
    """Metrics for a single query"""
    query_type: str
    duration: float
    nodes_returned: int
    success: bool
    timestamp: datetime
    error: Optional[str] = None


@dataclass
class HealthStatus:
    """Health status of the graph service"""
    is_healthy: bool
    neo4j_connected: bool
    graphiti_available: bool
    response_time: float
    node_count: int
    edge_count: int
    last_check: datetime
    errors: List[str]


class GraphMonitor:
    """
    Monitors the health and performance of the Graphiti knowledge graph
    """
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None,
                 check_interval: int = 30):
        """
        Initialize Graph Monitor
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            check_interval: Health check interval in seconds
        """
        import os
        
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = None
        self.check_interval = check_interval
        self.is_monitoring = False
        
        # Metrics storage
        self.query_metrics = deque(maxlen=1000)  # Keep last 1000 queries
        self.health_history = deque(maxlen=100)  # Keep last 100 health checks
        self.current_health = None
        
        # Performance thresholds
        self.thresholds = {
            "query_duration_warning": 1.0,  # seconds
            "query_duration_critical": 5.0,  # seconds
            "node_count_warning": 1000000,  # 1M nodes
            "node_count_critical": 10000000,  # 10M nodes
            "memory_usage_warning": 0.8,  # 80% of available
            "memory_usage_critical": 0.95  # 95% of available
        }
        
        logger.info("Graph Monitor initialized")
        
    async def start(self):
        """Start monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
            
        self.is_monitoring = True
        
        # Initialize driver
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        logger.info("Graph monitoring started")
        
    async def stop(self):
        """Stop monitoring"""
        self.is_monitoring = False
        
        if self.driver:
            await self.driver.close()
            
        logger.info("Graph monitoring stopped")
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Perform health check
                health = await self.check_health()
                self.current_health = health
                self.health_history.append(health)
                
                # Update Prometheus metrics
                await self._update_prometheus_metrics(health)
                
                # Check for alerts
                await self._check_alerts(health)
                
                # Log metrics
                metrics_logger.record_gauge("graph_health", 1.0 if health.is_healthy else 0.0)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
            # Wait for next check
            await asyncio.sleep(self.check_interval)
            
    async def check_health(self) -> HealthStatus:
        """Check the health of the graph database"""
        start_time = time.time()
        errors = []
        
        try:
            async with self.driver.session() as session:
                # Test connection
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                neo4j_connected = record and record["test"] == 1
                
                if not neo4j_connected:
                    errors.append("Neo4j connection test failed")
                
                # Get node count
                node_result = await session.run("""
                    MATCH (n)
                    RETURN count(n) as count, labels(n)[0] as type
                    ORDER BY count DESC
                """)
                
                node_count = 0
                async for record in node_result:
                    count = record["count"]
                    node_type = record["type"] or "unknown"
                    node_count += count
                    
                    # Update Prometheus metric
                    graph_nodes_total.labels(node_type=node_type).set(count)
                
                # Get edge count
                edge_result = await session.run("""
                    MATCH ()-[r]->()
                    RETURN count(r) as count, type(r) as type
                    ORDER BY count DESC
                """)
                
                edge_count = 0
                async for record in edge_result:
                    count = record["count"]
                    edge_type = record["type"] or "unknown"
                    edge_count += count
                    
                    # Update Prometheus metric
                    graph_edges_total.labels(edge_type=edge_type).set(count)
                
                # Check Graphiti availability
                graphiti_available = True  # Would need actual check
                
                response_time = time.time() - start_time
                
                # Determine overall health
                is_healthy = (
                    neo4j_connected and 
                    response_time < self.thresholds["query_duration_critical"] and
                    len(errors) == 0
                )
                
                return HealthStatus(
                    is_healthy=is_healthy,
                    neo4j_connected=neo4j_connected,
                    graphiti_available=graphiti_available,
                    response_time=response_time,
                    node_count=node_count,
                    edge_count=edge_count,
                    last_check=datetime.now(),
                    errors=errors
                )
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            errors.append(str(e))
            
            return HealthStatus(
                is_healthy=False,
                neo4j_connected=False,
                graphiti_available=False,
                response_time=time.time() - start_time,
                node_count=0,
                edge_count=0,
                last_check=datetime.now(),
                errors=errors
            )
            
    async def record_query(self, 
                          query_type: str,
                          duration: float,
                          nodes_returned: int = 0,
                          success: bool = True,
                          error: Optional[str] = None):
        """Record metrics for a query"""
        
        metric = QueryMetric(
            query_type=query_type,
            duration=duration,
            nodes_returned=nodes_returned,
            success=success,
            timestamp=datetime.now(),
            error=error
        )
        
        self.query_metrics.append(metric)
        
        # Update Prometheus metrics
        graph_query_duration.labels(query_type=query_type).observe(duration)
        graph_query_total.labels(
            query_type=query_type,
            status="success" if success else "failure"
        ).inc()
        
        # Log to metrics logger
        metrics_logger.record_timing(f"graph_query_{query_type}", duration)
        
        if not success:
            logger.warning(f"Query failed: {query_type}, error: {error}")
            
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the graph"""
        
        stats = {
            "health": asdict(self.current_health) if self.current_health else None,
            "performance": await self._get_performance_stats(),
            "usage": await self._get_usage_stats(),
            "alerts": await self._get_active_alerts()
        }
        
        return stats
        
    async def _get_performance_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        
        if not self.query_metrics:
            return {}
        
        # Calculate statistics from recent queries
        recent_queries = list(self.query_metrics)
        
        durations = [q.duration for q in recent_queries]
        success_count = sum(1 for q in recent_queries if q.success)
        
        stats = {
            "total_queries": len(recent_queries),
            "success_rate": success_count / len(recent_queries) if recent_queries else 0,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "p50_duration": self._percentile(durations, 50),
            "p95_duration": self._percentile(durations, 95),
            "p99_duration": self._percentile(durations, 99)
        }
        
        # Group by query type
        by_type = {}
        for query in recent_queries:
            if query.query_type not in by_type:
                by_type[query.query_type] = {
                    "count": 0,
                    "total_duration": 0,
                    "success_count": 0
                }
            
            by_type[query.query_type]["count"] += 1
            by_type[query.query_type]["total_duration"] += query.duration
            if query.success:
                by_type[query.query_type]["success_count"] += 1
        
        # Calculate averages by type
        for query_type, data in by_type.items():
            data["avg_duration"] = data["total_duration"] / data["count"]
            data["success_rate"] = data["success_count"] / data["count"]
            
        stats["by_query_type"] = by_type
        
        return stats
        
    async def _get_usage_stats(self) -> Dict[str, Any]:
        """Get database usage statistics"""
        
        try:
            async with self.driver.session() as session:
                # Get database size
                size_result = await session.run("""
                    CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes')
                    YIELD attributes
                    RETURN attributes
                """)
                
                size_record = await size_result.single()
                
                # Get memory usage
                memory_result = await session.run("""
                    CALL dbms.queryJmx('java.lang:type=Memory')
                    YIELD attributes
                    RETURN attributes
                """)
                
                memory_record = await memory_result.single()
                
                usage = {
                    "database_size": size_record["attributes"] if size_record else {},
                    "memory_usage": memory_record["attributes"] if memory_record else {},
                    "node_count": self.current_health.node_count if self.current_health else 0,
                    "edge_count": self.current_health.edge_count if self.current_health else 0
                }
                
                return usage
                
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {}
            
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        
        alerts = []
        
        if not self.current_health:
            return alerts
        
        # Check response time
        if self.current_health.response_time > self.thresholds["query_duration_critical"]:
            alerts.append({
                "level": "critical",
                "type": "response_time",
                "message": f"Response time critical: {self.current_health.response_time:.2f}s",
                "threshold": self.thresholds["query_duration_critical"]
            })
        elif self.current_health.response_time > self.thresholds["query_duration_warning"]:
            alerts.append({
                "level": "warning",
                "type": "response_time",
                "message": f"Response time high: {self.current_health.response_time:.2f}s",
                "threshold": self.thresholds["query_duration_warning"]
            })
        
        # Check node count
        if self.current_health.node_count > self.thresholds["node_count_critical"]:
            alerts.append({
                "level": "critical",
                "type": "node_count",
                "message": f"Node count critical: {self.current_health.node_count}",
                "threshold": self.thresholds["node_count_critical"]
            })
        elif self.current_health.node_count > self.thresholds["node_count_warning"]:
            alerts.append({
                "level": "warning",
                "type": "node_count",
                "message": f"Node count high: {self.current_health.node_count}",
                "threshold": self.thresholds["node_count_warning"]
            })
        
        # Check health errors
        if self.current_health.errors:
            alerts.append({
                "level": "critical",
                "type": "health_errors",
                "message": f"Health check errors: {', '.join(self.current_health.errors)}",
                "errors": self.current_health.errors
            })
        
        return alerts
        
    async def _check_alerts(self, health: HealthStatus):
        """Check for alert conditions and log them"""
        
        alerts = await self._get_active_alerts()
        
        for alert in alerts:
            if alert["level"] == "critical":
                logger.critical(f"ALERT: {alert['message']}")
            elif alert["level"] == "warning":
                logger.warning(f"WARNING: {alert['message']}")
                
    async def _update_prometheus_metrics(self, health: HealthStatus):
        """Update Prometheus metrics"""
        
        # Update memory and disk usage if available
        usage = await self._get_usage_stats()
        
        if usage.get("memory_usage"):
            memory_bytes = usage["memory_usage"].get("HeapMemoryUsage", {}).get("used", 0)
            graph_memory_usage.set(memory_bytes)
            
        if usage.get("database_size"):
            disk_bytes = usage["database_size"].get("TotalStoreSize", 0)
            graph_disk_usage.set(disk_bytes)
            
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0
            
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        
        if index >= len(sorted_values):
            return sorted_values[-1]
            
        return sorted_values[index]


class GraphMetricsDashboard:
    """
    Dashboard for visualizing graph metrics
    """
    
    def __init__(self, monitor: GraphMonitor):
        self.monitor = monitor
        
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        
        stats = await self.monitor.get_statistics()
        
        dashboard = {
            "status": {
                "health": "healthy" if stats["health"]["is_healthy"] else "unhealthy",
                "neo4j": "connected" if stats["health"]["neo4j_connected"] else "disconnected",
                "graphiti": "available" if stats["health"]["graphiti_available"] else "unavailable",
                "last_check": stats["health"]["last_check"].isoformat()
            },
            "metrics": {
                "nodes": stats["health"]["node_count"],
                "edges": stats["health"]["edge_count"],
                "queries": stats["performance"].get("total_queries", 0),
                "success_rate": f"{stats['performance'].get('success_rate', 0) * 100:.1f}%"
            },
            "performance": {
                "avg_response": f"{stats['performance'].get('avg_duration', 0):.3f}s",
                "p95_response": f"{stats['performance'].get('p95_duration', 0):.3f}s",
                "p99_response": f"{stats['performance'].get('p99_duration', 0):.3f}s"
            },
            "alerts": stats.get("alerts", []),
            "charts": {
                "query_distribution": self._get_query_distribution(),
                "response_time_trend": self._get_response_time_trend(),
                "health_history": self._get_health_history()
            }
        }
        
        return dashboard
        
    def _get_query_distribution(self) -> Dict[str, int]:
        """Get distribution of query types"""
        
        distribution = {}
        for metric in self.monitor.query_metrics:
            distribution[metric.query_type] = distribution.get(metric.query_type, 0) + 1
            
        return distribution
        
    def _get_response_time_trend(self) -> List[Dict[str, Any]]:
        """Get response time trend over time"""
        
        # Group by minute
        trend = []
        current_minute = None
        minute_data = []
        
        for metric in sorted(self.monitor.query_metrics, key=lambda x: x.timestamp):
            metric_minute = metric.timestamp.replace(second=0, microsecond=0)
            
            if current_minute != metric_minute:
                if minute_data:
                    trend.append({
                        "time": current_minute.isoformat(),
                        "avg_duration": sum(minute_data) / len(minute_data),
                        "count": len(minute_data)
                    })
                
                current_minute = metric_minute
                minute_data = [metric.duration]
            else:
                minute_data.append(metric.duration)
        
        # Add last minute
        if minute_data and current_minute:
            trend.append({
                "time": current_minute.isoformat(),
                "avg_duration": sum(minute_data) / len(minute_data),
                "count": len(minute_data)
            })
        
        return trend
        
    def _get_health_history(self) -> List[Dict[str, Any]]:
        """Get health check history"""
        
        history = []
        for health in self.monitor.health_history:
            history.append({
                "time": health.last_check.isoformat(),
                "healthy": health.is_healthy,
                "response_time": health.response_time,
                "node_count": health.node_count,
                "edge_count": health.edge_count
            })
        
        return history


# Monitoring decorator for graph operations
def monitor_graph_operation(operation_type: str):
    """Decorator to monitor graph operations"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                success = False
                error = str(e)
                raise
                
            finally:
                duration = time.time() - start_time
                
                # Record metrics
                graph_operations_total.labels(
                    operation=operation_type,
                    status="success" if success else "failure"
                ).inc()
                
                # Log to monitoring service if available
                # This would need to be connected to the actual monitor instance
                logger.info(f"Graph operation {operation_type}: {duration:.3f}s, success={success}")
                
        return wrapper
    return decorator


# Example usage
async def demo_monitoring():
    """Demonstrate graph monitoring"""
    
    # Initialize monitor
    monitor = GraphMonitor()
    
    # Start monitoring
    await monitor.start()
    
    # Simulate some queries
    await monitor.record_query("property_search", 0.5, nodes_returned=10, success=True)
    await monitor.record_query("relationship_traversal", 1.2, nodes_returned=25, success=True)
    await monitor.record_query("property_search", 0.3, nodes_returned=5, success=True)
    await monitor.record_query("complex_aggregation", 3.5, nodes_returned=100, success=False, error="Timeout")
    
    # Wait for health check
    await asyncio.sleep(2)
    
    # Get statistics
    stats = await monitor.get_statistics()
    print(f"Graph Statistics: {json.dumps(stats, indent=2, default=str)}")
    
    # Get dashboard data
    dashboard = GraphMetricsDashboard(monitor)
    dashboard_data = await dashboard.get_dashboard_data()
    print(f"Dashboard Data: {json.dumps(dashboard_data, indent=2, default=str)}")
    
    # Stop monitoring
    await monitor.stop()


if __name__ == "__main__":
    asyncio.run(demo_monitoring())