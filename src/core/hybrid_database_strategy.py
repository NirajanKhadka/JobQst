"""
Hybrid Database Strategy for JobLens
PostgreSQL (primary) + Redis (caching) for optimal performance
"""

import os
import json
import redis
import asyncpg
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration for hybrid setup"""
    # PostgreSQL (Primary)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "joblens"
    postgres_user: str = "joblens_user"
    postgres_password: str = "joblens_pass"
    
    # Redis (Cache)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Performance Settings
    postgres_pool_min: int = 5
    postgres_pool_max: int = 20
    redis_pool_size: int = 10
    cache_ttl: int = 3600  # 1 hour
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Load configuration from environment variables"""
        return cls(
            postgres_host=os.getenv('POSTGRES_HOST', 'localhost'),
            postgres_port=int(os.getenv('POSTGRES_PORT', '5432')),
            postgres_db=os.getenv('POSTGRES_DB', 'joblens'),
            postgres_user=os.getenv('POSTGRES_USER', 'joblens_user'),
            postgres_password=os.getenv('POSTGRES_PASSWORD', 'joblens_pass'),
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', '6379')),
            redis_db=int(os.getenv('REDIS_DB', '0')),
            redis_password=os.getenv('REDIS_PASSWORD'),
        )


class HybridJobDatabase:
    """
    Hybrid database using PostgreSQL + Redis for optimal JobLens performance
    
    Architecture:
    - PostgreSQL: Primary storage for jobs, profiles, analytics
    - Redis: Hot cache for frequently accessed data, session storage
    - Automatic fallback: Redis -> PostgreSQL if cache miss
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connections"""
        if self._initialized:
            return
            
        try:
            # Initialize PostgreSQL connection pool
            self.postgres_pool = await asyncpg.create_pool(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                min_size=self.config.postgres_pool_min,
                max_size=self.config.postgres_pool_max,
                command_timeout=30
            )
            
            # Initialize Redis connection
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connections
            await self._test_connections()
            
            # Initialize schema
            await self._initialize_schema()
            
            self._initialized = True
            logger.info("✅ Hybrid database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize hybrid database: {e}")
            raise
    
    async def _test_connections(self) -> None:
        """Test database connections"""
        # Test PostgreSQL
        async with self.postgres_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Test Redis
        self.redis_client.ping()
    
    async def _initialize_schema(self) -> None:
        """Initialize PostgreSQL schema optimized for JobLens"""
        schema_sql = """
        -- Enable extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fast text search
        CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes
        
        -- Jobs table with JobLens-specific optimizations
        CREATE TABLE IF NOT EXISTS jobs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id VARCHAR(255) UNIQUE NOT NULL,
            profile_name VARCHAR(100) NOT NULL,
            
            -- Core job data
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            description TEXT,
            salary_range TEXT,
            experience_level VARCHAR(50),
            employment_type VARCHAR(50),
            
            -- JobLens enhanced fields
            remote_work_option VARCHAR(50),
            job_posted_date TIMESTAMP,
            application_deadline TIMESTAMP,
            required_years_experience VARCHAR(50),
            education_requirements TEXT,
            industry VARCHAR(100),
            
            -- Analysis results (JSONB for fast queries)
            skills JSONB,
            requirements JSONB,
            benefits JSONB,
            
            -- Scoring and analytics
            fit_score DECIMAL(5,4),
            compatibility_score DECIMAL(5,4),
            ai_analysis JSONB,
            
            -- Processing metadata
            source VARCHAR(50) NOT NULL, -- 'jobspy', 'eluta', etc.
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            
            -- Performance tracking
            processing_time_ms INTEGER,
            worker_id INTEGER,
            
            CONSTRAINT valid_fit_score CHECK (fit_score >= 0 AND fit_score <= 1),
            CONSTRAINT valid_compatibility_score CHECK (compatibility_score >= 0 AND compatibility_score <= 1)
        );
        
        -- Optimized indexes for JobLens queries
        CREATE INDEX IF NOT EXISTS idx_jobs_profile_status ON jobs(profile_name, status);
        CREATE INDEX IF NOT EXISTS idx_jobs_fit_score ON jobs(fit_score DESC) WHERE status = 'active';
        CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
        CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs USING gin(location gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS idx_jobs_title_company ON jobs USING gin((title || ' ' || company) gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS idx_jobs_skills ON jobs USING gin(skills);
        CREATE INDEX IF NOT EXISTS idx_jobs_requirements ON jobs USING gin(requirements);
        
        -- Performance analytics table
        CREATE TABLE IF NOT EXISTS processing_metrics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            profile_name VARCHAR(100),
            operation VARCHAR(50),
            jobs_processed INTEGER,
            processing_time_ms INTEGER,
            success_rate DECIMAL(5,4),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_metrics_profile_timestamp ON processing_metrics(profile_name, timestamp DESC);
        """
        
        async with self.postgres_pool.acquire() as conn:
            await conn.execute(schema_sql)
    
    async def add_job(self, job_data: Dict[str, Any], profile_name: str) -> bool:
        """Add job with caching strategy"""
        try:
            # Prepare job data
            job_data['profile_name'] = profile_name
            job_data['scraped_at'] = datetime.utcnow()
            
            # Insert into PostgreSQL
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO jobs (job_id, profile_name, title, company, location, 
                                    description, salary_range, experience_level, employment_type,
                                    remote_work_option, skills, requirements, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (job_id) DO NOTHING
                """, 
                    job_data.get('job_id'),
                    profile_name,
                    job_data.get('title'),
                    job_data.get('company'),
                    job_data.get('location'),
                    job_data.get('description'),
                    job_data.get('salary_range'),
                    job_data.get('experience_level'),
                    job_data.get('employment_type'),
                    job_data.get('remote_work_option'),
                    json.dumps(job_data.get('skills', [])),
                    json.dumps(job_data.get('requirements', [])),
                    job_data.get('source', 'unknown')
                )
            
            # Cache recent jobs for fast access
            cache_key = f"recent_jobs:{profile_name}"
            self.redis_client.lpush(cache_key, json.dumps(job_data))
            self.redis_client.ltrim(cache_key, 0, 99)  # Keep latest 100
            self.redis_client.expire(cache_key, self.config.cache_ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add job: {e}")
            return False
    
    async def get_top_jobs(self, profile_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top jobs with intelligent caching"""
        cache_key = f"top_jobs:{profile_name}:{limit}"
        
        # Try cache first
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            pass  # Cache miss, continue to database
        
        # Query PostgreSQL
        async with self.postgres_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT job_id, title, company, location, fit_score, compatibility_score,
                       skills, requirements, scraped_at, source
                FROM jobs 
                WHERE profile_name = $1 AND status = 'active'
                ORDER BY fit_score DESC NULLS LAST, scraped_at DESC
                LIMIT $2
            """, profile_name, limit)
            
            jobs = [dict(row) for row in rows]
            
            # Cache the results
            try:
                self.redis_client.setex(
                    cache_key, 
                    self.config.cache_ttl // 2,  # Shorter TTL for top jobs
                    json.dumps(jobs, default=str)
                )
            except Exception:
                pass  # Cache write failure, not critical
            
            return jobs
    
    async def search_jobs(self, profile_name: str, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Advanced job search with full-text capabilities"""
        filters = filters or {}
        
        # Build dynamic query
        where_conditions = ["profile_name = $1", "status = 'active'"]
        params = [profile_name]
        param_count = 1
        
        # Text search
        if query:
            param_count += 1
            where_conditions.append(f"(title || ' ' || company || ' ' || description) ILIKE ${param_count}")
            params.append(f"%{query}%")
        
        # Filters
        if filters.get('location'):
            param_count += 1
            where_conditions.append(f"location ILIKE ${param_count}")
            params.append(f"%{filters['location']}%")
        
        if filters.get('min_fit_score'):
            param_count += 1
            where_conditions.append(f"fit_score >= ${param_count}")
            params.append(float(filters['min_fit_score']))
        
        # Execute search
        search_sql = f"""
            SELECT job_id, title, company, location, fit_score, compatibility_score,
                   skills, requirements, scraped_at, source
            FROM jobs 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY fit_score DESC NULLS LAST, scraped_at DESC
            LIMIT 100
        """
        
        async with self.postgres_pool.acquire() as conn:
            rows = await conn.fetch(search_sql, *params)
            return [dict(row) for row in rows]
    
    async def update_job_analysis(self, job_id: str, analysis_data: Dict[str, Any]) -> bool:
        """Update job with analysis results"""
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE jobs 
                    SET fit_score = $2, 
                        compatibility_score = $3,
                        ai_analysis = $4,
                        processed_at = $5
                    WHERE job_id = $1
                """, 
                    job_id,
                    analysis_data.get('fit_score'),
                    analysis_data.get('compatibility_score'),
                    json.dumps(analysis_data.get('ai_analysis', {})),
                    datetime.utcnow()
                )
            
            # Invalidate related caches
            # This is a simplified cache invalidation - in production you might want more sophisticated cache management
            cache_pattern = f"*top_jobs*"
            for key in self.redis_client.scan_iter(match=cache_pattern):
                self.redis_client.delete(key)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update job analysis: {e}")
            return False
    
    async def get_performance_metrics(self, profile_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        async with self.postgres_pool.acquire() as conn:
            # Job processing stats
            job_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE processed_at IS NOT NULL) as processed_jobs,
                    AVG(processing_time_ms) as avg_processing_time,
                    AVG(fit_score) FILTER (WHERE fit_score IS NOT NULL) as avg_fit_score
                FROM jobs 
                WHERE profile_name = $1 AND scraped_at >= $2
            """, profile_name, since)
            
            # Source breakdown
            source_stats = await conn.fetch("""
                SELECT source, COUNT(*) as count
                FROM jobs 
                WHERE profile_name = $1 AND scraped_at >= $2
                GROUP BY source
                ORDER BY count DESC
            """, profile_name, since)
            
            return {
                'total_jobs': job_stats['total_jobs'],
                'processed_jobs': job_stats['processed_jobs'],
                'processing_rate': job_stats['processed_jobs'] / max(job_stats['total_jobs'], 1),
                'avg_processing_time_ms': float(job_stats['avg_processing_time'] or 0),
                'avg_fit_score': float(job_stats['avg_fit_score'] or 0),
                'source_breakdown': {row['source']: row['count'] for row in source_stats}
            }
    
    async def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up old jobs to maintain performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self.postgres_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM jobs 
                WHERE scraped_at < $1 AND status != 'applied'
            """, cutoff_date)
            
            # Also clean up processing metrics
            await conn.execute("""
                DELETE FROM processing_metrics 
                WHERE timestamp < $1
            """, cutoff_date)
            
            return int(result.split()[-1])  # Extract number of deleted rows
    
    async def close(self) -> None:
        """Close database connections"""
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.redis_client:
            self.redis_client.close()


# Factory function for easy integration
async def create_hybrid_database(config: Optional[DatabaseConfig] = None) -> HybridJobDatabase:
    """Create and initialize hybrid database"""
    db = HybridJobDatabase(config)
    await db.initialize()
    return db


# Test function
async def test_hybrid_database():
    """Test the hybrid database setup"""
    print("🧪 Testing Hybrid Database...")
    
    db = await create_hybrid_database()
    
    # Test job insertion
    test_job = {
        'job_id': 'test_123',
        'title': 'Senior Python Developer',
        'company': 'TechCorp',
        'location': 'Toronto, ON',
        'description': 'Python development role...',
        'skills': ['Python', 'PostgreSQL', 'Redis'],
        'source': 'test'
    }
    
    success = await db.add_job(test_job, 'TestProfile')
    print(f"✅ Job insertion: {'SUCCESS' if success else 'FAILED'}")
    
    # Test job retrieval
    jobs = await db.get_top_jobs('TestProfile', 10)
    print(f"✅ Job retrieval: {len(jobs)} jobs found")
    
    # Test performance metrics
    metrics = await db.get_performance_metrics('TestProfile')
    print(f"✅ Performance metrics: {metrics}")
    
    await db.close()
    print("✅ Hybrid database test completed")


if __name__ == "__main__":
    asyncio.run(test_hybrid_database())
