"""
Query optimization system for efficient data access.

This module provides Automated query optimization:
- Query analysis and optimization
- Query caching and memoization
- Batch query execution
- Query result optimization
- Database query optimization
"""

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union, Tuple, Set
import threading
from collections import defaultdict, OrderedDict
from functools import wraps
import weakref

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    AGGREGATE = "aggregate"
    JOIN = "join"
    SEARCH = "search"


class OptimizationLevel(Enum):
    """Query optimization levels."""
    NONE = "none"
    BASIC = "basic"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    execution_time: float
    result_size: int
    cache_hit: bool
    optimization_applied: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


@dataclass
class QueryPlan:
    """Query execution plan."""
    query_id: str
    query_type: QueryType
    estimated_cost: float
    estimated_rows: int
    optimizations: List[str] = field(default_factory=list)
    cache_key: Optional[str] = None
    batch_group: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)


@dataclass
class BatchQuery:
    """Batch query container."""
    queries: List[Tuple[str, Dict[str, Any]]]
    batch_id: str
    query_type: QueryType
    created_at: datetime = field(default_factory=datetime.now)
    max_batch_size: int = 100
    timeout: float = 30.0


class QueryOptimizer(ABC):
    """Abstract base class for query optimizers."""
    
    @abstractmethod
    async def optimize_query(self, query: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Optimize a single query."""
        pass
    
    @abstractmethod
    async def analyze_query(self, query: str, params: Dict[str, Any]) -> QueryPlan:
        """Analyze query and create execution plan."""
        pass
    
    @abstractmethod
    async def batch_optimize(self, queries: List[Tuple[str, Dict[str, Any]]]) -> List[BatchQuery]:
        """Optimize multiple queries for batch execution."""
        pass


class SQLQueryOptimizer(QueryOptimizer):
    """SQL query optimizer."""
    
    def __init__(self):
        self.optimization_rules: List[Callable] = []
        self.query_patterns: Dict[str, str] = {}
        self.index_suggestions: Dict[str, List[str]] = defaultdict(list)
    
    async def optimize_query(self, query: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Optimize SQL query."""
        optimized_query = query
        optimized_params = params.copy()
        
        # Apply optimization rules
        for rule in self.optimization_rules:
            try:
                optimized_query, optimized_params = await rule(optimized_query, optimized_params)
            except Exception as e:
                logger.error(f"Error applying optimization rule: {e}")
        
        return optimized_query, optimized_params
    
    async def analyze_query(self, query: str, params: Dict[str, Any]) -> QueryPlan:
        """Analyze SQL query."""
        query_id = self._generate_query_id(query, params)
        query_type = self._detect_query_type(query)
        
        # Estimate cost (simplified)
        estimated_cost = self._estimate_query_cost(query, params)
        estimated_rows = self._estimate_result_size(query, params)
        
        # Suggest optimizations
        optimizations = await self._suggest_optimizations(query, params)
        
        return QueryPlan(
            query_id=query_id,
            query_type=query_type,
            estimated_cost=estimated_cost,
            estimated_rows=estimated_rows,
            optimizations=optimizations,
            cache_key=self._generate_cache_key(query, params)
        )
    
    async def batch_optimize(self, queries: List[Tuple[str, Dict[str, Any]]]) -> List[BatchQuery]:
        """Optimize queries for batch execution."""
        # Group queries by type and similarity
        query_groups = defaultdict(list)
        
        for query, params in queries:
            query_type = self._detect_query_type(query)
            group_key = f"{query_type.value}_{self._get_table_names(query)}"
            query_groups[group_key].append((query, params))
        
        batch_queries = []
        for group_key, group_queries in query_groups.items():
            # Split large groups into smaller batches
            for i in range(0, len(group_queries), 100):
                batch = group_queries[i:i+100]
                batch_id = f"{group_key}_{i//100}"
                query_type = self._detect_query_type(batch[0][0])
                
                batch_queries.append(BatchQuery(
                    queries=batch,
                    batch_id=batch_id,
                    query_type=query_type
                ))
        
        return batch_queries
    
    def add_optimization_rule(self, rule: Callable) -> None:
        """Add a query optimization rule."""
        self.optimization_rules.append(rule)
    
    def add_query_pattern(self, pattern: str, optimized: str) -> None:
        """Add a query optimization pattern."""
        self.query_patterns[pattern] = optimized
    
    def _generate_query_id(self, query: str, params: Dict[str, Any]) -> str:
        """Generate unique query ID."""
        query_hash = hashlib.md5(f"{query}{str(params)}".encode()).hexdigest()
        return f"query_{query_hash[:8]}"
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detect query type from SQL."""
        query_lower = query.lower().strip()
        
        if query_lower.startswith('select'):
            if 'group by' in query_lower or 'count(' in query_lower:
                return QueryType.AGGREGATE
            elif 'join' in query_lower:
                return QueryType.JOIN
            else:
                return QueryType.SELECT
        elif query_lower.startswith('insert'):
            return QueryType.INSERT
        elif query_lower.startswith('update'):
            return QueryType.UPDATE
        elif query_lower.startswith('delete'):
            return QueryType.DELETE
        else:
            return QueryType.SELECT
    
    def _estimate_query_cost(self, query: str, params: Dict[str, Any]) -> float:
        """Estimate query execution cost."""
        # Simplified cost estimation
        cost = 1.0
        
        # Higher cost for joins
        if 'join' in query.lower():
            cost *= 2.0
        
        # Higher cost for complex WHERE clauses
        where_count = query.lower().count('where')
        cost *= (1.0 + where_count * 0.5)
        
        # Higher cost for ORDER BY
        if 'order by' in query.lower():
            cost *= 1.5
        
        return cost
    
    def _estimate_result_size(self, query: str, params: Dict[str, Any]) -> int:
        """Estimate result set size."""
        # Simplified estimation
        if 'limit' in query.lower():
            # Try to extract limit value
            import re
            limit_match = re.search(r'limit\s+(\d+)', query.lower())
            if limit_match:
                return int(limit_match.group(1))
        
        # Default estimate
        return 100
    
    async def _suggest_optimizations(self, query: str, params: Dict[str, Any]) -> List[str]:
        """Suggest query optimizations."""
        suggestions = []
        query_lower = query.lower()
        
        # Check for missing indexes
        if 'where' in query_lower and 'index' not in query_lower:
            suggestions.append("consider_adding_index")
        
        # Check for SELECT *
        if 'select *' in query_lower:
            suggestions.append("specify_columns")
        
        # Check for unnecessary ORDER BY
        if 'order by' in query_lower and 'limit' not in query_lower:
            suggestions.append("remove_unnecessary_order_by")
        
        return suggestions
    
    def _get_table_names(self, query: str) -> str:
        """Extract table names from query."""
        # Simplified table name extraction
        import re
        
        # Look for FROM and JOIN clauses
        tables = set()
        
        from_match = re.search(r'from\s+(\w+)', query.lower())
        if from_match:
            tables.add(from_match.group(1))
        
        join_matches = re.findall(r'join\s+(\w+)', query.lower())
        tables.update(join_matches)
        
        return '_'.join(sorted(tables))
    
    def _generate_cache_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key for query."""
        import json
        key_data = {"query": query, "params": params}
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()


class NoSQLQueryOptimizer(QueryOptimizer):
    """NoSQL query optimizer."""
    
    def __init__(self):
        self.aggregation_pipeline_cache: Dict[str, List[Dict]] = {}
        self.index_hints: Dict[str, List[str]] = defaultdict(list)
    
    async def optimize_query(self, query: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Optimize NoSQL query."""
        # For NoSQL, query might be a JSON object or aggregation pipeline
        optimized_query = query
        optimized_params = params.copy()
        
        # Apply NoSQL-specific optimizations
        if self._is_aggregation_pipeline(query):
            optimized_query = await self._optimize_aggregation_pipeline(query)
        
        return optimized_query, optimized_params
    
    async def analyze_query(self, query: str, params: Dict[str, Any]) -> QueryPlan:
        """Analyze NoSQL query."""
        query_id = hashlib.md5(f"{query}{str(params)}".encode()).hexdigest()[:8]
        
        # Determine query type
        query_type = self._detect_nosql_query_type(query, params)
        
        # Estimate cost and size
        estimated_cost = self._estimate_nosql_cost(query, params)
        estimated_rows = params.get('limit', 100)
        
        return QueryPlan(
            query_id=query_id,
            query_type=query_type,
            estimated_cost=estimated_cost,
            estimated_rows=estimated_rows,
            cache_key=hashlib.md5(f"{query}{str(params)}".encode()).hexdigest()
        )
    
    async def batch_optimize(self, queries: List[Tuple[str, Dict[str, Any]]]) -> List[BatchQuery]:
        """Optimize NoSQL queries for batch execution."""
        # Group by collection and operation type
        query_groups = defaultdict(list)
        
        for query, params in queries:
            collection = params.get('collection', 'default')
            operation = params.get('operation', 'find')
            group_key = f"{collection}_{operation}"
            query_groups[group_key].append((query, params))
        
        batch_queries = []
        for group_key, group_queries in query_groups.items():
            batch_id = f"nosql_{group_key}_{int(time.time())}"
            batch_queries.append(BatchQuery(
                queries=group_queries,
                batch_id=batch_id,
                query_type=QueryType.SELECT
            ))
        
        return batch_queries
    
    def _is_aggregation_pipeline(self, query: str) -> bool:
        """Check if query is an aggregation pipeline."""
        try:
            import json
            parsed = json.loads(query)
            return isinstance(parsed, list) and all(isinstance(stage, dict) for stage in parsed)
        except:
            return False
    
    async def _optimize_aggregation_pipeline(self, pipeline: str) -> str:
        """Optimize aggregation pipeline."""
        try:
            import json
            stages = json.loads(pipeline)
            
            # Move $match stages as early as possible
            match_stages = [stage for stage in stages if '$match' in stage]
            other_stages = [stage for stage in stages if '$match' not in stage]
            
            optimized = match_stages + other_stages
            return json.dumps(optimized)
        
        except Exception as e:
            logger.error(f"Error optimizing aggregation pipeline: {e}")
            return pipeline
    
    def _detect_nosql_query_type(self, query: str, params: Dict[str, Any]) -> QueryType:
        """Detect NoSQL query type."""
        operation = params.get('operation', 'find')
        
        if operation in ['find', 'findOne']:
            return QueryType.SELECT
        elif operation in ['aggregate']:
            return QueryType.AGGREGATE
        elif operation in ['insertOne', 'insertMany']:
            return QueryType.INSERT
        elif operation in ['updateOne', 'updateMany']:
            return QueryType.UPDATE
        elif operation in ['deleteOne', 'deleteMany']:
            return QueryType.DELETE
        else:
            return QueryType.SELECT
    
    def _estimate_nosql_cost(self, query: str, params: Dict[str, Any]) -> float:
        """Estimate NoSQL query cost."""
        cost = 1.0
        
        # Higher cost for aggregation
        if params.get('operation') == 'aggregate':
            cost *= 3.0
        
        # Higher cost for large limits
        limit = params.get('limit', 100)
        if limit > 1000:
            cost *= 2.0
        
        return cost


class QueryCache:
    """Query result caching system."""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        enable_compression: bool = True
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        
        self.cache: OrderedDict = OrderedDict()
        self.cache_metadata: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    async def get(self, cache_key: str) -> Optional[Any]:
        """Get cached query result."""
        with self._lock:
            if cache_key not in self.cache:
                return None
            
            metadata = self.cache_metadata.get(cache_key, {})
            
            # Check TTL
            if self._is_expired(metadata):
                del self.cache[cache_key]
                del self.cache_metadata[cache_key]
                return None
            
            # Move to end (LRU)
            self.cache.move_to_end(cache_key)
            
            # Update access info
            metadata['last_accessed'] = datetime.now()
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            
            result = self.cache[cache_key]
            
            # Decompress if needed
            if self.enable_compression and metadata.get('compressed'):
                result = await self._decompress(result)
            
            return result
    
    async def set(
        self,
        cache_key: str,
        result: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Cache query result."""
        with self._lock:
            # Compress if enabled
            cached_result = result
            compressed = False
            
            if self.enable_compression:
                try:
                    cached_result = await self._compress(result)
                    compressed = True
                except Exception as e:
                    logger.error(f"Error compressing cache entry: {e}")
            
            # Store result
            self.cache[cache_key] = cached_result
            self.cache.move_to_end(cache_key)
            
            # Store metadata
            self.cache_metadata[cache_key] = {
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'ttl': ttl or self.default_ttl,
                'access_count': 0,
                'compressed': compressed,
                'size_bytes': len(str(cached_result))
            }
            
            # Trim cache if necessary
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.cache_metadata[oldest_key]
    
    def invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries."""
        with self._lock:
            if pattern is None:
                count = len(self.cache)
                self.cache.clear()
                self.cache_metadata.clear()
                return count
            
            import fnmatch
            keys_to_remove = [
                key for key in self.cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_remove:
                del self.cache[key]
                del self.cache_metadata[key]
            
            return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_size = sum(
                metadata.get('size_bytes', 0)
                for metadata in self.cache_metadata.values()
            )
            
            return {
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'total_size_bytes': total_size,
                'hit_ratio': self._calculate_hit_ratio(),
                'compressed_entries': sum(
                    1 for metadata in self.cache_metadata.values()
                    if metadata.get('compressed', False)
                )
            }
    
    def _is_expired(self, metadata: Dict) -> bool:
        """Check if cache entry is expired."""
        if 'created_at' not in metadata or 'ttl' not in metadata:
            return True
        
        created_at = metadata['created_at']
        ttl = metadata['ttl']
        
        return (datetime.now() - created_at).total_seconds() > ttl
    
    async def _compress(self, data: Any) -> bytes:
        """Compress data."""
        import pickle
        import gzip
        
        pickled = pickle.dumps(data)
        return gzip.compress(pickled)
    
    async def _decompress(self, data: bytes) -> Any:
        """Decompress data."""
        import pickle
        import gzip
        
        decompressed = gzip.decompress(data)
        return pickle.loads(decompressed)
    
    def _calculate_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        # This would need to be tracked separately in a real implementation
        return 0.0


class BatchQueryExecutor:
    """Batch query execution system."""
    
    def __init__(
        self,
        executor_function: Callable,
        max_batch_size: int = 100,
        batch_timeout: float = 1.0
    ):
        self.executor_function = executor_function
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        
        self.pending_queries: Dict[str, List] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self._lock = threading.RLock()
    
    async def execute_query(
        self,
        query: str,
        params: Dict[str, Any],
        batch_key: Optional[str] = None
    ) -> Any:
        """Execute query with batching."""
        if batch_key is None:
            # Execute immediately
            return await self.executor_function(query, params)
        
        # Add to batch
        future = asyncio.Future()
        
        with self._lock:
            self.pending_queries[batch_key].append((query, params, future))
            
            # Start batch timer if this is the first query
            if len(self.pending_queries[batch_key]) == 1:
                self.batch_timers[batch_key] = asyncio.create_task(
                    self._batch_timer(batch_key)
                )
            
            # Execute batch if it's full
            if len(self.pending_queries[batch_key]) >= self.max_batch_size:
                await self._execute_batch(batch_key)
        
        return await future
    
    async def _batch_timer(self, batch_key: str) -> None:
        """Timer for batch execution."""
        try:
            await asyncio.sleep(self.batch_timeout)
            await self._execute_batch(batch_key)
        except asyncio.CancelledError:
            pass
    
    async def _execute_batch(self, batch_key: str) -> None:
        """Execute a batch of queries."""
        with self._lock:
            if batch_key not in self.pending_queries:
                return
            
            queries = self.pending_queries[batch_key]
            if not queries:
                return
            
            # Clear pending queries
            del self.pending_queries[batch_key]
            
            # Cancel timer
            if batch_key in self.batch_timers:
                self.batch_timers[batch_key].cancel()
                del self.batch_timers[batch_key]
        
        try:
            # Execute batch
            results = await self.executor_function([
                (query, params) for query, params, _ in queries
            ])
            
            # Resolve futures
            for i, (_, _, future) in enumerate(queries):
                if i < len(results):
                    future.set_result(results[i])
                else:
                    future.set_exception(RuntimeError("Batch execution failed"))
        
        except Exception as e:
            # Reject all futures
            for _, _, future in queries:
                future.set_exception(e)


class ConfigurableQueryEngine:
    """Configurable query engine with optimization and caching."""
    
    def __init__(
        self,
        optimizer: QueryOptimizer,
        cache: Optional[QueryCache] = None,
        batch_executor: Optional[BatchQueryExecutor] = None
    ):
        self.optimizer = optimizer
        self.cache = cache or QueryCache()
        self.batch_executor = batch_executor
        
        self.query_metrics: Dict[str, List[QueryMetrics]] = defaultdict(list)
        self.optimization_stats: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    async def execute_query(
        self,
        query: str,
        params: Dict[str, Any],
        use_cache: bool = True,
        use_batch: bool = False,
        batch_key: Optional[str] = None
    ) -> Any:
        """Execute query with optimization and caching."""
        start_time = time.time()
        
        # Generate cache key
        cache_key = hashlib.md5(f"{query}{str(params)}".encode()).hexdigest()
        
        # Try cache first
        if use_cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                self._record_metrics(cache_key, time.time() - start_time, 0, True)
                return cached_result
        
        try:
            # Optimize query
            optimized_query, optimized_params = await self.optimizer.optimize_query(query, params)
            self.optimization_stats['optimized_queries'] += 1
            
            # Execute query
            if use_batch and self.batch_executor:
                result = await self.batch_executor.execute_query(
                    optimized_query, 
                    optimized_params, 
                    batch_key
                )
            else:
                # This would be your actual query execution function
                result = await self._execute_raw_query(optimized_query, optimized_params)
            
            # Cache result
            if use_cache:
                await self.cache.set(cache_key, result)
            
            # Record metrics
            execution_time = time.time() - start_time
            result_size = len(result) if isinstance(result, (list, tuple)) else 1
            self._record_metrics(cache_key, execution_time, result_size, False)
            
            return result
        
        except Exception as e:
            self._record_metrics(cache_key, time.time() - start_time, 0, False, str(e))
            raise
    
    async def _execute_raw_query(self, query: str, params: Dict[str, Any]) -> Any:
        """Execute raw query - implement based on your data source."""
        # This is a placeholder - implement based on your specific data source
        await asyncio.sleep(0.1)  # Simulate query execution
        return []
    
    def _record_metrics(
        self,
        query_id: str,
        execution_time: float,
        result_size: int,
        cache_hit: bool,
        error: Optional[str] = None
    ) -> None:
        """Record query execution metrics."""
        metrics = QueryMetrics(
            execution_time=execution_time,
            result_size=result_size,
            cache_hit=cache_hit,
            error=error
        )
        
        with self._lock:
            self.query_metrics[query_id].append(metrics)
            
            # Keep only recent metrics
            if len(self.query_metrics[query_id]) > 100:
                self.query_metrics[query_id] = self.query_metrics[query_id][-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        with self._lock:
            all_metrics = []
            for metrics_list in self.query_metrics.values():
                all_metrics.extend(metrics_list)
            
            if not all_metrics:
                return {"total_queries": 0}
            
            cache_hits = sum(1 for m in all_metrics if m.cache_hit)
            errors = sum(1 for m in all_metrics if m.error)
            
            execution_times = [m.execution_time for m in all_metrics if not m.error]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            return {
                "total_queries": len(all_metrics),
                "cache_hit_ratio": cache_hits / len(all_metrics),
                "error_rate": errors / len(all_metrics),
                "average_execution_time": avg_execution_time,
                "optimization_stats": dict(self.optimization_stats),
                "cache_stats": self.cache.get_stats()
            }


# Utility functions for common optimization patterns

def create_sql_optimization_rules() -> List[Callable]:
    """Create common SQL optimization rules."""
    
    async def remove_select_star(query: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Replace SELECT * with specific columns if possible."""
        if 'select *' in query.lower() and 'columns' in params:
            columns = ', '.join(params['columns'])
            optimized_query = query.replace('SELECT *', f'SELECT {columns}')
            optimized_query = optimized_query.replace('select *', f'select {columns}')
            return optimized_query, params
        return query, params
    
    async def add_limit_if_missing(query: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Add LIMIT clause if missing."""
        if 'limit' not in query.lower() and params.get('auto_limit', False):
            limit = params.get('default_limit', 100)
            optimized_query = f"{query} LIMIT {limit}"
            return optimized_query, params
        return query, params
    
    return [remove_select_star, add_limit_if_missing]


def query_cache_decorator(cache: QueryCache, ttl: Optional[int] = None):
    """Decorator for caching query results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            import json
            cache_key = hashlib.md5(
                json.dumps({"args": args, "kwargs": kwargs}, default=str, sort_keys=True).encode()
            ).hexdigest()
            
            # Try cache first
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
