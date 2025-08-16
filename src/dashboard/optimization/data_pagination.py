"""
Data pagination system for efficient large dataset handling.

This module provides Automated pagination strategies:
- Virtual scrolling for large lists
- Progressive data loading
- Cursor-based pagination
- Adaptive page sizing
- Data windowing and buffering
"""

import asyncio
import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union, Tuple, Generic, TypeVar
import threading
from collections import deque, OrderedDict

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PaginationStrategy(Enum):
    """Pagination strategies."""
    OFFSET_LIMIT = "offset_limit"
    CURSOR_BASED = "cursor_based"
    SEEK_PAGINATE = "seek_paginate"
    VIRTUAL_SCROLL = "virtual_scroll"
    ADAPTIVE = "adaptive"


class SortDirection(Enum):
    """Sort directions."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 20
    offset: int = 0
    cursor: Optional[str] = None
    sort_by: Optional[str] = None
    sort_direction: SortDirection = SortDirection.ASC
    filters: Dict[str, Any] = field(default_factory=dict)
    search: Optional[str] = None


@dataclass
class PaginationResult(Generic[T]):
    """Pagination result container."""
    data: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def start_index(self) -> int:
        """Get starting index of current page."""
        return (self.page - 1) * self.page_size
    
    @property
    def end_index(self) -> int:
        """Get ending index of current page."""
        return min(self.start_index + self.page_size, self.total_count)


@dataclass
class VirtualWindow:
    """Virtual scrolling window."""
    start_index: int
    end_index: int
    buffer_size: int
    item_height: float
    container_height: float
    
    @property
    def visible_count(self) -> int:
        """Number of visible items."""
        return self.end_index - self.start_index
    
    @property
    def total_height(self) -> float:
        """Total virtual height."""
        return self.visible_count * self.item_height


class PaginationProvider(ABC, Generic[T]):
    """Abstract base class for pagination providers."""
    
    @abstractmethod
    async def fetch_page(self, params: PaginationParams) -> PaginationResult[T]:
        """Fetch a page of data."""
        pass
    
    @abstractmethod
    async def get_total_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Get total count of items."""
        pass
    
    @abstractmethod
    async def search(self, query: str, params: PaginationParams) -> PaginationResult[T]:
        """Search with pagination."""
        pass


