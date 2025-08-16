"""
Dashboard optimization system.

This module provides comprehensive performance optimization:
- Lazy loading for components and data
- Automated data pagination
- Query optimization and caching
- Resource management and allocation
"""

from .lazy_loader import (
    LazyLoader,
    ComponentLazyLoader,
    DataLazyLoader,
    ModuleLazyLoader,
    LoadableItem,
    LoadingState,
    LoadingPriority,
    LazyLoadStrategy,
    OnDemandStrategy,
    ViewportStrategy,
    PredictiveStrategy,
    lazy_load
)

from .data_pagination import (
    PaginationParams,
    PaginationResult,
    VirtualWindow,
    PaginationStrategy,
    SortDirection,
    PaginationProvider,
    OffsetLimitProvider,
    CursorBasedProvider,
    VirtualScrollProvider,
    AdaptivePaginator,
    ConfigurablePaginator,
    create_database_paginator,
    create_api_paginator
)

from .query_optimizer import (
    QueryOptimizer,
    SQLQueryOptimizer,
    NoSQLQueryOptimizer,
    QueryCache,
    BatchQueryExecutor,
    ConfigurableQueryEngine,
    QueryType,
    QueryPlan,
    QueryMetrics,
    BatchQuery,
    OptimizationLevel,
    create_sql_optimization_rules,
    query_cache_decorator
)

from .resource_manager import (
    ResourceManager,
    GlobalResourceManager,
    CPUManager,
    MemoryManager,
    ThreadPoolManager,
    ConnectionPoolManager,
    ResourceType,
    ResourceQuota,
    ResourceUsage,
    ResourceAllocation,
    PriorityLevel,
    ResourceContext,
    create_resource_allocation
)

__all__ = [
    # Lazy loading
    'LazyLoader',
    'ComponentLazyLoader',
    'DataLazyLoader',
    'ModuleLazyLoader',
    'LoadableItem',
    'LoadingState',
    'LoadingPriority',
    'LazyLoadStrategy',
    'OnDemandStrategy',
    'ViewportStrategy',
    'PredictiveStrategy',
    'lazy_load',
    
    # Data pagination
    'PaginationParams',
    'PaginationResult',
    'VirtualWindow',
    'PaginationStrategy',
    'SortDirection',
    'PaginationProvider',
    'OffsetLimitProvider',
    'CursorBasedProvider',
    'VirtualScrollProvider',
    'AdaptivePaginator',
    'ConfigurablePaginator',
    'create_database_paginator',
    'create_api_paginator',
    
    # Query optimization
    'QueryOptimizer',
    'SQLQueryOptimizer',
    'NoSQLQueryOptimizer',
    'QueryCache',
    'BatchQueryExecutor',
    'ConfigurableQueryEngine',
    'QueryType',
    'QueryPlan',
    'QueryMetrics',
    'BatchQuery',
    'OptimizationLevel',
    'create_sql_optimization_rules',
    'query_cache_decorator',
    
    # Resource management
    'ResourceManager',
    'GlobalResourceManager',
    'CPUManager',
    'MemoryManager',
    'ThreadPoolManager',
    'ConnectionPoolManager',
    'ResourceType',
    'ResourceQuota',
    'ResourceUsage',
    'ResourceAllocation',
    'PriorityLevel',
    'ResourceContext',
    'create_resource_allocation'
]
