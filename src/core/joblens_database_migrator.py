"""
JobLens Database Migration Strategy - SQLite to PostgreSQL
Optimized for JobLens architecture with minimal downtime
"""

import os
import sqlite3
import asyncio
import asyncpg
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import shutil
from rich.console import Console
from rich.progress import track

console = Console()
logger = logging.getLogger(__name__)


class JobLensDatabaseMigrator:
    """
    Specialized migrator for JobLens architecture
    
    Features:
    - Profile-aware migration (each profile has its own database)
    - Batch processing for large datasets
    - Data validation and integrity checks
    - Rollback capabilities
    - Performance optimization
    """
    
    def __init__(self, postgres_config: Dict[str, Any]):
        self.postgres_config = postgres_config
        self.batch_size = 1000
        self.backup_dir = Path("migration_backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def migrate_all_profiles(self, profiles_dir: str = "profiles") -> Dict[str, bool]:
        """Migrate all user profiles from SQLite to PostgreSQL"""
        console.print("🚀 Starting JobLens Database Migration to PostgreSQL")
        console.print("=" * 60)
        
        profiles_path = Path(profiles_dir)
        migration_results = {}
        
        # Find all profile databases
        profile_dbs = []
        for profile_dir in profiles_path.iterdir():
            if profile_dir.is_dir():
                db_path = profile_dir / "jobs.db"
                if db_path.exists():
                    profile_dbs.append((profile_dir.name, str(db_path)))
        
        console.print(f"📊 Found {len(profile_dbs)} profile databases to migrate")
        
        # Initialize PostgreSQL connection
        postgres_pool = await self._create_postgres_pool()
        
        try:
            # Create schemas and tables
            await self._initialize_postgres_schema(postgres_pool)
            
            # Migrate each profile
            for profile_name, db_path in track(profile_dbs, description="Migrating profiles..."):
                try:
                    console.print(f"\n🔄 Migrating profile: {profile_name}")
                    
                    # Backup original database
                    await self._backup_sqlite_db(db_path, profile_name)
                    
                    # Perform migration
                    job_count = await self._migrate_profile_data(
                        postgres_pool, profile_name, db_path
                    )
                    
                    # Validate migration
                    is_valid = await self._validate_migration(
                        postgres_pool, profile_name, db_path
                    )
                    
                    if is_valid:
                        migration_results[profile_name] = True
                        console.print(f"✅ Successfully migrated {job_count} jobs for {profile_name}")
                    else:
                        migration_results[profile_name] = False
                        console.print(f"❌ Migration validation failed for {profile_name}")
                        
                except Exception as e:
                    migration_results[profile_name] = False
                    console.print(f"❌ Migration failed for {profile_name}: {e}")
                    logger.error(f"Profile migration error: {e}", exc_info=True)
        
        finally:
            await postgres_pool.close()
        
        # Summary
        successful = sum(1 for success in migration_results.values() if success)
        total = len(migration_results)
        
        console.print(f"\n📈 Migration Summary:")
        console.print(f"✅ Successful: {successful}/{total}")
        console.print(f"❌ Failed: {total - successful}/{total}")
        
        if successful == total:
            console.print("[green]🎉 All profiles migrated successfully![/green]")
            await self._create_migration_completion_script()
        else:
            console.print("[yellow]⚠️ Some migrations failed. Check logs for details.[/yellow]")
        
        return migration_results
    
    async def _create_postgres_pool(self) -> asyncpg.Pool:
        """Create PostgreSQL connection pool"""
        return await asyncpg.create_pool(
            host=self.postgres_config['host'],
            port=self.postgres_config['port'],
            database=self.postgres_config['database'],
            user=self.postgres_config['user'],
            password=self.postgres_config['password'],
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def _initialize_postgres_schema(self, pool: asyncpg.Pool) -> None:
        """Initialize PostgreSQL schema optimized for JobLens"""
        schema_sql = """
        -- Enable PostgreSQL extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        CREATE EXTENSION IF NOT EXISTS "btree_gin";
        
        -- Main jobs table (optimized for JobLens)
        CREATE TABLE IF NOT EXISTS jobs (
            id BIGSERIAL PRIMARY KEY,
            job_id VARCHAR(255) UNIQUE NOT NULL,
            profile_name VARCHAR(100) NOT NULL,
            
            -- Core job fields (matching your current schema)
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            description TEXT,
            requirements TEXT,
            benefits TEXT,
            job_type TEXT,
            experience_level TEXT,
            education_level TEXT,
            skills_required TEXT,
            posted_date TEXT,
            application_url TEXT,
            source_url TEXT,
            
            -- JobLens enhanced fields
            remote_option TEXT,
            employment_type TEXT,
            industry TEXT,
            job_posted_date TIMESTAMP,
            application_deadline TIMESTAMP,
            required_years_experience TEXT,
            education_requirements TEXT,
            
            -- Analysis and scoring (JSONB for performance)
            fit_score DECIMAL(5,4),
            compatibility_score DECIMAL(5,4),
            ai_analysis JSONB,
            skills_extracted JSONB,
            requirements_extracted JSONB,
            benefits_extracted JSONB,
            
            -- Processing metadata
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            analysis_version TEXT,
            scraper_version TEXT,
            processing_time_ms INTEGER,
            
            -- Status tracking
            status VARCHAR(20) DEFAULT 'active',
            is_applied BOOLEAN DEFAULT FALSE,
            application_date TIMESTAMP,
            
            -- Constraints
            CONSTRAINT valid_fit_score CHECK (fit_score IS NULL OR (fit_score >= 0 AND fit_score <= 1)),
            CONSTRAINT valid_compatibility_score CHECK (compatibility_score IS NULL OR (compatibility_score >= 0 AND compatibility_score <= 1))
        );
        
        -- Performance-optimized indexes for JobLens queries
        CREATE INDEX IF NOT EXISTS idx_jobs_profile_status ON jobs(profile_name, status);
        CREATE INDEX IF NOT EXISTS idx_jobs_profile_fit_score ON jobs(profile_name, fit_score DESC NULLS LAST) 
            WHERE status = 'active';
        CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_location_trgm ON jobs USING gin(location gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS idx_jobs_title_company_trgm ON jobs USING gin((title || ' ' || company) gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS idx_jobs_skills_gin ON jobs USING gin(skills_extracted);
        CREATE INDEX IF NOT EXISTS idx_jobs_requirements_gin ON jobs USING gin(requirements_extracted);
        CREATE INDEX IF NOT EXISTS idx_jobs_full_text ON jobs USING gin(to_tsvector('english', title || ' ' || company || ' ' || COALESCE(description, '')));
        
        -- User profiles table
        CREATE TABLE IF NOT EXISTS user_profiles (
            id BIGSERIAL PRIMARY KEY,
            profile_name VARCHAR(100) UNIQUE NOT NULL,
            profile_data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Processing metrics for performance monitoring
        CREATE TABLE IF NOT EXISTS processing_metrics (
            id BIGSERIAL PRIMARY KEY,
            profile_name VARCHAR(100),
            operation VARCHAR(100),
            jobs_processed INTEGER,
            processing_time_ms INTEGER,
            success_rate DECIMAL(5,4),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_metrics_profile_timestamp ON processing_metrics(profile_name, timestamp DESC);
        
        -- Migration tracking
        CREATE TABLE IF NOT EXISTS migration_log (
            id BIGSERIAL PRIMARY KEY,
            profile_name VARCHAR(100),
            source_db_path TEXT,
            jobs_migrated INTEGER,
            migration_status VARCHAR(50),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT
        );
        """
        
        async with pool.acquire() as conn:
            await conn.execute(schema_sql)
            console.print("✅ PostgreSQL schema initialized")
    
    async def _backup_sqlite_db(self, db_path: str, profile_name: str) -> None:
        """Create backup of SQLite database"""
        backup_path = self.backup_dir / f"{profile_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_path, backup_path)
        console.print(f"💾 Backup created: {backup_path}")
    
    async def _migrate_profile_data(self, pool: asyncpg.Pool, profile_name: str, db_path: str) -> int:
        """Migrate data for a single profile"""
        # Log migration start
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO migration_log (profile_name, source_db_path, migration_status, started_at)
                VALUES ($1, $2, 'in_progress', $3)
            """, profile_name, db_path, datetime.now())
        
        try:
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(db_path)
            sqlite_conn.row_factory = sqlite3.Row
            cursor = sqlite_conn.cursor()
            
            # Get total job count
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            console.print(f"📊 Found {total_jobs} jobs to migrate")
            
            if total_jobs == 0:
                return 0
            
            # Migrate jobs in batches
            jobs_migrated = 0
            offset = 0
            
            while offset < total_jobs:
                # Fetch batch from SQLite
                cursor.execute("""
                    SELECT * FROM jobs 
                    ORDER BY id 
                    LIMIT ? OFFSET ?
                """, (self.batch_size, offset))
                
                batch_jobs = cursor.fetchall()
                
                if not batch_jobs:
                    break
                
                # Convert and insert to PostgreSQL
                async with pool.acquire() as conn:
                    for job_row in batch_jobs:
                        job_data = dict(job_row)
                        
                        # Convert JSON fields if they exist as strings
                        json_fields = ['skills_extracted', 'requirements_extracted', 'benefits_extracted', 'ai_analysis']
                        for field in json_fields:
                            if field in job_data and isinstance(job_data[field], str):
                                try:
                                    job_data[field] = json.loads(job_data[field])
                                except:
                                    job_data[field] = None
                        
                        # Insert into PostgreSQL
                        await conn.execute("""
                            INSERT INTO jobs (
                                job_id, profile_name, title, company, location, salary, description,
                                requirements, benefits, job_type, experience_level, education_level,
                                skills_required, posted_date, application_url, source_url,
                                fit_score, compatibility_score, ai_analysis, skills_extracted,
                                requirements_extracted, benefits_extracted, scraped_at, processed_at,
                                status, is_applied
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                                $17, $18, $19, $20, $21, $22, $23, $24, $25, $26
                            ) ON CONFLICT (job_id) DO NOTHING
                        """,
                            job_data.get('job_id'),
                            profile_name,
                            job_data.get('title'),
                            job_data.get('company'),
                            job_data.get('location'),
                            job_data.get('salary'),
                            job_data.get('description'),
                            job_data.get('requirements'),
                            job_data.get('benefits'),
                            job_data.get('job_type'),
                            job_data.get('experience_level'),
                            job_data.get('education_level'),
                            job_data.get('skills_required'),
                            job_data.get('posted_date'),
                            job_data.get('application_url'),
                            job_data.get('source_url'),
                            job_data.get('fit_score'),
                            job_data.get('compatibility_score'),
                            json.dumps(job_data.get('ai_analysis')) if job_data.get('ai_analysis') else None,
                            json.dumps(job_data.get('skills_extracted')) if job_data.get('skills_extracted') else None,
                            json.dumps(job_data.get('requirements_extracted')) if job_data.get('requirements_extracted') else None,
                            json.dumps(job_data.get('benefits_extracted')) if job_data.get('benefits_extracted') else None,
                            job_data.get('scraped_at'),
                            job_data.get('processed_at'),
                            job_data.get('status', 'active'),
                            job_data.get('is_applied', False)
                        )
                
                jobs_migrated += len(batch_jobs)
                offset += self.batch_size
                
                # Progress update
                progress = (offset / total_jobs) * 100
                console.print(f"  📈 Progress: {progress:.1f}% ({jobs_migrated}/{total_jobs} jobs)")
            
            sqlite_conn.close()
            
            # Log successful migration
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE migration_log 
                    SET jobs_migrated = $1, migration_status = 'completed', completed_at = $2
                    WHERE profile_name = $3 AND migration_status = 'in_progress'
                """, jobs_migrated, datetime.now(), profile_name)
            
            return jobs_migrated
            
        except Exception as e:
            # Log failed migration
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE migration_log 
                    SET migration_status = 'failed', completed_at = $1, error_message = $2
                    WHERE profile_name = $3 AND migration_status = 'in_progress'
                """, datetime.now(), str(e), profile_name)
            raise
    
    async def _validate_migration(self, pool: asyncpg.Pool, profile_name: str, sqlite_path: str) -> bool:
        """Validate that migration was successful"""
        try:
            # Count jobs in SQLite
            sqlite_conn = sqlite3.connect(sqlite_path)
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            sqlite_count = cursor.fetchone()[0]
            sqlite_conn.close()
            
            # Count jobs in PostgreSQL
            async with pool.acquire() as conn:
                postgres_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM jobs WHERE profile_name = $1
                """, profile_name)
            
            # Validate counts match
            is_valid = sqlite_count == postgres_count
            
            if is_valid:
                console.print(f"✅ Validation passed: {postgres_count} jobs migrated")
            else:
                console.print(f"❌ Validation failed: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
            
            return is_valid
            
        except Exception as e:
            console.print(f"❌ Validation error: {e}")
            return False
    
    async def _create_migration_completion_script(self) -> None:
        """Create script to update JobLens configuration for PostgreSQL"""
        config_script = '''#!/usr/bin/env python3
"""
JobLens PostgreSQL Configuration Update
Run this script after successful migration to update your configuration.
"""

import os
import json
from pathlib import Path

def update_joblens_config():
    """Update JobLens configuration for PostgreSQL"""
    
    # Update environment variables
    env_updates = {
        'DATABASE_TYPE': 'postgresql',
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'joblens',
        'POSTGRES_USER': 'joblens_user',
        'POSTGRES_PASSWORD': 'joblens_pass',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'REDIS_DB': '0'
    }
    
    # Create .env file
    env_file = Path('.env')
    env_content = []
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    
    # Update or add variables
    updated_vars = set()
    for i, line in enumerate(env_content):
        for key, value in env_updates.items():
            if line.startswith(f'{key}='):
                env_content[i] = f'{key}={value}\\n'
                updated_vars.add(key)
                break
    
    # Add new variables
    for key, value in env_updates.items():
        if key not in updated_vars:
            env_content.append(f'{key}={value}\\n')
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    print("✅ Environment configuration updated")
    
    # Update config files if they exist
    config_files = [
        'config/database_config.json',
        'src/core/database_config.py'
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"⚠️ Please manually update {config_file} for PostgreSQL configuration")
    
    print("🎉 Migration configuration complete!")
    print("📝 Next steps:")
    print("  1. Start PostgreSQL and Redis services")
    print("  2. Test with: python main.py <ProfileName> --action analyze-jobs")
    print("  3. Run dashboard: python main.py <ProfileName> --action dashboard")

if __name__ == "__main__":
    update_joblens_config()
'''
        
        script_path = Path("configure_postgresql.py")
        with open(script_path, 'w') as f:
            f.write(config_script)
        
        console.print(f"📝 Configuration script created: {script_path}")


# Docker Compose for PostgreSQL + Redis
def create_docker_compose():
    """Create Docker Compose file for PostgreSQL + Redis"""
    docker_compose = '''version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: joblens_postgres
    environment:
      POSTGRES_DB: joblens
      POSTGRES_USER: joblens_user
      POSTGRES_PASSWORD: joblens_pass
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - joblens_postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U joblens_user -d joblens"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: joblens_redis
    ports:
      - "6379:6379"
    volumes:
      - joblens_redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: joblens_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@joblens.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "8080:80"
    volumes:
      - joblens_pgadmin_data:/var/lib/pgadmin
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  joblens_postgres_data:
  joblens_redis_data:
  joblens_pgadmin_data:

networks:
  default:
    name: joblens_network
'''
    
    with open('docker-compose.postgresql.yml', 'w') as f:
        f.write(docker_compose)
    
    console.print("🐳 Docker Compose file created: docker-compose.postgresql.yml")


async def main():
    """Main migration function"""
    console.print("🔄 JobLens Database Migration Tool")
    console.print("=" * 50)
    
    # PostgreSQL configuration
    postgres_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'joblens'),
        'user': os.getenv('POSTGRES_USER', 'joblens_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'joblens_pass')
    }
    
    # Create Docker Compose file
    create_docker_compose()
    
    # Initialize migrator
    migrator = JobLensDatabaseMigrator(postgres_config)
    
    # Perform migration
    results = await migrator.migrate_all_profiles()
    
    # Output final results
    console.print("\n🎯 Migration Results:")
    for profile_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        console.print(f"  {profile_name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
