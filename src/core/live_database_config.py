"""
Live Database Configuration for JobLens
PostgreSQL + Redis for real-time updates and caching
"""

import os
import redis
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from typing import Optional, Dict, Any, Tuple
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LiveDatabaseConfig:
    """
    Optimized database configuration for live numbers and caching.
    Combines PostgreSQL for persistence with Redis for real-time caching.
    """
    
    def __init__(self):
        self.postgres_pool: Optional[ThreadedConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._setup_connections()
    
    def _setup_connections(self):
        """Initialize PostgreSQL and Redis connections."""
        try:
            # PostgreSQL Configuration
            self.postgres_config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', 5432)),
                'database': os.getenv('POSTGRES_DB', 'joblens_db'),
                'user': os.getenv('POSTGRES_USER', 'joblens_user'),
                'password': os.getenv('POSTGRES_PASSWORD', 'joblens_password')
            }
            
            # Redis Configuration
            self.redis_config = {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'decode_responses': True
            }
            
            logger.info("Database configurations loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load database configurations: {e}")
            raise
    
    def get_postgres_connection(self):
        """Get PostgreSQL connection from pool."""
        if not self.postgres_pool:
            self._create_postgres_pool()
        return self.postgres_pool.getconn()
    
    def return_postgres_connection(self, conn):
        """Return PostgreSQL connection to pool."""
        if self.postgres_pool:
            self.postgres_pool.putconn(conn)
    
    def _create_postgres_pool(self):
        """Create PostgreSQL connection pool."""
        try:
            self.postgres_pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                **self.postgres_config
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise
    
    def get_redis_client(self) -> redis.Redis:
        """Get Redis client for caching."""
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(**self.redis_config)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self.redis_client
    
    def cache_job_counts(self, profile_name: str, counts: Dict[str, int]):
        """Cache live job counts for real-time dashboard."""
        try:
            redis_client = self.get_redis_client()
            cache_key = f"job_counts:{profile_name}"
            
            # Add timestamp for freshness tracking
            counts['last_updated'] = datetime.now().isoformat()
            
            # Cache for 5 minutes
            redis_client.setex(
                cache_key,
                timedelta(minutes=5),
                json.dumps(counts)
            )
            
            # Publish update for live dashboards
            redis_client.publish(f"live_updates:{profile_name}", json.dumps({
                'type': 'job_counts',
                'data': counts
            }))
            
            logger.debug(f"Cached job counts for {profile_name}: {counts}")
            
        except Exception as e:
            logger.error(f"Failed to cache job counts: {e}")
    
    def get_cached_job_counts(self, profile_name: str) -> Optional[Dict[str, int]]:
        """Get cached job counts for live numbers."""
        try:
            redis_client = self.get_redis_client()
            cache_key = f"job_counts:{profile_name}"
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached job counts: {e}")
            return None
    
    def cache_search_results(self, search_key: str, job_ids: list, ttl_minutes: int = 30):
        """Cache job search results to avoid re-querying."""
        try:
            redis_client = self.get_redis_client()
            cache_key = f"search:{search_key}"
            
            redis_client.setex(
                cache_key,
                timedelta(minutes=ttl_minutes),
                json.dumps(job_ids)
            )
            
            logger.debug(f"Cached search results: {len(job_ids)} jobs")
            
        except Exception as e:
            logger.error(f"Failed to cache search results: {e}")
    
    def get_cached_search_results(self, search_key: str) -> Optional[list]:
        """Get cached search results."""
        try:
            redis_client = self.get_redis_client()
            cache_key = f"search:{search_key}"
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached search results: {e}")
            return None
    
    def publish_live_update(self, profile_name: str, update_type: str, data: Dict[str, Any]):
        """Publish live update for real-time dashboard."""
        try:
            redis_client = self.get_redis_client()
            
            message = {
                'type': update_type,
                'profile': profile_name,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Publish to profile-specific channel
            redis_client.publish(f"live_updates:{profile_name}", json.dumps(message))
            
            # Publish to global channel for monitoring
            redis_client.publish("live_updates:global", json.dumps(message))
            
            logger.debug(f"Published live update: {update_type} for {profile_name}")
            
        except Exception as e:
            logger.error(f"Failed to publish live update: {e}")
    
    def test_connections(self) -> Tuple[bool, str]:
        """Test both PostgreSQL and Redis connections."""
        results = []
        
        # Test PostgreSQL
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            self.return_postgres_connection(conn)
            results.append("✅ PostgreSQL connection successful")
        except Exception as e:
            results.append(f"❌ PostgreSQL connection failed: {e}")
        
        # Test Redis
        try:
            redis_client = self.get_redis_client()
            redis_client.ping()
            results.append("✅ Redis connection successful")
        except Exception as e:
            results.append(f"❌ Redis connection failed: {e}")
        
        success = all("✅" in result for result in results)
        return success, "\n".join(results)
    
    def close_connections(self):
        """Close all database connections."""
        if self.postgres_pool:
            self.postgres_pool.closeall()
            logger.info("PostgreSQL pool closed")
        
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis client closed")


# Global instance for live database operations
live_db = LiveDatabaseConfig()
