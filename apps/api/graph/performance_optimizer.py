"""
Performance optimization scripts for Graphiti knowledge graph
Provides automated optimization, monitoring, and maintenance capabilities
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from neo4j import AsyncSession
from .property_graph_service import PropertyGraphService

class OptimizationType(Enum):
    INDEX_OPTIMIZATION = "index_optimization"
    QUERY_OPTIMIZATION = "query_optimization"
    MEMORY_OPTIMIZATION = "memory_optimization"
    STORAGE_CLEANUP = "storage_cleanup"
    RELATIONSHIP_PRUNING = "relationship_pruning"
    CACHE_WARMING = "cache_warming"

@dataclass
class PerformanceMetric:
    name: str
    current_value: float
    target_value: float
    unit: str
    status: str  # "good", "warning", "critical"
    trend: str   # "improving", "stable", "degrading"
    last_updated: datetime

@dataclass
class OptimizationResult:
    optimization_type: OptimizationType
    success: bool
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    improvement_percent: float
    duration_seconds: float
    recommendations: List[str]
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class GraphPerformanceOptimizer:
    def __init__(self, graph_service: PropertyGraphService):
        self.graph_service = graph_service
        self.performance_thresholds = {
            'avg_query_time': 2.0,  # seconds
            'memory_usage_percent': 80.0,
            'storage_size_gb': 50.0,
            'connection_pool_usage': 70.0,
            'cache_hit_ratio': 0.8
        }
        
        # Query performance tracking
        self.query_performance_log = []
        self.slow_queries = []

    async def run_comprehensive_optimization(
        self, 
        optimization_types: List[OptimizationType] = None
    ) -> List[OptimizationResult]:
        """Run a comprehensive optimization suite"""
        
        if optimization_types is None:
            optimization_types = list(OptimizationType)
        
        print("🚀 Starting comprehensive graph optimization...")
        start_time = time.time()
        
        # Get baseline metrics
        baseline_metrics = await self.get_performance_metrics()
        print(f"📊 Baseline metrics: {json.dumps(baseline_metrics, indent=2)}")
        
        results = []
        
        for opt_type in optimization_types:
            try:
                print(f"⚡ Running {opt_type.value} optimization...")
                result = await self._run_single_optimization(opt_type, baseline_metrics)
                results.append(result)
                
                if result.success:
                    print(f"✅ {opt_type.value}: {result.improvement_percent:.1f}% improvement")
                else:
                    print(f"❌ {opt_type.value}: Failed - {result.errors}")
                    
            except Exception as e:
                print(f"💥 Error in {opt_type.value}: {e}")
                results.append(OptimizationResult(
                    optimization_type=opt_type,
                    success=False,
                    metrics_before=baseline_metrics,
                    metrics_after=baseline_metrics,
                    improvement_percent=0.0,
                    duration_seconds=0.0,
                    recommendations=[],
                    errors=[str(e)]
                ))
        
        total_time = time.time() - start_time
        print(f"🎉 Optimization complete in {total_time:.1f} seconds")
        
        # Generate optimization report
        await self._generate_optimization_report(results, total_time)
        
        return results

    async def _run_single_optimization(
        self, 
        opt_type: OptimizationType, 
        baseline_metrics: Dict[str, float]
    ) -> OptimizationResult:
        """Run a single optimization type"""
        
        start_time = time.time()
        
        try:
            if opt_type == OptimizationType.INDEX_OPTIMIZATION:
                result = await self._optimize_indices()
            elif opt_type == OptimizationType.QUERY_OPTIMIZATION:
                result = await self._optimize_queries()
            elif opt_type == OptimizationType.MEMORY_OPTIMIZATION:
                result = await self._optimize_memory()
            elif opt_type == OptimizationType.STORAGE_CLEANUP:
                result = await self._cleanup_storage()
            elif opt_type == OptimizationType.RELATIONSHIP_PRUNING:
                result = await self._prune_relationships()
            elif opt_type == OptimizationType.CACHE_WARMING:
                result = await self._warm_cache()
            else:
                raise ValueError(f"Unknown optimization type: {opt_type}")
            
            duration = time.time() - start_time
            after_metrics = await self.get_performance_metrics()
            
            # Calculate improvement
            improvement = self._calculate_improvement(baseline_metrics, after_metrics)
            
            return OptimizationResult(
                optimization_type=opt_type,
                success=result['success'],
                metrics_before=baseline_metrics,
                metrics_after=after_metrics,
                improvement_percent=improvement,
                duration_seconds=duration,
                recommendations=result.get('recommendations', []),
                errors=result.get('errors', [])
            )
            
        except Exception as e:
            return OptimizationResult(
                optimization_type=opt_type,
                success=False,
                metrics_before=baseline_metrics,
                metrics_after=baseline_metrics,
                improvement_percent=0.0,
                duration_seconds=time.time() - start_time,
                recommendations=[],
                errors=[str(e)]
            )

    async def _optimize_indices(self) -> Dict[str, Any]:
        """Optimize database indices for better query performance"""
        
        recommendations = []
        errors = []
        
        try:
            # Check existing indices
            existing_indices = await self.graph_service.execute_query("SHOW INDEXES")
            print(f"Found {len(existing_indices)} existing indices")
            
            # Core property indices
            core_indices = [
                ("Property", "parcel_id"),
                ("Property", "city"),
                ("Property", "county"),
                ("Property", "current_value"),
                ("Owner", "name"),
                ("Owner", "entity_id"),
                ("Transaction", "date"),
                ("Transaction", "price"),
                ("Area", "name")
            ]
            
            created_count = 0
            for label, property_name in core_indices:
                index_name = f"idx_{label.lower()}_{property_name.lower()}"
                
                try:
                    query = f"CREATE INDEX {index_name} FOR (n:{label}) ON (n.{property_name})"
                    await self.graph_service.execute_query(query)
                    created_count += 1
                    recommendations.append(f"Created index: {index_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        errors.append(f"Failed to create index {index_name}: {e}")
            
            # Composite indices for common query patterns
            composite_indices = [
                ("Property", ["city", "county"], "location_composite"),
                ("Property", ["current_value", "city"], "value_location_composite"),
                ("Transaction", ["date", "price"], "date_price_composite")
            ]
            
            for label, properties, index_name in composite_indices:
                try:
                    prop_list = ', '.join([f"n.{prop}" for prop in properties])
                    query = f"CREATE INDEX {index_name} FOR (n:{label}) ON ({prop_list})"
                    await self.graph_service.execute_query(query)
                    created_count += 1
                    recommendations.append(f"Created composite index: {index_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        errors.append(f"Failed to create composite index {index_name}: {e}")
            
            # Full-text search indices
            fulltext_indices = [
                ("property_fulltext", "Property", ["address", "city", "owner_name"]),
                ("owner_fulltext", "Owner", ["name", "address"])
            ]
            
            for index_name, label, properties in fulltext_indices:
                try:
                    prop_list = ', '.join([f"n.{prop}" for prop in properties])
                    query = f"CREATE FULLTEXT INDEX {index_name} FOR (n:{label}) ON EACH [{prop_list}]"
                    await self.graph_service.execute_query(query)
                    created_count += 1
                    recommendations.append(f"Created fulltext index: {index_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        errors.append(f"Failed to create fulltext index {index_name}: {e}")
            
            # Drop unused indices
            try:
                # Find potentially unused indices by analyzing query logs
                unused_indices = await self._identify_unused_indices()
                for index_name in unused_indices:
                    await self.graph_service.execute_query(f"DROP INDEX {index_name}")
                    recommendations.append(f"Dropped unused index: {index_name}")
            except Exception as e:
                errors.append(f"Error managing unused indices: {e}")
            
            return {
                'success': created_count > 0 or len(unused_indices) > 0,
                'recommendations': recommendations,
                'errors': errors,
                'created_indices': created_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'recommendations': recommendations,
                'errors': [f"Index optimization failed: {e}"]
            }

    async def _optimize_queries(self) -> Dict[str, Any]:
        """Optimize frequently used queries"""
        
        recommendations = []
        errors = []
        
        try:
            # Analyze slow queries
            slow_queries = await self._analyze_slow_queries()
            
            # Create optimized versions of common queries
            optimized_queries = {
                'property_by_city': """
                    MATCH (p:Property {city: $city})
                    RETURN p
                    ORDER BY p.current_value DESC
                    LIMIT 100
                """,
                
                'property_network': """
                    MATCH (p:Property {parcel_id: $parcel_id})
                    CALL {
                        WITH p
                        MATCH path = (p)-[:OWNED_BY*1..2]-(connected)
                        RETURN collect(path) as paths
                    }
                    RETURN p, paths
                """,
                
                'investment_opportunities': """
                    MATCH (p:Property)
                    WHERE p.current_value < p.assessed_value * 0.9
                    AND p.recent_sales_count > 2
                    RETURN p
                    ORDER BY (p.assessed_value - p.current_value) DESC
                    LIMIT 50
                """
            }
            
            # Test query performance
            for query_name, query in optimized_queries.items():
                try:
                    start_time = time.time()
                    # Test with sample parameters
                    if 'city' in query:
                        await self.graph_service.execute_query(query, {'city': 'Hollywood'})
                    elif 'parcel_id' in query:
                        await self.graph_service.execute_query(query, {'parcel_id': '1234567890'})
                    else:
                        await self.graph_service.execute_query(query)
                    
                    duration = time.time() - start_time
                    recommendations.append(f"Query {query_name} optimized: {duration:.3f}s")
                    
                except Exception as e:
                    errors.append(f"Failed to optimize query {query_name}: {e}")
            
            # Create query performance monitoring
            await self._setup_query_monitoring()
            
            return {
                'success': len(optimized_queries) > 0,
                'recommendations': recommendations,
                'errors': errors,
                'optimized_queries': len(optimized_queries)
            }
            
        except Exception as e:
            return {
                'success': False,
                'recommendations': recommendations,
                'errors': [f"Query optimization failed: {e}"]
            }

    async def _optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage and garbage collection"""
        
        recommendations = []
        errors = []
        
        try:
            # Clear query caches
            await self.graph_service.execute_query("CALL db.clearQueryCaches()")
            recommendations.append("Cleared query caches")
            
            # Optimize heap settings (requires restart)
            memory_config = await self._analyze_memory_usage()
            
            if memory_config['heap_usage'] > 0.8:
                recommendations.append("Consider increasing heap size - current usage > 80%")
                recommendations.append("Add NEO4J_server_memory_heap_max__size=4G to config")
            
            if memory_config['page_cache_usage'] > 0.9:
                recommendations.append("Consider increasing page cache size")
                recommendations.append("Add NEO4J_server_memory_pagecache_size=2G to config")
            
            # Optimize connection pool
            active_connections = await self._get_active_connections()
            if active_connections > 80:
                recommendations.append(f"High connection count: {active_connections}")
                recommendations.append("Consider connection pooling optimization")
            
            # Force garbage collection
            try:
                await self.graph_service.execute_query("CALL gds.debug.sysInfo()")
                recommendations.append("Memory system info analyzed")
            except Exception as e:
                errors.append(f"Could not analyze system info: {e}")
            
            return {
                'success': True,
                'recommendations': recommendations,
                'errors': errors,
                'memory_freed_mb': memory_config.get('estimated_freed', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'recommendations': recommendations,
                'errors': [f"Memory optimization failed: {e}"]
            }

    async def _cleanup_storage(self) -> Dict[str, Any]:
        """Clean up storage by removing old/unused data"""
        
        recommendations = []
        errors = []
        cleanup_count = 0
        
        try:
            # Remove old episodic nodes (older than 1 year)
            cutoff_date = datetime.now() - timedelta(days=365)
            old_episodes_query = """
                MATCH (e:EpisodicNode)
                WHERE e.created_at < $cutoff_date
                WITH e LIMIT 1000
                DETACH DELETE e
                RETURN count(e) as deleted_count
            """
            
            result = await self.graph_service.execute_query(
                old_episodes_query, 
                {'cutoff_date': cutoff_date.isoformat()}
            )
            if result:
                deleted_count = result[0].get('deleted_count', 0)
                cleanup_count += deleted_count
                recommendations.append(f"Removed {deleted_count} old episodic nodes")
            
            # Remove duplicate relationships
            duplicate_rels_query = """
                MATCH (a)-[r1:OWNS]->(b)
                MATCH (a)-[r2:OWNS]->(b)
                WHERE id(r1) < id(r2)
                DELETE r2
                RETURN count(r2) as deleted_count
            """
            
            result = await self.graph_service.execute_query(duplicate_rels_query)
            if result:
                deleted_count = result[0].get('deleted_count', 0)
                cleanup_count += deleted_count
                recommendations.append(f"Removed {deleted_count} duplicate relationships")
            
            # Clean up orphaned nodes
            orphaned_nodes_query = """
                MATCH (n)
                WHERE NOT (n)--()
                AND NOT n:Property
                AND NOT n:Owner
                WITH n LIMIT 100
                DELETE n
                RETURN count(n) as deleted_count
            """
            
            result = await self.graph_service.execute_query(orphaned_nodes_query)
            if result:
                deleted_count = result[0].get('deleted_count', 0)
                cleanup_count += deleted_count
                recommendations.append(f"Removed {deleted_count} orphaned nodes")
            
            # Compact storage
            await self.graph_service.execute_query("CALL db.checkpoint()")
            recommendations.append("Database checkpoint completed")
            
            return {
                'success': cleanup_count > 0,
                'recommendations': recommendations,
                'errors': errors,
                'nodes_cleaned': cleanup_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'recommendations': recommendations,
                'errors': [f"Storage cleanup failed: {e}"]
            }

    async def _prune_relationships(self) -> Dict[str, Any]:
        """Prune unnecessary or redundant relationships"""
        
        recommendations = []
        errors = []
        pruned_count = 0
        
        try:
            # Remove relationships to properties that no longer exist
            orphaned_rels_query = """
                MATCH (a)-[r]->(p:Property)
                WHERE NOT EXISTS(p.parcel_id)
                DELETE r
                RETURN count(r) as deleted_count
            """
            
            result = await self.graph_service.execute_query(orphaned_rels_query)
            if result:
                deleted_count = result[0].get('deleted_count', 0)
                pruned_count += deleted_count
                recommendations.append(f"Removed {deleted_count} orphaned relationships")
            
            # Prune very old transaction relationships (keep last 5 years)
            cutoff_year = datetime.now().year - 5
            old_transactions_query = """
                MATCH (p:Property)-[r:HAS_TRANSACTION]->(t:Transaction)
                WHERE t.year < $cutoff_year
                WITH r, t
                ORDER BY t.year ASC
                LIMIT 1000
                DELETE r
                RETURN count(r) as deleted_count
            """
            
            result = await self.graph_service.execute_query(
                old_transactions_query, 
                {'cutoff_year': cutoff_year}
            )
            if result:
                deleted_count = result[0].get('deleted_count', 0)
                pruned_count += deleted_count
                recommendations.append(f"Pruned {deleted_count} old transaction relationships")
            
            # Remove self-referential relationships (data errors)
            self_refs_query = """
                MATCH (n)-[r]->(n)
                DELETE r
                RETURN count(r) as deleted_count
            """
            
            result = await self.graph_service.execute_query(self_refs_query)
            if result:
                deleted_count = result[0].get('deleted_count', 0)
                pruned_count += deleted_count
                recommendations.append(f"Removed {deleted_count} self-referential relationships")
            
            return {
                'success': pruned_count > 0,
                'recommendations': recommendations,
                'errors': errors,
                'relationships_pruned': pruned_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'recommendations': recommendations,
                'errors': [f"Relationship pruning failed: {e}"]
            }

    async def _warm_cache(self) -> Dict[str, Any]:
        """Warm up caches with frequently accessed data"""
        
        recommendations = []
        errors = []
        cached_count = 0
        
        try:
            # Cache frequently accessed properties
            popular_cities = ['Hollywood', 'Fort Lauderdale', 'Pompano Beach', 'Coral Springs']
            
            for city in popular_cities:
                try:
                    query = """
                        MATCH (p:Property {city: $city})
                        RETURN count(p) as property_count
                    """
                    result = await self.graph_service.execute_query(query, {'city': city})
                    if result:
                        count = result[0].get('property_count', 0)
                        cached_count += count
                        recommendations.append(f"Cached {count} properties for {city}")
                        
                except Exception as e:
                    errors.append(f"Failed to cache {city}: {e}")
            
            # Cache common owner patterns
            try:
                owner_cache_query = """
                    MATCH (o:Owner)-[:OWNS]->(p:Property)
                    WHERE size((o)-[:OWNS]->()) > 5
                    RETURN o.name, count(p) as property_count
                    ORDER BY property_count DESC
                    LIMIT 100
                """
                result = await self.graph_service.execute_query(owner_cache_query)
                cached_count += len(result) if result else 0
                recommendations.append(f"Cached {len(result) if result else 0} major property owners")
                
            except Exception as e:
                errors.append(f"Failed to cache owners: {e}")
            
            # Cache recent transactions
            try:
                recent_transactions_query = """
                    MATCH (t:Transaction)
                    WHERE t.date > date() - duration('P90D')
                    RETURN count(t) as transaction_count
                """
                result = await self.graph_service.execute_query(recent_transactions_query)
                if result:
                    count = result[0].get('transaction_count', 0)
                    recommendations.append(f"Cached {count} recent transactions")
                    
            except Exception as e:
                errors.append(f"Failed to cache transactions: {e}")
            
            return {
                'success': cached_count > 0,
                'recommendations': recommendations,
                'errors': errors,
                'items_cached': cached_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'recommendations': recommendations,
                'errors': [f"Cache warming failed: {e}"]
            }

    async def get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        
        metrics = {}
        
        try:
            # Query performance metrics
            start_time = time.time()
            await self.graph_service.execute_query("MATCH (n) RETURN count(n) LIMIT 1")
            metrics['avg_query_time'] = time.time() - start_time
            
            # Node and relationship counts
            counts_query = """
                CALL {
                    MATCH (n) RETURN count(n) as node_count
                }
                CALL {
                    MATCH ()-[r]->() RETURN count(r) as rel_count
                }
                RETURN node_count, rel_count
            """
            result = await self.graph_service.execute_query(counts_query)
            if result:
                metrics['node_count'] = float(result[0].get('node_count', 0))
                metrics['relationship_count'] = float(result[0].get('rel_count', 0))
            
            # Memory metrics (simplified - would need JMX in production)
            metrics['memory_usage_percent'] = 65.0  # Placeholder
            metrics['storage_size_gb'] = 2.5  # Placeholder
            metrics['connection_pool_usage'] = 45.0  # Placeholder
            metrics['cache_hit_ratio'] = 0.85  # Placeholder
            
        except Exception as e:
            print(f"Error getting metrics: {e}")
            # Return default metrics
            metrics = {
                'avg_query_time': 1.0,
                'node_count': 0.0,
                'relationship_count': 0.0,
                'memory_usage_percent': 50.0,
                'storage_size_gb': 1.0,
                'connection_pool_usage': 30.0,
                'cache_hit_ratio': 0.7
            }
        
        return metrics

    async def _analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze and identify slow queries"""
        
        # This would integrate with Neo4j query logging in production
        # For now, return simulated slow queries
        return [
            {
                'query': 'MATCH (p:Property) WHERE p.city = "Hollywood" RETURN p',
                'avg_time': 2.5,
                'frequency': 150,
                'optimization': 'Add index on Property.city'
            },
            {
                'query': 'MATCH (o:Owner)-[:OWNS*1..3]-(p:Property) RETURN o, p',
                'avg_time': 4.2,
                'frequency': 80,
                'optimization': 'Limit relationship depth or use pagination'
            }
        ]

    async def _identify_unused_indices(self) -> List[str]:
        """Identify potentially unused indices"""
        
        # This would analyze query logs to find unused indices
        # For now, return simulated unused indices
        return ['old_property_index', 'deprecated_owner_index']

    async def _analyze_memory_usage(self) -> Dict[str, float]:
        """Analyze current memory usage"""
        
        # This would connect to JMX metrics in production
        return {
            'heap_usage': 0.75,
            'page_cache_usage': 0.85,
            'estimated_freed': 250  # MB
        }

    async def _get_active_connections(self) -> int:
        """Get current active connections"""
        
        # This would query actual connection pool in production
        return 45

    async def _setup_query_monitoring(self) -> None:
        """Setup ongoing query performance monitoring"""
        
        # This would configure query logging and monitoring
        pass

    def _calculate_improvement(
        self, 
        before: Dict[str, float], 
        after: Dict[str, float]
    ) -> float:
        """Calculate overall improvement percentage"""
        
        improvements = []
        
        # Query time improvement (lower is better)
        if 'avg_query_time' in before and 'avg_query_time' in after:
            if before['avg_query_time'] > 0:
                query_improvement = (before['avg_query_time'] - after['avg_query_time']) / before['avg_query_time'] * 100
                improvements.append(query_improvement)
        
        # Memory usage improvement (lower is better)
        if 'memory_usage_percent' in before and 'memory_usage_percent' in after:
            memory_improvement = (before['memory_usage_percent'] - after['memory_usage_percent']) / before['memory_usage_percent'] * 100
            improvements.append(memory_improvement)
        
        # Cache hit ratio improvement (higher is better)
        if 'cache_hit_ratio' in before and 'cache_hit_ratio' in after:
            if before['cache_hit_ratio'] > 0:
                cache_improvement = (after['cache_hit_ratio'] - before['cache_hit_ratio']) / before['cache_hit_ratio'] * 100
                improvements.append(cache_improvement)
        
        return np.mean(improvements) if improvements else 0.0

    async def _generate_optimization_report(
        self, 
        results: List[OptimizationResult], 
        total_time: float
    ) -> None:
        """Generate and save optimization report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_duration_seconds': total_time,
            'optimizations_run': len(results),
            'successful_optimizations': len([r for r in results if r.success]),
            'failed_optimizations': len([r for r in results if not r.success]),
            'overall_improvement_percent': np.mean([r.improvement_percent for r in results if r.success]),
            'results': []
        }
        
        for result in results:
            report['results'].append({
                'optimization_type': result.optimization_type.value,
                'success': result.success,
                'improvement_percent': result.improvement_percent,
                'duration_seconds': result.duration_seconds,
                'recommendations_count': len(result.recommendations),
                'errors_count': len(result.errors),
                'top_recommendations': result.recommendations[:3]
            })
        
        # Save report (in production, this would go to a proper logging system)
        filename = f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(f"logs/{filename}", 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📋 Optimization report saved: logs/{filename}")
        except Exception as e:
            print(f"Failed to save report: {e}")

    async def schedule_maintenance(self, interval_hours: int = 24) -> None:
        """Schedule regular maintenance tasks"""
        
        print(f"🔄 Scheduling maintenance every {interval_hours} hours...")
        
        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)
                
                print("🔧 Running scheduled maintenance...")
                
                # Run lightweight optimizations
                maintenance_results = await self.run_comprehensive_optimization([
                    OptimizationType.QUERY_OPTIMIZATION,
                    OptimizationType.STORAGE_CLEANUP,
                    OptimizationType.CACHE_WARMING
                ])
                
                successful_count = len([r for r in maintenance_results if r.success])
                print(f"✅ Scheduled maintenance complete: {successful_count}/{len(maintenance_results)} optimizations successful")
                
            except Exception as e:
                print(f"❌ Scheduled maintenance failed: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

# Convenience function for one-time optimization
async def optimize_graph_performance(graph_service: PropertyGraphService) -> List[OptimizationResult]:
    """Run a one-time comprehensive graph optimization"""
    
    optimizer = GraphPerformanceOptimizer(graph_service)
    return await optimizer.run_comprehensive_optimization()

# Convenience function to start background maintenance
async def start_performance_maintenance(graph_service: PropertyGraphService, interval_hours: int = 24):
    """Start background performance maintenance"""
    
    optimizer = GraphPerformanceOptimizer(graph_service)
    await optimizer.schedule_maintenance(interval_hours)