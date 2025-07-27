"""
Optimized Connection Pool for enhanced connection management.

This module provides an optimized connection pool system for the scraper pipeline
with advanced features including connection pooling, rate limiting, health monitoring,
and intelligent retry mechanisms.

Features:
- Connection pooling with configurable pool size
- Advanced rate limiting with configurable thresholds
- Connection health monitoring and automatic cleanup
- Retry strategy with exponential backoff
- Performance metrics and monitoring
- Integration with existing pipeline components
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import aiohttp
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for connection pool performance tracking."""
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_health_check: datetime = field(default_factory=datetime.now)
    connection_errors: Dict[str, int] = field(default_factory=dict)
    rate_limit_hits: int = 0
    retry_attempts: int = 0


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: int = 100
    burst_limit: int = 50
    window_size_seconds: int = 60
    backoff_multiplier: float = 2.0
    max_backoff_seconds: int = 60


@dataclass
class ConnectionConfig:
    """Configuration for connection pool."""
    pool_size: int = 10
    max_connections: int = 50
    connection_timeout: int = 30
    read_timeout: int = 30
    write_timeout: int = 30
    keepalive_timeout: int = 60
    retry_attempts: int = 3
    health_check_interval: int = 30
    max_retry_delay: int = 60


class RateLimiter:
    """Advanced rate limiter with sliding window and burst handling."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times = deque()
        self.last_request_time = 0
        self.backoff_until = 0
        
    def can_make_request(self) -> bool:
        """Check if a request can be made based on rate limits."""
        now = time.time()
        
        # Check if we're in backoff period
        if now < self.backoff_until:
            return False
            
        # Remove old requests outside the window
        while self.request_times and now - self.request_times[0] > self.config.window_size_seconds:
            self.request_times.popleft()
            
        # Check if we're within rate limits
        if len(self.request_times) >= self.config.requests_per_second:
            return False
            
        return True
        
    def record_request(self) -> None:
        """Record a request for rate limiting."""
        now = time.time()
        self.request_times.append(now)
        self.last_request_time = now
        
    def handle_rate_limit(self) -> float:
        """Handle rate limit hit and return backoff delay."""
        now = time.time()
        
        # Calculate exponential backoff
        if self.backoff_until == 0:
            delay = 1.0
        else:
            delay = min(
                self.config.backoff_multiplier * (now - self.last_request_time),
                self.config.max_backoff_seconds
            )
            
        self.backoff_until = now + delay
        return delay


class OptimizedConnectionPool:
    """
    Optimized connection pool with advanced features for the scraper pipeline.
    
    Features:
    - Connection pooling with configurable pool size
    - Advanced rate limiting with sliding window
    - Connection health monitoring
    - Automatic retry with exponential backoff
    - Performance metrics and monitoring
    - Integration with existing pipeline components
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None, 
                 rate_limit_config: Optional[RateLimitConfig] = None):
        self.config = config or ConnectionConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        
        # Initialize components
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(self.rate_limit_config)
        self.metrics = ConnectionMetrics()
        
        # Connection management
        self.connection_pool = {}
        self.health_check_task = None
        self.is_running = False
        
        # Performance tracking
        self.response_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        
        logger.info(f"OptimizedConnectionPool initialized: pool_size={self.config.pool_size}")
        
    async def start(self) -> None:
        """Start the connection pool and health monitoring."""
        if self.is_running:
            return
            
        # Create aiohttp session with connection pooling
        try:
            connector = aiohttp.TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.pool_size,
                keepalive_timeout=self.config.keepalive_timeout,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config.connection_timeout,
                connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout,
                sock_connect=self.config.write_timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        except AttributeError:
            # Fallback for older aiohttp versions
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        
        # Start health monitoring
        self.is_running = True
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("OptimizedConnectionPool started")
        
    async def stop(self) -> None:
        """Stop the connection pool and cleanup resources."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Stop health monitoring
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
                
        # Close session
        if self.session:
            await self.session.close()
            
        logger.info("OptimizedConnectionPool stopped")
        
    @asynccontextmanager
    async def get_connection(self, url: str):
        """Get a connection from the pool with automatic cleanup."""
        if not self.is_running:
            raise RuntimeError("Connection pool not started")
            
        # Check rate limits
        if not self.rate_limiter.can_make_request():
            delay = self.rate_limiter.handle_rate_limit()
            self.metrics.rate_limit_hits += 1
            logger.warning(f"Rate limit hit, waiting {delay:.2f}s")
            await asyncio.sleep(delay)
            
        # Record request
        self.rate_limiter.record_request()
        self.metrics.total_connections += 1
        self.metrics.active_connections += 1
        
        start_time = time.time()
        
        try:
            yield self.session
            
            # Record successful request
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            self.metrics.successful_requests += 1
            
            # Update average response time
            if self.response_times:
                self.metrics.avg_response_time = sum(self.response_times) / len(self.response_times)
                
        except Exception as e:
            # Record failed request
            self.metrics.failed_requests += 1
            self.metrics.connection_errors[str(type(e).__name__)] += 1
            self.error_counts[str(type(e).__name__)] += 1
            logger.error(f"Connection error: {e}")
            raise
            
        finally:
            self.metrics.active_connections -= 1
            
    async def make_request(self, url: str, method: str = "GET", 
                          **kwargs) -> Optional[Any]:
        """Make an HTTP request with automatic retry and error handling."""
        for attempt in range(self.config.retry_attempts + 1):
            try:
                async with self.get_connection(url) as session:
                    async with session.request(method, url, **kwargs) as response:
                        response.raise_for_status()
                        return response
                        
            except (aiohttp.ClientError, aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                self.metrics.retry_attempts += 1
                
                if attempt == self.config.retry_attempts:
                    logger.error(f"Request failed after {attempt + 1} attempts: {e}")
                    raise
                    
                # Exponential backoff
                delay = min(2 ** attempt, self.config.max_retry_delay)
                logger.warning(f"Request failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
                
        return None
        
    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
                
    async def _perform_health_check(self) -> None:
        """Perform health check on connection pool."""
        try:
            # Check session health
            if self.session and self.session.closed:
                logger.warning("Session closed, recreating...")
                await self.start()
                
            # Update metrics
            self.metrics.last_health_check = datetime.now()
            
            # Log health status
            if self.metrics.failed_requests > 0:
                error_rate = self.metrics.failed_requests / (self.metrics.successful_requests + self.metrics.failed_requests)
                if error_rate > 0.1:  # 10% error rate threshold
                    logger.warning(f"High error rate detected: {error_rate:.2%}")
                    
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current connection pool metrics."""
        return {
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "avg_response_time": self.metrics.avg_response_time,
            "error_rate": (self.metrics.failed_requests / 
                          max(1, self.metrics.successful_requests + self.metrics.failed_requests)),
            "rate_limit_hits": self.metrics.rate_limit_hits,
            "retry_attempts": self.metrics.retry_attempts,
            "connection_errors": dict(self.metrics.connection_errors),
            "last_health_check": self.metrics.last_health_check.isoformat()
        }
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the connection pool."""
        error_rate = (self.metrics.failed_requests / 
                     max(1, self.metrics.successful_requests + self.metrics.failed_requests))
        
        return {
            "status": "healthy" if error_rate < 0.1 else "degraded",
            "error_rate": error_rate,
            "active_connections": self.metrics.active_connections,
            "pool_size": self.config.pool_size,
            "is_running": self.is_running
        } 