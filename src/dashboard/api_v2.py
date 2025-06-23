"""
Enhanced Dashboard API v2 - Performance Optimized
Features:
- Caching for expensive operations
- Reduced polling frequency
- WebSocket for real-time updates
- Connection pooling
- Background job processing
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import threading
from pathlib import Path
import os
import uvicorn
from functools import lru_cache
from cachetools import TTLCache
from src.utils.enhanced_database_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardAPIv2:
    def __init__(self, profile_name: str = "default"):
        self.app = FastAPI(title="AutoJobAgent Dashboard v2", version="2.0.0")
        self.profile_name = profile_name
        self.cache = TTLCache(maxsize=100, ttl=300)
        self.cache_timestamps = {}
        self.cache_duration = 30  # seconds
        self.websocket_connections = []
        self.background_tasks = {}
        self.db_connections = {}
        self.db_lock = threading.Lock()
        self.db_manager = DatabaseManager(self.profile_name)
        
        # Setup routes
        self._setup_routes()
        
        # Start background tasks
        self.start_background_tasks()
    
    def _setup_routes(self):
        """Setup API routes with caching and optimization."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Serve the main dashboard page."""
            return self.get_dashboard_html()
        
        @self.app.get("/api/health")
        async def health_check():
            """Basic health check endpoint."""
            return {
                "status": "ok",
                "version": "2.0",
                "profile": self.profile_name,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get basic stats."""
            return self.fetch_basic_stats()
        
        @self.app.get("/api/jobs")
        async def get_jobs(limit: int = 20, offset: int = 0, site: Optional[str] = None):
            """Get jobs with caching."""
            cache_key = f"jobs_{limit}_{offset}_{site}"
            return await self.get_cached_data(cache_key, 
                                            lambda: self.fetch_jobs(limit, offset, site))
        
        @self.app.get("/api/jobs-table")
        async def get_jobs_table(limit: int = 20, offset: int = 0):
            """Get jobs in table format."""
            cache_key = f"jobs_table_{limit}_{offset}"
            return await self.get_cached_data(cache_key,
                                            lambda: self.fetch_jobs_table(limit, offset))
        
        @self.app.get("/api/comprehensive-stats")
        async def get_comprehensive_stats():
            """Get comprehensive stats with long cache duration."""
            return await self.get_cached_data("comprehensive_stats", 
                                            self.fetch_comprehensive_stats,
                                            cache_duration=60)  # 1 minute cache
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates."""
            await self.handle_websocket(websocket)
        
        @self.app.post("/api/process-jobs")
        async def process_jobs():
            """Trigger background job processing."""
            return await self.trigger_job_processing()
    
    async def get_cached_data(self, key: str, fetch_func, cache_duration: Optional[int] = None):
        """Get data from cache or fetch if expired."""
        current_cache_duration = cache_duration if cache_duration is not None else self.cache_duration
        
        # Check if cache is valid
        if key in self.cache_timestamps:
            age = time.time() - self.cache_timestamps[key]
            if age < current_cache_duration:
                logger.info(f"Cache hit for {key} (age: {age:.1f}s)")
                return self.cache[key]
        
        # Fetch new data
        logger.info(f"Cache miss for {key}, fetching fresh data")
        try:
            data = await self.run_in_executor(fetch_func)
            self.cache[key] = data
            self.cache_timestamps[key] = time.time()
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {key}: {e}")
            # Return cached data if available, even if expired
            if key in self.cache:
                logger.warning(f"Returning stale cache for {key}")
                return self.cache[key]
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_cached_stats(self, profile_name: str) -> Dict[str, Any]:
        """Get cached stats for a profile."""
        cache_key = f"stats_{profile_name}"
        return await self.get_cached_data(cache_key, lambda: self.get_profile_stats(profile_name))

    def fetch_basic_stats(self):
        """Fetch basic system stats."""
        try:
            stats = self.db_manager.get_stats()
            return stats
        except Exception as e:
            logger.error(f"Error fetching basic stats: {e}")
            return {}
    
    async def fetch_comprehensive_stats(self):
        """Fetch comprehensive stats for all profiles."""
        try:
            stats = {
                "timestamp": datetime.now().isoformat(),
                "profiles": {},
                "system": {
                    "cache_size": len(self.cache),
                    "active_connections": len(self.websocket_connections),
                    "background_tasks": len(self.background_tasks)
                }
            }
            
            # Get stats for current profile
            current_stats = self.fetch_basic_stats()
            stats["profiles"][self.profile_name] = current_stats
            
            # Get stats for other profiles
            profiles_dir = Path("profiles")
            if profiles_dir.exists():
                for profile_dir in profiles_dir.iterdir():
                    if profile_dir.is_dir() and profile_dir.name != self.profile_name:
                        try:
                            profile_stats = await self.get_cached_stats(profile_dir.name)
                            stats["profiles"][profile_dir.name] = profile_stats
                        except Exception as e:
                            logger.warning(f"Could not get stats for profile {profile_dir.name}: {e}")
            
            return stats
        except Exception as e:
            logger.error(f"Error fetching comprehensive stats: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_profile_stats(self, profile_name: str):
        """Get stats for a specific profile."""
        try:
            db_path = f"profiles/{profile_name}/{profile_name}.db"
            if not os.path.exists(db_path):
                return {"total_jobs": 0, "jobs_by_site": {}, "recent_jobs": 0}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if jobs table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
            if not cursor.fetchone():
                conn.close()
                return {"total_jobs": 0, "jobs_by_site": {}, "recent_jobs": 0}
            
            # Get stats
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            
            cursor.execute("SELECT site, COUNT(*) FROM jobs GROUP BY site")
            jobs_by_site = dict(cursor.fetchall())
            
            cursor.execute("""
                SELECT COUNT(*) FROM jobs 
                WHERE scraped_at > datetime('now', '-1 day')
            """)
            recent_jobs = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_jobs": total_jobs,
                "jobs_by_site": jobs_by_site,
                "recent_jobs": recent_jobs
            }
        except Exception as e:
            logger.error(f"Error getting stats for profile {profile_name}: {e}")
            return {"total_jobs": 0, "jobs_by_site": {}, "recent_jobs": 0, "error": str(e)}
    
    def fetch_jobs(self, limit: int = 20, offset: int = 0, site: Optional[str] = None):
        """Fetch jobs from database."""
        try:
            db = self.get_database_connection()
            cursor = db.cursor()
            
            query = "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
            params: tuple = (limit, offset)
            
            if site:
                query = "SELECT * FROM jobs WHERE site = ? ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
                params = (site, limit, offset)

            cursor.execute(query, params)
            
            columns = [description[0] for description in cursor.description]
            jobs = []
            
            for row in cursor.fetchall():
                job = dict(zip(columns, row))
                # Convert datetime objects to strings
                if 'scraped_at' in job and job['scraped_at']:
                    job['scraped_at'] = str(job['scraped_at'])
                jobs.append(job)
            
            return {
                "jobs": jobs,
                "total": len(jobs),
                "limit": limit,
                "offset": offset,
                "site": site
            }
        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            return {"jobs": [], "error": str(e)}
    
    def fetch_jobs_table(self, limit: int = 20, offset: int = 0):
        """Fetch jobs in table format."""
        jobs_data = self.fetch_jobs(limit, offset)
        
        # Format for table display
        table_data = []
        for job in jobs_data.get("jobs", []):
            table_data.append({
                "id": job.get("id"),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "site": job.get("site", ""),
                "scraped_at": job.get("scraped_at", ""),
                "url": job.get("url", "")
            })
        
        return {
            "data": table_data,
            "total": len(table_data),
            "limit": limit,
            "offset": offset
        }
    
    def get_database_connection(self):
        """Get cached database connection."""
        db_path = f"profiles/{self.profile_name}/{self.profile_name}.db"
        
        with self.db_lock:
            if db_path not in self.db_connections:
                # Ensure directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                self.db_connections[db_path] = sqlite3.connect(db_path)
                
                # Initialize database if needed
                self.initialize_database(self.db_connections[db_path])
            
            return self.db_connections[db_path]
    
    def initialize_database(self, conn):
        """Initialize database schema."""
        try:
            cursor = conn.cursor()
            
            # Create jobs table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    description TEXT,
                    url TEXT UNIQUE,
                    site TEXT,
                    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    job_hash TEXT,
                    experience_level TEXT,
                    salary_range TEXT,
                    job_type TEXT,
                    remote_work TEXT,
                    requirements TEXT,
                    benefits TEXT
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized for profile {self.profile_name}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def run_in_executor(self, func):
        """Run function in executor to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func)
    
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections for real-time updates."""
        await websocket.accept()
        self.websocket_connections.append(websocket)
        
        try:
            # Send initial data
            await websocket.send_text(json.dumps({
                "type": "connected",
                "profile": self.profile_name,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Keep connection alive and send updates
            while True:
                await asyncio.sleep(5)  # Send updates every 5 seconds
                
                # Get latest stats
                stats = await self.get_cached_stats()
                
                await websocket.send_text(json.dumps({
                    "type": "stats_update",
                    "data": stats,
                    "timestamp": datetime.now().isoformat()
                }))
                
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
    
    async def trigger_job_processing(self):
        """Trigger background job processing."""
        try:
            # Start background job processing
            task_id = f"job_processing_{int(time.time())}"
            self.background_tasks[task_id] = {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "profile": self.profile_name
            }
            
            # Run job processing in background
            asyncio.create_task(self.process_jobs_background(task_id))
            
            return {
                "status": "started",
                "task_id": task_id,
                "message": "Job processing started in background"
            }
        except Exception as e:
            logger.error(f"Error triggering job processing: {e}")
            return {"status": "error", "error": str(e)}
    
    async def process_jobs_background(self, task_id: str):
        """Process jobs in background."""
        try:
            logger.info(f"Starting background job processing for task {task_id}")
            
            # Simulate job processing
            await asyncio.sleep(2)
            
            # Update task status
            self.background_tasks[task_id]["status"] = "completed"
            self.background_tasks[task_id]["completed_at"] = datetime.now().isoformat()
            
            # Notify WebSocket clients
            await self.notify_websocket_clients({
                "type": "job_processing_complete",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Background job processing completed for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in background job processing: {e}")
            self.background_tasks[task_id]["status"] = "failed"
            self.background_tasks[task_id]["error"] = str(e)
    
    async def notify_websocket_clients(self, message: dict):
        """Notify all WebSocket clients."""
        disconnected = []
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
    
    def start_background_tasks(self):
        """Start background maintenance tasks."""
        # Note: Background tasks are disabled for now to avoid async issues
        # They can be re-enabled when running in a proper async context
        logger.info("Background tasks disabled - will be enabled when running in async context")
        
        # async def cache_cleanup():
        #     """Clean up expired cache entries."""
        #     while True:
        #         try:
        #             current_time = time.time()
        #             expired_keys = []
        #             
        #             for key, timestamp in self.cache_timestamps.items():
        #                 if current_time - timestamp > self.cache_duration * 2:  # 2x cache duration
        #                     expired_keys.append(key)
        #             
        #             for key in expired_keys:
        #                 del self.cache[key]
        #                 del self.cache_timestamps[key]
        #             
        #             if expired_keys:
        #                 logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        #             
        #             await asyncio.sleep(60)  # Run every minute
        #             
        #         except Exception as e:
        #             logger.error(f"Error in cache cleanup: {e}")
        #             await asyncio.sleep(60)
        # 
        # # Start background task
        # asyncio.create_task(cache_cleanup())
    
    def get_dashboard_html(self):
        """Get the dashboard HTML with optimized JavaScript."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoJobAgent Dashboard v2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
        .jobs-table { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }
        .jobs-table table { width: 100%; border-collapse: collapse; }
        .jobs-table th, .jobs-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        .jobs-table th { background: #34495e; color: white; }
        .jobs-table tr:hover { background: #f8f9fa; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status-online { background: #27ae60; }
        .status-offline { background: #e74c3c; }
        .loading { text-align: center; padding: 20px; color: #7f8c8d; }
        .error { background: #e74c3c; color: white; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { background: #27ae60; color: white; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AutoJobAgent Dashboard v2</h1>
            <p>Performance optimized dashboard with real-time updates</p>
            <div>
                <span class="status-indicator" id="ws-status"></span>
                <span id="connection-status">Connecting...</span>
            </div>
        </div>
        
        <div class="stats-grid" id="stats-grid">
            <div class="loading">Loading stats...</div>
        </div>
        
        <div class="jobs-table">
            <h2 style="padding: 20px; margin: 0;">Recent Jobs</h2>
            <div id="jobs-container">
                <div class="loading">Loading jobs...</div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <button onclick="processJobs()" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">
                🔄 Process Jobs
            </button>
        </div>
    </div>

    <script>
        let ws = null;
        let statsCache = {};
        let jobsCache = {};
        let lastUpdate = 0;
        
        // Initialize WebSocket connection
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                document.getElementById('ws-status').className = 'status-indicator status-online';
                document.getElementById('connection-status').textContent = 'Connected (Real-time)';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'stats_update') {
                    updateStats(data.data);
                } else if (data.type === 'job_processing_complete') {
                    showMessage('Job processing completed!', 'success');
                    loadJobs(); // Refresh jobs
                }
            };
            
            ws.onclose = function() {
                document.getElementById('ws-status').className = 'status-indicator status-offline';
                document.getElementById('connection-status').textContent = 'Disconnected';
                // Reconnect after 5 seconds
                setTimeout(initWebSocket, 5000);
            };
            
            ws.onerror = function() {
                document.getElementById('ws-status').className = 'status-indicator status-offline';
                document.getElementById('connection-status').textContent = 'Connection Error';
            };
        }
        
        // Load stats with caching
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                updateStats(stats);
            } catch (error) {
                console.error('Error loading stats:', error);
                showMessage('Error loading stats', 'error');
            }
        }
        
        // Update stats display
        function updateStats(stats) {
            const statsGrid = document.getElementById('stats-grid');
            
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${stats.total_jobs || 0}</div>
                    <div class="stat-label">Total Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.recent_jobs || 0}</div>
                    <div class="stat-label">Recent Jobs (24h)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${Object.keys(stats.jobs_by_site || {}).length}</div>
                    <div class="stat-label">Job Sites</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.profile || 'Unknown'}</div>
                    <div class="stat-label">Active Profile</div>
                </div>
            `;
        }
        
        // Load jobs with caching
        async function loadJobs() {
            try {
                const response = await fetch('/api/jobs-table?limit=10');
                const data = await response.json();
                updateJobsTable(data);
            } catch (error) {
                console.error('Error loading jobs:', error);
                showMessage('Error loading jobs', 'error');
            }
        }
        
        // Update jobs table
        function updateJobsTable(data) {
            const container = document.getElementById('jobs-container');
            
            if (data.data && data.data.length > 0) {
                let tableHtml = '<table style="width: 100%; border-collapse: collapse;">';
                tableHtml += '<tr><th>Title</th><th>Company</th><th>Location</th><th>Site</th><th>Scraped</th></tr>';
                
                data.data.forEach(job => {
                    tableHtml += `
                        <tr>
                            <td><a href="${job.url}" target="_blank">${job.title}</a></td>
                            <td>${job.company}</td>
                            <td>${job.location}</td>
                            <td>${job.site}</td>
                            <td>${new Date(job.scraped_at).toLocaleDateString()}</td>
                        </tr>
                    `;
                });
                
                tableHtml += '</table>';
                container.innerHTML = tableHtml;
            } else {
                container.innerHTML = '<div class="loading">No jobs found</div>';
            }
        }
        
        // Process jobs
        async function processJobs() {
            try {
                const response = await fetch('/api/process-jobs', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'started') {
                    showMessage('Job processing started in background', 'success');
                } else {
                    showMessage('Error starting job processing', 'error');
                }
            } catch (error) {
                console.error('Error processing jobs:', error);
                showMessage('Error processing jobs', 'error');
            }
        }
        
        // Show message
        function showMessage(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            
            const container = document.querySelector('.container');
            container.insertBefore(messageDiv, container.firstChild);
            
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
            loadStats();
            loadJobs();
            
            // Refresh stats every 30 seconds (reduced from constant polling)
            setInterval(loadStats, 30000);
        });
    </script>
</body>
</html>
        """

def create_dashboard_v2(profile_name: str, host: str = "0.0.0.0", port: int = 8002):
    """Factory function to create and run the simplified dashboard v2."""
    if not profile_name:
        profile_name = "default"
    
    dashboard_api = DashboardAPIv2(profile_name)
    
    config = uvicorn.Config(
        dashboard_api.app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    # In a real app, you'd use asyncio.run(server.serve()), 
    # but for this script to be importable, we just run it directly.
    # This will block if called from a script.
    server.run()

if __name__ == '__main__':
    create_dashboard_v2("Nirajan") 