class OffsetLimitProvider(PaginationProvider[T]):
    """Offset/limit based pagination provider."""
    
    def __init__(self, data_source: Callable, count_source: Optional[Callable] = None):
        self.data_source = data_source
        self.count_source = count_source or self._default_count_source
    
    async def fetch_page(self, params: PaginationParams) -> PaginationResult[T]:
        """Fetch page using offset/limit."""
        offset = params.offset or (params.page - 1) * params.page_size
        
        # Fetch data
        data = await self.data_source(
            offset=offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_direction=params.sort_direction.value,
            filters=params.filters,
            search=params.search
        )
        
        # Get total count
        total_count = await self.get_total_count(params.filters)
        total_pages = math.ceil(total_count / params.page_size)
        
        return PaginationResult(
            data=data,
            total_count=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )
    
    async def get_total_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Get total count."""
        return await self.count_source(filters=filters or {})
    
    async def search(self, query: str, params: PaginationParams) -> PaginationResult[T]:
        """Search with pagination."""
        params.search = query
        return await self.fetch_page(params)
    
    async def _default_count_source(self, filters: Dict[str, Any]) -> int:
        """Default count source that fetches all data."""
        data = await self.data_source(
            offset=0,
            limit=None,
            filters=filters
        )
        return len(data) if data else 0


class CursorBasedProvider(PaginationProvider[T]):
    """Cursor-based pagination provider for large datasets."""
    
    def __init__(
        self,
        data_source: Callable,
        cursor_field: str = "id",
        encode_cursor: Optional[Callable] = None,
        decode_cursor: Optional[Callable] = None
    ):
        self.data_source = data_source
        self.cursor_field = cursor_field
        self.encode_cursor = encode_cursor or self._default_encode_cursor
        self.decode_cursor = decode_cursor or self._default_decode_cursor
    
    async def fetch_page(self, params: PaginationParams) -> PaginationResult[T]:
        """Fetch page using cursor-based pagination."""
        cursor_value = None
        if params.cursor:
            cursor_value = self.decode_cursor(params.cursor)
        
        # Fetch one extra item to determine if there's a next page
        data = await self.data_source(
            cursor=cursor_value,
            cursor_field=self.cursor_field,
            limit=params.page_size + 1,
            sort_by=params.sort_by,
            sort_direction=params.sort_direction.value,
            filters=params.filters,
            search=params.search
        )
        
        has_next = len(data) > params.page_size
        if has_next:
            data = data[:-1]  # Remove the extra item
        
        # Generate cursors
        next_cursor = None
        if has_next and data:
            last_item = data[-1]
            if isinstance(last_item, dict):
                cursor_val = last_item.get(self.cursor_field)
            else:
                cursor_val = getattr(last_item, self.cursor_field, None)
            
            if cursor_val is not None:
                next_cursor = self.encode_cursor(cursor_val)
        
        return PaginationResult(
            data=data,
            total_count=-1,  # Unknown for cursor-based pagination
            page=params.page,
            page_size=params.page_size,
            total_pages=-1,  # Unknown for cursor-based pagination
            has_next=has_next,
            has_previous=params.cursor is not None,
            next_cursor=next_cursor,
            previous_cursor=params.cursor
        )
    
    async def get_total_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Get total count (expensive for cursor-based pagination)."""
        # This is expensive for cursor-based pagination
        # Consider caching or approximating
        return -1
    
    async def search(self, query: str, params: PaginationParams) -> PaginationResult[T]:
        """Search with cursor-based pagination."""
        params.search = query
        return await self.fetch_page(params)
    
    def _default_encode_cursor(self, value: Any) -> str:
        """Default cursor encoding."""
        import base64
        import json
        return base64.b64encode(json.dumps(value).encode()).decode()
    
    def _default_decode_cursor(self, cursor: str) -> Any:
        """Default cursor decoding."""
        import base64
        import json
        return json.loads(base64.b64decode(cursor.encode()).decode())


class VirtualScrollProvider(PaginationProvider[T]):
    """Virtual scrolling provider for large lists."""
    
    def __init__(
        self,
        data_source: Callable,
        item_height: float = 50.0,
        buffer_size: int = 10,
        prefetch_pages: int = 2
    ):
        self.data_source = data_source
        self.item_height = item_height
        self.buffer_size = buffer_size
        self.prefetch_pages = prefetch_pages
        self.cache: OrderedDict = OrderedDict()
        self.max_cache_size = 1000
        self._lock = threading.RLock()
    
    async def fetch_page(self, params: PaginationParams) -> PaginationResult[T]:
        """Fetch page for virtual scrolling."""
        # Calculate virtual window
        window = self._calculate_window(params)
        
        # Fetch data with buffer
        start_index = max(0, window.start_index - self.buffer_size)
        end_index = window.end_index + self.buffer_size
        
        data = await self._fetch_range(start_index, end_index, params)
        
        # Extract visible portion
        visible_start = window.start_index - start_index
        visible_end = visible_start + window.visible_count
        visible_data = data[visible_start:visible_end]
        
        total_count = await self.get_total_count(params.filters)
        
        return PaginationResult(
            data=visible_data,
            total_count=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=math.ceil(total_count / params.page_size),
            has_next=window.end_index < total_count,
            has_previous=window.start_index > 0,
            metadata={
                "virtual_window": {
                    "start_index": window.start_index,
                    "end_index": window.end_index,
                    "item_height": window.item_height,
                    "total_height": total_count * self.item_height
                }
            }
        )
    
    def _calculate_window(self, params: PaginationParams) -> VirtualWindow:
        """Calculate virtual scrolling window."""
        scroll_top = params.metadata.get("scroll_top", 0)
        container_height = params.metadata.get("container_height", 400)
        
        start_index = max(0, int(scroll_top / self.item_height))
        visible_count = math.ceil(container_height / self.item_height) + 1
        end_index = start_index + visible_count
        
        return VirtualWindow(
            start_index=start_index,
            end_index=end_index,
            buffer_size=self.buffer_size,
            item_height=self.item_height,
            container_height=container_height
        )
    
    async def _fetch_range(self, start: int, end: int, params: PaginationParams) -> List[T]:
        """Fetch data range with caching."""
        cache_key = self._make_cache_key(start, end, params)
        
        with self._lock:
            if cache_key in self.cache:
                # Move to end (LRU)
                self.cache.move_to_end(cache_key)
                return self.cache[cache_key]
        
        # Fetch from data source
        data = await self.data_source(
            offset=start,
            limit=end - start,
            sort_by=params.sort_by,
            sort_direction=params.sort_direction.value,
            filters=params.filters,
            search=params.search
        )
        
        # Cache the result
        with self._lock:
            self.cache[cache_key] = data
            self.cache.move_to_end(cache_key)
            
            # Trim cache if too large
            while len(self.cache) > self.max_cache_size:
                self.cache.popitem(last=False)
        
        return data
    
    def _make_cache_key(self, start: int, end: int, params: PaginationParams) -> str:
        """Create cache key for data range."""
        import hashlib
        import json
        
        key_data = {
            "start": start,
            "end": end,
            "sort_by": params.sort_by,
            "sort_direction": params.sort_direction.value,
            "filters": params.filters,
            "search": params.search
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get_total_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Get total count with caching."""
        cache_key = f"total_count_{hash(str(filters))}"
        
        with self._lock:
            if cache_key in self.cache:
                return self.cache[cache_key]
        
        # This would typically be a separate, optimized count query
        count = await self._get_count_from_source(filters or {})
        
        with self._lock:
            self.cache[cache_key] = count
        
        return count
    
    async def _get_count_from_source(self, filters: Dict[str, Any]) -> int:
        """Get count from data source."""
        # This is a placeholder - implement based on your data source
        data = await self.data_source(
            offset=0,
            limit=None,
            filters=filters,
            count_only=True
        )
        return len(data) if isinstance(data, list) else data
    
    async def search(self, query: str, params: PaginationParams) -> PaginationResult[T]:
        """Search with virtual scrolling."""
        params.search = query
        return await self.fetch_page(params)


class AdaptivePaginator:
    """Adaptive paginator that chooses the best strategy."""
    
    def __init__(self):
        self.providers: Dict[PaginationStrategy, PaginationProvider] = {}
        self.strategy_performance: Dict[PaginationStrategy, List[float]] = {}
        self.default_strategy = PaginationStrategy.OFFSET_LIMIT
    
    def register_provider(self, strategy: PaginationStrategy, provider: PaginationProvider) -> None:
        """Register a pagination provider."""
        self.providers[strategy] = provider
        self.strategy_performance[strategy] = []
    
    async def fetch_page(
        self,
        params: PaginationParams,
        strategy: Optional[PaginationStrategy] = None
    ) -> PaginationResult[T]:
        """Fetch page using adaptive strategy selection."""
        if strategy is None:
            strategy = self._select_best_strategy(params)
        
        if strategy not in self.providers:
            strategy = self.default_strategy
        
        provider = self.providers[strategy]
        
        # Measure performance
        start_time = asyncio.get_event_loop().time()
        try:
            result = await provider.fetch_page(params)
            performance = asyncio.get_event_loop().time() - start_time
            self._record_performance(strategy, performance)
            return result
        except Exception as e:
            logger.error(f"Error with strategy {strategy}: {e}")
            # Fallback to default strategy
            if strategy != self.default_strategy:
                return await self.fetch_page(params, self.default_strategy)
            raise
    
    def _select_best_strategy(self, params: PaginationParams) -> PaginationStrategy:
        """Select the best strategy based on parameters and performance."""
        # Rule-based strategy selection
        if params.search and len(params.search) > 3:
            # For complex searches, cursor-based might be better
            if PaginationStrategy.CURSOR_BASED in self.providers:
                return PaginationStrategy.CURSOR_BASED
        
        if params.page_size > 100:
            # For large page sizes, virtual scrolling might be better
            if PaginationStrategy.VIRTUAL_SCROLL in self.providers:
                return PaginationStrategy.VIRTUAL_SCROLL
        
        # Performance-based selection
        if self.strategy_performance:
            avg_performance = {
                strategy: sum(times) / len(times)
                for strategy, times in self.strategy_performance.items()
                if times
            }
            
            if avg_performance:
                best_strategy = min(avg_performance, key=avg_performance.get)
                return best_strategy
        
        return self.default_strategy
    
    def _record_performance(self, strategy: PaginationStrategy, performance: float) -> None:
        """Record performance metrics."""
        performance_list = self.strategy_performance[strategy]
        performance_list.append(performance)
        
        # Keep only recent performance data
        if len(performance_list) > 100:
            performance_list.pop(0)


class ConfigurablePaginator:
    """Configurable paginator with Improved features."""
    
    def __init__(
        self,
        provider: PaginationProvider[T],
        enable_prefetch: bool = True,
        enable_cache: bool = True,
        cache_size: int = 100
    ):
        self.provider = provider
        self.enable_prefetch = enable_prefetch
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        
        self.page_cache: OrderedDict = OrderedDict()
        self.prefetch_queue: deque = deque()
        self.prefetch_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
    
    async def fetch_page(self, params: PaginationParams) -> PaginationResult[T]:
        """Fetch page with Configurable caching and prefetching."""
        cache_key = self._make_cache_key(params)
        
        # Check cache first
        if self.enable_cache:
            with self._lock:
                if cache_key in self.page_cache:
                    self.page_cache.move_to_end(cache_key)
                    cached_result = self.page_cache[cache_key]
                    
                    # Check if cached result is still valid
                    if self._is_cache_valid(cached_result):
                        # Schedule prefetch for next pages
                        if self.enable_prefetch:
                            self._schedule_prefetch(params)
                        
                        return cached_result
        
        # Fetch from provider
        result = await self.provider.fetch_page(params)
        
        # Cache the result
        if self.enable_cache:
            with self._lock:
                self.page_cache[cache_key] = result
                self.page_cache.move_to_end(cache_key)
                
                # Trim cache
                while len(self.page_cache) > self.cache_size:
                    self.page_cache.popitem(last=False)
        
        # Schedule prefetch
        if self.enable_prefetch:
            self._schedule_prefetch(params)
        
        return result
    
    def _make_cache_key(self, params: PaginationParams) -> str:
        """Create cache key for pagination parameters."""
        import hashlib
        import json
        
        key_data = {
            "page": params.page,
            "page_size": params.page_size,
            "sort_by": params.sort_by,
            "sort_direction": params.sort_direction.value,
            "filters": params.filters,
            "search": params.search,
            "cursor": params.cursor
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, result: PaginationResult[T]) -> bool:
        """Check if cached result is still valid."""
        # For now, assume cache is always valid
        # In practice, you might check timestamps or version numbers
        return True
    
    def _schedule_prefetch(self, params: PaginationParams) -> None:
        """Schedule prefetch for likely next pages."""
        if not self.enable_prefetch:
            return
        
        prefetch_params = []
        
        # Prefetch next page
        if params.page and params.page > 0:
            next_params = PaginationParams(
                page=params.page + 1,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_direction=params.sort_direction,
                filters=params.filters.copy(),
                search=params.search
            )
            prefetch_params.append(next_params)
        
        # Prefetch previous page
        if params.page and params.page > 1:
            prev_params = PaginationParams(
                page=params.page - 1,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_direction=params.sort_direction,
                filters=params.filters.copy(),
                search=params.search
            )
            prefetch_params.append(prev_params)
        
        # Add to prefetch queue
        for prefetch_param in prefetch_params:
            cache_key = self._make_cache_key(prefetch_param)
            with self._lock:
                if cache_key not in self.page_cache:
                    self.prefetch_queue.append(prefetch_param)
        
        # Start prefetch task if not running
        if not self.prefetch_task or self.prefetch_task.done():
            self.prefetch_task = asyncio.create_task(self._prefetch_worker())
    
    async def _prefetch_worker(self) -> None:
        """Background prefetch worker."""
        while self.prefetch_queue:
            try:
                with self._lock:
                    if not self.prefetch_queue:
                        break
                    params = self.prefetch_queue.popleft()
                
                cache_key = self._make_cache_key(params)
                
                # Check if already cached
                with self._lock:
                    if cache_key in self.page_cache:
                        continue
                
                # Fetch and cache
                result = await self.provider.fetch_page(params)
                
                with self._lock:
                    self.page_cache[cache_key] = result
                    self.page_cache.move_to_end(cache_key)
                    
                    # Trim cache
                    while len(self.page_cache) > self.cache_size:
                        self.page_cache.popitem(last=False)
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in prefetch worker: {e}")
    
    def invalidate_cache(self, pattern: Optional[str] = None) -> None:
        """Invalidate cache entries."""
        with self._lock:
            if pattern is None:
                self.page_cache.clear()
            else:
                import fnmatch
                keys_to_remove = [
                    key for key in self.page_cache.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
                for key in keys_to_remove:
                    del self.page_cache[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "cache_size": len(self.page_cache),
                "max_cache_size": self.cache_size,
                "prefetch_queue_size": len(self.prefetch_queue),
                "prefetch_enabled": self.enable_prefetch,
                "cache_enabled": self.enable_cache
            }


# Utility functions for common pagination patterns

def create_database_paginator(
    db_connection,
    table_name: str,
    strategy: PaginationStrategy = PaginationStrategy.OFFSET_LIMIT
) -> ConfigurablePaginator:
    """Create a paginator for database queries."""
    
    async def db_data_source(**kwargs):
        # This is a placeholder - implement based on your database
        # Example for SQL databases:
        offset = kwargs.get('offset', 0)
        limit = kwargs.get('limit', 20)
        filters = kwargs.get('filters', {})
        
        # Build query
        query = f"SELECT * FROM {table_name}"
        if filters:
            # Add WHERE clause
            pass
        
        # Add ORDER BY, LIMIT, OFFSET
        query += f" LIMIT {limit} OFFSET {offset}"
        
        # Execute query and return results
        return []
    
    if strategy == PaginationStrategy.OFFSET_LIMIT:
        provider = OffsetLimitProvider(db_data_source)
    elif strategy == PaginationStrategy.CURSOR_BASED:
        provider = CursorBasedProvider(db_data_source)
    else:
        provider = OffsetLimitProvider(db_data_source)
    
    return ConfigurablePaginator(provider)


def create_api_paginator(
    api_client,
    endpoint: str,
    strategy: PaginationStrategy = PaginationStrategy.CURSOR_BASED
) -> ConfigurablePaginator:
    """Create a paginator for API endpoints."""
    
    async def api_data_source(**kwargs):
        # This is a placeholder - implement based on your API
        params = {
            'offset': kwargs.get('offset', 0),
            'limit': kwargs.get('limit', 20),
            'cursor': kwargs.get('cursor'),
            'sort': kwargs.get('sort_by'),
            'order': kwargs.get('sort_direction', 'asc')
        }
        
        # Add filters
        params.update(kwargs.get('filters', {}))
        
        # Make API request
        response = await api_client.get(endpoint, params=params)
        return response.get('data', [])
    
    if strategy == PaginationStrategy.CURSOR_BASED:
        provider = CursorBasedProvider(api_data_source)
    elif strategy == PaginationStrategy.OFFSET_LIMIT:
        provider = OffsetLimitProvider(api_data_source)
    else:
        provider = OffsetLimitProvider(api_data_source)
    
    return ConfigurablePaginator(provider)
