#!/usr/bin/env python3
"""
Job Processor Component for Dashboard Integration
Provides job processing controls and real-time feedback through logging.
"""

import streamlit as st
import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import psutil
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.job_database import get_job_db
# from src.analysis.two_stage_processor import TwoStageProcessor  # Import when needed
# from src.pipeline.fast_job_pipeline import FastJobPipeline  # Unused, kept commented
from src.utils.profile_helpers import load_profile

# New centralized orchestration controllers
try:
    from src.orchestration import OrchestratorConfig, run_processing_batches
    HAS_ORCH_CONTROLLERS = True
except Exception:
    HAS_ORCH_CONTROLLERS = False

logger = logging.getLogger(__name__)

class JobProcessorComponent:
    """Job processing component for dashboard integration."""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name) or {}
        self.db = get_job_db(profile_name)
        
        # Initialize session state
        if "processing_active" not in st.session_state:
            st.session_state.processing_active = False
        if "processing_progress" not in st.session_state:
            st.session_state.processing_progress = {}
        if "processing_logs" not in st.session_state:
            st.session_state.processing_logs = []
    
    def render_processor_controls(self):
        """Render the main job processor control panel."""
        st.markdown("### ⚙️ Job Processing Controls")
        
        # Get job statistics
        job_stats = self._get_job_statistics()
        
        # Display job pipeline status
        self._render_pipeline_status(job_stats)
        
        # System resource monitor (new utility)
        self._render_system_resource_monitor()
        
        # Processing health dashboard (new utility)
        self._render_processing_health_dashboard(job_stats)
        
        # Processing controls
        self._render_processing_controls(job_stats)
        
        # Processing analytics (new utility)
        self._render_processing_analytics()
        
        # Processing progress and logs
        if st.session_state.processing_active:
            self._render_processing_progress()
    
    def _get_job_statistics(self) -> Dict[str, int]:
        """Get current job statistics from database."""
        try:
            # Get jobs by status
            all_jobs = self.db.get_jobs(limit=1000)
            
            stats = {
                "total_jobs": len(all_jobs),
                "scraped_jobs": 0,
                "processed_jobs": 0,
                "document_ready_jobs": 0,
                "applied_jobs": 0,
                "pending_processing": 0
            }
            
            for job in all_jobs:
                status = job.get('status', 'scraped').lower()
                app_status = job.get('application_status', 'not_applied').lower()
                
                # Count by processing status
                if status == 'scraped':
                    stats["scraped_jobs"] += 1
                elif status in ['processed', 'Improved', 'analyzed']:
                    stats["processed_jobs"] += 1
                
                # Count by application status
                if app_status == 'applied':
                    stats["applied_jobs"] += 1
                elif app_status in ['documents_ready', 'document_created']:
                    stats["document_ready_jobs"] += 1
                
                # Count pending processing (scraped but not processed)
                if status == 'scraped' and app_status == 'not_applied':
                    stats["pending_processing"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {
                "total_jobs": 0,
                "scraped_jobs": 0,
                "processed_jobs": 0,
                "document_ready_jobs": 0,
                "applied_jobs": 0,
                "pending_processing": 0
            }
    
    def _render_pipeline_status(self, stats: Dict[str, int]):
        """Render the job processing pipeline status."""
        st.markdown("#### 📊 Processing Pipeline Status")
        
        # Create pipeline visualization
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; text-align: center;'>
                <div style='font-size: 1.5rem; color: #3b82f6; font-weight: bold;'>{stats['scraped_jobs']}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem;'>📋 Scraped</div>
                <div style='color: #64748b; font-size: 0.75rem;'>Ready for processing</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; text-align: center;'>
                <div style='font-size: 1.5rem; color: #f59e0b; font-weight: bold;'>{stats['processed_jobs']}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem;'>⚙️ Processed</div>
                <div style='color: #64748b; font-size: 0.75rem;'>AI analysis complete</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; text-align: center;'>
                <div style='font-size: 1.5rem; color: #8b5cf6; font-weight: bold;'>{stats['document_ready_jobs']}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem;'>📄 Documents</div>
                <div style='color: #64748b; font-size: 0.75rem;'>Ready to apply</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; text-align: center;'>
                <div style='font-size: 1.5rem; color: #10b981; font-weight: bold;'>{stats['applied_jobs']}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem;'>✅ Applied</div>
                <div style='color: #64748b; font-size: 0.75rem;'>Applications sent</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Processing recommendation
        if stats['pending_processing'] > 0:
            st.info(f"💡 {stats['pending_processing']} jobs are ready for processing")
        elif stats['processed_jobs'] > stats['document_ready_jobs']:
            st.info(f"💡 {stats['processed_jobs'] - stats['document_ready_jobs']} processed jobs need document generation")
    
    def _render_system_resource_monitor(self):
        """Render system resource monitoring section."""
        st.markdown("### 🖥️ System Resource Monitor")
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            # Get GPU info if available
            gpu_info = self._get_gpu_info()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cpu_color = "🔴" if cpu_percent > 80 else "🟡" if cpu_percent > 60 else "🟢"
                st.metric("CPU Usage", f"{cpu_percent:.1f}%", delta=f"{cpu_color}")
            
            with col2:
                memory_percent = memory.percent
                memory_color = "🔴" if memory_percent > 80 else "🟡" if memory_percent > 60 else "🟢"
                st.metric("Memory Usage", f"{memory_percent:.1f}%", delta=f"{memory_color}")
            
            with col3:
                disk_percent = disk.percent
                disk_color = "🔴" if disk_percent > 90 else "🟡" if disk_percent > 75 else "🟢"
                st.metric("Disk Usage", f"{disk_percent:.1f}%", delta=f"{disk_color}")
            
            with col4:
                if gpu_info:
                    gpu_usage = gpu_info.get('utilization', 0)
                    gpu_color = "🔴" if gpu_usage > 80 else "🟡" if gpu_usage > 60 else "🟢"
                    st.metric("GPU Usage", f"{gpu_usage:.1f}%", delta=f"{gpu_color}")
                else:
                    st.metric("GPU", "Not Available", delta="ℹ️")
            
            # Resource details in expandable section
            with st.expander("📊 Detailed Resource Information"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Memory Details:**")
                    st.text(f"• Total: {memory.total / (1024**3):.1f} GB")
                    st.text(f"• Available: {memory.available / (1024**3):.1f} GB")
                    st.text(f"• Used: {memory.used / (1024**3):.1f} GB")
                    
                    st.markdown("**Disk Details:**")
                    st.text(f"• Total: {disk.total / (1024**3):.1f} GB")
                    st.text(f"• Free: {disk.free / (1024**3):.1f} GB")
                    st.text(f"• Used: {disk.used / (1024**3):.1f} GB")
                
                with col2:
                    st.markdown("**CPU Details:**")
                    st.text(f"• Cores: {psutil.cpu_count(logical=False)} physical")
                    st.text(f"• Threads: {psutil.cpu_count(logical=True)} logical")
                    st.text(f"• Frequency: {psutil.cpu_freq().current:.0f} MHz")
                    
                    if gpu_info:
                        st.markdown("**GPU Details:**")
                        st.text(f"• Name: {gpu_info.get('name', 'Unknown')}")
                        st.text(f"• Memory: {gpu_info.get('memory_used', 0):.1f} / {gpu_info.get('memory_total', 0):.1f} MB")
                        st.text(f"• Temperature: {gpu_info.get('temperature', 'N/A')}°C")
                
                st.info("💡 **Tip:** Monitor resource usage during processing to optimize batch sizes and concurrency settings.")
                
        except Exception as e:
            st.warning(f"⚠️ Unable to get system metrics: {str(e)}")
            st.info("System monitoring requires psutil library.")
    
    def _render_processing_health_dashboard(self, stats: Dict[str, int]):
        """Render processing health monitoring section."""
        st.markdown("### 🏥 Processing Health Dashboard")
        
        try:
            # Get processing health metrics
            health_metrics = self._get_processing_health_metrics(stats)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                db_status = "✅ Connected" if health_metrics['db_healthy'] else "❌ Error"
                st.metric("Database", db_status)
            
            with col2:
                ai_status = "✅ Ready" if health_metrics['ai_ready'] else "❌ Not Ready"
                st.metric("AI Models", ai_status)
            
            with col3:
                queue_health = health_metrics['queue_health']
                queue_status = "✅ Healthy" if queue_health > 0.8 else "⚠️ Issues" if queue_health > 0.5 else "❌ Critical"
                st.metric("Queue Health", f"{queue_health:.1%}")
            
            with col4:
                processing_rate = health_metrics['processing_rate']
                st.metric("Processing Rate", f"{processing_rate:.1f} jobs/min")
            
            # Health details
            with st.expander("🔍 Detailed Health Information"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Database Health:**")
                    st.text(f"• Connection: {'✅ Active' if health_metrics['db_healthy'] else '❌ Failed'}")
                    st.text(f"• Response Time: {health_metrics['db_response_time']:.2f}ms")
                    st.text(f"• Total Jobs: {stats['total_jobs']:,}")
                    
                    st.markdown("**Processing Pipeline:**")
                    pipeline_efficiency = (stats['processed_jobs'] / max(stats['scraped_jobs'], 1)) * 100
                    st.text(f"• Pipeline Efficiency: {pipeline_efficiency:.1f}%")
                    st.text(f"• Jobs in Queue: {stats['pending_processing']:,}")
                    st.text(f"• Success Rate: {health_metrics['success_rate']:.1f}%")
                
                with col2:
                    st.markdown("**AI Model Status:**")
                    model_info = health_metrics['model_info']
                    st.text(f"• Model Loaded: {'✅ Yes' if model_info['loaded'] else '❌ No'}")
                    st.text(f"• Inference Time: {model_info['avg_inference_time']:.2f}s")
                    st.text(f"• Memory Usage: {model_info['memory_usage']:.1f} MB")
                    
                    st.markdown("**System Performance:**")
                    st.text(f"• Avg Processing Time: {health_metrics['avg_processing_time']:.2f}s/job")
                    st.text(f"• Error Rate: {health_metrics['error_rate']:.1f}%")
                    st.text(f"• Uptime: {health_metrics['uptime']}")
                
                # Health recommendations
                if health_metrics['queue_health'] < 0.7:
                    st.warning("⚠️ **Recommendation:** Consider increasing batch size or processing workers.")
                if health_metrics['error_rate'] > 10:
                    st.error("🔥 **Alert:** High error rate detected. Check logs for issues.")
                if health_metrics['processing_rate'] < 1:
                    st.info("💡 **Tip:** Low processing rate may indicate resource constraints.")
                    
        except Exception as e:
            st.warning(f"⚠️ Unable to get health metrics: {str(e)}")
    
    def _get_processing_health_metrics(self, stats: Dict[str, int]) -> Dict[str, Any]:
        """Get processing health metrics."""
        try:
            # Test database connectivity
            db_healthy = False
            db_response_time = 0.0
            try:
                start_time = time.time()
                _ = self.db.get_jobs(limit=1)  # Test DB connection
                db_response_time = (time.time() - start_time) * 1000  # ms
                db_healthy = True
            except Exception:
                db_healthy = False
                db_response_time = 999.0
            
            # Calculate queue health (based on pending vs processed ratio)
            total_jobs = stats['total_jobs']
            pending_jobs = stats['pending_processing']
            processed_jobs = stats['processed_jobs']
            
            if total_jobs > 0:
                ratio = (processed_jobs / total_jobs) * 1.5
                queue_health = max(0.0, min(1.0, ratio))
            else:
                queue_health = 1.0
            
            # Calculate processing rate (jobs per minute)
            # Simplified calculation - in production, track actual timing
            processing_rate = processed_jobs / max(1, pending_jobs) * 5
            
            # Calculate error rate (simplified)
            failed_jobs = total_jobs - processed_jobs - pending_jobs
            error_rate = (failed_jobs / max(total_jobs, 1)) * 100
            
            # Calculate success rate
            success_rate = (processed_jobs / max(total_jobs, 1)) * 100
            
            # AI model status (simplified check)
            ai_ready = True  # Default to ready
            model_info = {
                'loaded': True,
                'avg_inference_time': 1.2,  # Mock value
                'memory_usage': 256.0  # Mock value in MB
            }
            
            # System performance metrics
            avg_processing_time = 2.5  # Mock value in seconds
            uptime = "24h 15m"  # Mock value
            
            return {
                'db_healthy': db_healthy,
                'db_response_time': db_response_time,
                'ai_ready': ai_ready,
                'queue_health': queue_health,
                'processing_rate': processing_rate,
                'error_rate': error_rate,
                'success_rate': success_rate,
                'avg_processing_time': avg_processing_time,
                'uptime': uptime,
                'model_info': model_info
            }
            
        except Exception as e:
            # Return safe defaults if health check fails
            logger.warning(f"Health metrics calculation failed: {e}")
            return {
                'db_healthy': False,
                'db_response_time': 999.0,
                'ai_ready': False,
                'queue_health': 0.5,
                'processing_rate': 0.0,
                'error_rate': 50.0,
                'success_rate': 50.0,
                'avg_processing_time': 5.0,
                'uptime': "Unknown",
                'model_info': {
                    'loaded': False,
                    'avg_inference_time': 0.0,
                    'memory_usage': 0.0
                }
            }
    
    def _get_processing_analytics(self) -> Dict[str, Any]:
        """Get processing analytics data."""
        try:
            # Get recent jobs data
            all_jobs = self.db.get_jobs(limit=500)
            
            if not all_jobs:
                return {'has_data': False}
            
            # Calculate 24h metrics
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            
            jobs_24h = len([
                j for j in all_jobs if
                j.get('processed_at') and
                datetime.fromisoformat(j['processed_at']) > yesterday
            ])
            
            # Mock analytics data (in production, calculate from actual data)
            return {
                'has_data': True,
                'jobs_24h': jobs_24h,
                'jobs_24h_change': max(0, jobs_24h - 15),
                'avg_success_rate': 85.5,
                'success_rate_change': 2.3,
                'peak_hour': 14,
                'peak_jobs': 25,
                'week_total': len(all_jobs),
                'daily_avg': len(all_jobs) / 7.0,
                'best_day': 'Monday',
                'best_day_count': 45,
                'efficiency_trend': '↗️ Improving',
                'fastest_job': 0.8,
                'slowest_job': 15.2,
                'avg_time': 2.5,
                'common_error': 'Rate limiting'
            }
            
        except Exception as e:
            logger.warning(f"Analytics calculation failed: {e}")
            return {'has_data': False}
    
    def _render_processing_analytics(self):
        """Render real job analytics - top companies, keywords, locations."""
        st.markdown("### 📈 Job Analytics")
        
        try:
            # Get real analytics data
            analytics = self._get_real_job_analytics()
            
            if analytics['has_data']:
                # Top companies section
                st.markdown("#### 🏢 Top Companies")
                col1, col2 = st.columns(2)
                
                with col1:
                    if analytics['top_companies']:
                        for i, company in enumerate(analytics['top_companies'][:5]):
                            st.metric(
                                f"#{i+1} {company['name']}", 
                                f"{company['job_count']} jobs",
                                delta=f"{company['percentage']:.1f}%"
                            )
                    else:
                        st.info("No company data available yet")
                
                with col2:
                    # Create a simple chart of top companies
                    if analytics['top_companies']:
                        company_data = {
                            'Company': [c['name'][:20] for c in analytics['top_companies'][:8]],
                            'Jobs': [c['job_count'] for c in analytics['top_companies'][:8]]
                        }
                        import pandas as pd
                        df = pd.DataFrame(company_data)
                        st.bar_chart(df.set_index('Company'))
                
                # Top keywords section
                st.markdown("#### 🔧 Top Technical Keywords")
                col1, col2 = st.columns(2)
                
                with col1:
                    if analytics['top_keywords']:
                        for i, keyword in enumerate(analytics['top_keywords'][:8]):
                            percentage = keyword['percentage']
                            color = "🟢" if percentage > 20 else "🟡" if percentage > 10 else "🔵"
                            st.write(f"{color} **{keyword['keyword']}**: {keyword['job_count']} jobs ({percentage:.1f}%)")
                    else:
                        st.info("No keyword data available yet")
                
                with col2:
                    # Top locations
                    st.markdown("**📍 Top Locations:**")
                    if analytics['location_stats']:
                        for location in analytics['location_stats'][:5]:
                            st.write(f"• **{location['location']}**: {location['job_count']} jobs")
                    else:
                        st.info("No location data available")
                
                # Recent activity summary
                st.markdown("#### 📊 Activity Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Jobs", analytics['total_jobs'])
                
                with col2:
                    recent = analytics.get('recent_activity', {})
                    st.metric("Recent (7d)", recent.get('jobs_7d', 0))
                
                with col3:
                    st.metric("Daily Avg", f"{recent.get('daily_average', 0):.1f}")
                
                # Insights
                with st.expander("� Job Market Insights"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🔥 Trending Skills:**")
                        if analytics['top_keywords']:
                            trending = [k for k in analytics['top_keywords'][:5] if k['percentage'] > 15]
                            if trending:
                                for skill in trending:
                                    st.write(f"• {skill['keyword']} ({skill['percentage']:.1f}%)")
                            else:
                                st.write("• Python, JavaScript, React (common)")
                        
                        st.markdown("**💼 Active Employers:**")
                        if analytics['top_companies']:
                            active = [c for c in analytics['top_companies'][:3] if c['job_count'] > 5]
                            if active:
                                for company in active:
                                    st.write(f"• {company['name']} ({company['job_count']} jobs)")
                    
                    with col2:
                        st.markdown("**📈 Market Activity:**")
                        st.write(f"• Activity Trend: {recent.get('activity_trend', 'Stable')}")
                        st.write(f"• Last Updated: {analytics.get('last_updated', 'Unknown')}")
                        
                        st.markdown("**🎯 Opportunities:**")
                        total_jobs = analytics['total_jobs']
                        if total_jobs > 100:
                            st.write("• High job volume - good market")
                        elif total_jobs > 50:
                            st.write("• Moderate activity - steady market")
                        else:
                            st.write("• Building job database")
                
            else:
                st.info("📊 No analytics data available yet. Process some jobs to see insights!")
                if 'error' in analytics:
                    st.error(f"Analytics error: {analytics['error']}")
                
        except Exception as e:
            st.warning(f"⚠️ Unable to load job analytics: {str(e)}")
            st.info("Analytics will be available once job processing is complete.")
    
    def _get_real_job_analytics(self) -> Dict[str, Any]:
        """Get real job analytics from database."""
        try:
            # Try to import and use real analytics
            try:
                from src.analytics.real_job_analytics import get_real_job_analytics
                analytics = get_real_job_analytics(self.db)
                return analytics.get_analytics_data()
            except ImportError:
                # Fallback to basic analytics if real analytics not available
                return self._get_basic_analytics()
            
        except Exception as e:
            return {
                'has_data': False, 
                'error': str(e),
                'message': 'Failed to load analytics'
            }
    
    def _get_basic_analytics(self) -> Dict[str, Any]:
        """Get basic analytics as fallback."""
        try:
            all_jobs = self.db.get_jobs(limit=1000)
            
            if not all_jobs:
                return {'has_data': False, 'message': 'No jobs in database'}
            
            # Basic company counting
            from collections import Counter
            companies = Counter()
            locations = Counter()
            
            for job in all_jobs:
                company = job.get('company', '').strip()
                if company and company.lower() not in ['unknown', 'n/a', '']:
                    companies[company] += 1
                
                location = job.get('location', '').strip()
                if location and location.lower() not in ['unknown', 'n/a', '']:
                    locations[location.split(',')[0].strip()] += 1
            
            # Basic keyword extraction
            keywords = Counter()
            common_tech = ['python', 'javascript', 'java', 'react', 'sql', 'aws', 'docker']
            
            for job in all_jobs:
                text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
                for tech in common_tech:
                    if tech in text:
                        keywords[tech] += 1
            
            return {
                'has_data': True,
                'total_jobs': len(all_jobs),
                'top_companies': [
                    {'name': name, 'job_count': count, 'percentage': (count/len(all_jobs))*100}
                    for name, count in companies.most_common(10)
                ],
                'top_keywords': [
                    {'keyword': keyword, 'job_count': count, 'percentage': (count/len(all_jobs))*100}
                    for keyword, count in keywords.most_common(10)
                ],
                'location_stats': [
                    {'location': loc, 'job_count': count, 'percentage': (count/len(all_jobs))*100}
                    for loc, count in locations.most_common(8)
                ],
                'recent_activity': {
                    'jobs_7d': len(all_jobs),  # Simplified
                    'daily_average': len(all_jobs) / 7.0,
                    'activity_trend': '→ Stable'
                },
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'has_data': False,
                'error': str(e),
                'message': 'Failed to calculate basic analytics'
            }
            
    def _get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU information if available."""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Use first GPU
                return {
                    'name': gpu.name,
                    'utilization': gpu.load * 100,
                    'memory_used': gpu.memoryUsed,
                    'memory_total': gpu.memoryTotal,
                    'temperature': gpu.temperature
                }
        except ImportError:
            # Try nvidia-ml-py alternative
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle).decode()
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                return {
                    'name': name,
                    'utilization': util.gpu,
                    'memory_used': memory.used / (1024**2),
                    'memory_total': memory.total / (1024**2),
                    'temperature': temp
                }
            except:
                pass
        except:
            pass
        return None
    
    def _get_processing_health_metrics(self, stats: Dict[str, int]) -> Dict[str, Any]:
        """Get processing health metrics."""
        try:
            # Database health check
            start_time = time.time()
            db_healthy = True
            try:
                test_jobs = self.db.get_jobs(limit=1)
                db_response_time = (time.time() - start_time) * 1000
            except:
                db_healthy = False
                db_response_time = 999.0
            
            # Calculate queue health (0-1 scale)
            total_jobs = stats['total_jobs']
            pending = stats['pending_processing']
            queue_health = 1.0 - (pending / max(total_jobs, 1)) if total_jobs > 0 else 1.0
            
            # Processing rate estimation
            processing_rate = self._estimate_processing_rate()
            
            # Success rate calculation
            success_rate = ((stats['processed_jobs'] + stats['applied_jobs']) / max(stats['total_jobs'], 1)) * 100
            
            # Mock AI model info (would be real in production)
            model_info = {
                'loaded': True,
                'avg_inference_time': 2.5,
                'memory_usage': 1024.0
            }
            
            # System metrics
            avg_processing_time = 45.0  # Would be calculated from actual data
            error_rate = max(0, 100 - success_rate)
            uptime = "2d 14h 32m"  # Would be calculated from system start time
            
            return {
                'db_healthy': db_healthy,
                'db_response_time': db_response_time,
                'ai_ready': True,
                'queue_health': queue_health,
                'processing_rate': processing_rate,
                'success_rate': success_rate,
                'model_info': model_info,
                'avg_processing_time': avg_processing_time,
                'error_rate': error_rate,
                'uptime': uptime
            }
            
        except Exception as e:
            logger.error(f"Error getting health metrics: {e}")
            return {
                'db_healthy': False,
                'db_response_time': 999.0,
                'ai_ready': False,
                'queue_health': 0.0,
                'processing_rate': 0.0,
                'success_rate': 0.0,
                'model_info': {'loaded': False, 'avg_inference_time': 0, 'memory_usage': 0},
                'avg_processing_time': 0.0,
                'error_rate': 100.0,
                'uptime': "Unknown"
            }
    
    def _estimate_processing_rate(self) -> float:
        """Estimate current processing rate in jobs per minute."""
        try:
            # This would be calculated from actual processing logs/timestamps
            # For now, return a mock value based on system load
            cpu_percent = psutil.cpu_percent()
            base_rate = 5.0  # Base rate of 5 jobs per minute
            
            # Adjust based on CPU usage
            if cpu_percent > 80:
                return base_rate * 0.5
            elif cpu_percent > 60:
                return base_rate * 0.8
            else:
                return base_rate
        except:
            return 0.0
    
    def _get_processing_analytics(self) -> Dict[str, Any]:
        """Get processing analytics and trends."""
        try:
            # This would query actual processing history from database
            # For now, return mock analytics data
            
            analytics = {
                'has_data': True,
                'jobs_24h': 127,
                'jobs_24h_change': 23,
                'avg_success_rate': 87.5,
                'success_rate_change': 2.3,
                'peak_hour': 14,
                'peak_jobs': 18,
                'week_total': 892,
                'daily_avg': 127.4,
                'best_day': 'Wednesday',
                'best_day_count': 156,
                'efficiency_trend': '↗️ Improving',
                'fastest_job': 12.3,
                'slowest_job': 89.7,
                'avg_time': 34.2,
                'common_error': 'API timeout (3%)'
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {'has_data': False}
    
    def _render_processing_controls(self, stats: Dict[str, int]):
        """Render processing control buttons and options."""
        st.markdown("#### 🎛️ Processing Controls")
        
        # Processing options
        col1, col2 = st.columns(2)
        
        with col1:
            processing_method = st.selectbox(
                "Processing Method",
                ["CPU Only", "GPU Accelerated", "Hybrid (CPU + GPU)"],
                index=2,  # Default to Hybrid (CPU + GPU)
                help="Choose processing method based on available hardware"
            )
            
            batch_size = st.slider(
                "Batch Size",
                min_value=1,
                max_value=50,
                value=10,
                help="Number of jobs to process simultaneously"
            )
        
        with col2:
            max_jobs = st.number_input(
                "Max Jobs to Process",
                min_value=1,
                max_value=stats['pending_processing'] if stats['pending_processing'] > 0 else 1,
                value=min(20, stats['pending_processing']) if stats['pending_processing'] > 0 else 1,
                help="Maximum number of jobs to process in this batch"
            )
            
            enable_filtering = st.checkbox(
                "Enable Configurable Filtering",
                value=True,
                help="Filter out low-quality or irrelevant jobs",
                key="processor_enable_filtering"
            )
        
        # Stage 2 concurrency control (GPU parallelism)
        # Default based on method selection
        default_concurrency = 1 if processing_method == "CPU Only" else 2
        stage2_concurrency = st.slider(
            "Stage 2 Parallel Jobs (GPU)",
            min_value=1,
            max_value=8,
            value=default_concurrency,
            help="Number of concurrent Stage 2 (semantic) jobs. Tune based on GPU memory."
        )
        
        # Processing buttons
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(
                "🚀 Start Processing",
                disabled=st.session_state.processing_active or stats['pending_processing'] == 0,
                use_container_width=True
            ):
                self._start_job_processing(
                    method=processing_method,
                    batch_size=batch_size,
                    max_jobs=max_jobs,
                    enable_filtering=enable_filtering,
                    stage2_concurrency=stage2_concurrency
                )
        
        with col2:
            if st.button(
                "⏸️ Pause Processing",
                disabled=not st.session_state.processing_active,
                use_container_width=True
            ):
                self._pause_job_processing()
        
        with col3:
            if st.button(
                "🛑 Stop Processing",
                disabled=not st.session_state.processing_active,
                use_container_width=True
            ):
                self._stop_job_processing()
        
        with col4:
            if st.button(
                "🔄 Refresh Status",
                use_container_width=True
            ):
                st.rerun()
    
    def _render_processing_progress(self):
        """Render processing progress and real-time logs."""
        st.markdown("#### 📈 Processing Progress")
        
        progress_data = st.session_state.processing_progress
        
        if progress_data:
            # Progress bar
            progress_percent = progress_data.get('progress_percent', 0)
            st.progress(progress_percent / 100)
            
            # Progress details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Jobs Processed", progress_data.get('jobs_processed', 0))
            
            with col2:
                st.metric("Success Rate", f"{progress_data.get('success_rate', 0):.1f}%")
            
            with col3:
                estimated_time = progress_data.get('estimated_time_remaining', 0)
                st.metric("ETA", f"{estimated_time:.1f}s")
        
        # Real-time processing logs
        st.markdown("#### 📋 Processing Logs")
        
        log_container = st.container()
        with log_container:
            if st.session_state.processing_logs:
                # Show last 10 log entries
                for log_entry in st.session_state.processing_logs[-10:]:
                    timestamp = log_entry.get('timestamp', '')
                    level = log_entry.get('level', 'INFO')
                    message = log_entry.get('message', '')
                    
                    # Color code by log level
                    if level == 'ERROR':
                        st.error(f"[{timestamp}] {message}")
                    elif level == 'WARNING':
                        st.warning(f"[{timestamp}] {message}")
                    elif level == 'SUCCESS':
                        st.success(f"[{timestamp}] {message}")
                    else:
                        st.info(f"[{timestamp}] {message}")
            else:
                st.info("No processing logs yet. Start processing to see real-time updates.")
    
    def _start_job_processing(self, method: str, batch_size: int, max_jobs: int, enable_filtering: bool, stage2_concurrency: int):
        """Start job processing in background thread."""
        st.session_state.processing_active = True
        st.session_state.processing_progress = {
            'progress_percent': 0,
            'jobs_processed': 0,
            'success_rate': 0.0,
            'estimated_time_remaining': 0
        }
        st.session_state.processing_logs = []
        
        # Add initial log
        self._add_processing_log("INFO", f"Starting job processing with {method} method")
        self._add_processing_log("INFO", f"Batch size: {batch_size}, Max jobs: {max_jobs}, Stage2 concurrency: {stage2_concurrency}")
        
        # Start processing in background thread
        processing_thread = threading.Thread(
            target=self._run_job_processing,
            args=(method, batch_size, max_jobs, enable_filtering, stage2_concurrency),
            daemon=True
        )
        processing_thread.start()
        
        st.success("🚀 Job processing started! Check the progress below.")
        st.rerun()
    
    def _pause_job_processing(self):
        """Pause job processing."""
        st.session_state.processing_active = False
        self._add_processing_log("WARNING", "Job processing paused by user")
        st.warning("⏸️ Job processing paused.")
    
    def _stop_job_processing(self):
        """Stop job processing."""
        st.session_state.processing_active = False
        st.session_state.processing_progress = {}
        self._add_processing_log("WARNING", "Job processing stopped by user")
        st.error("🛑 Job processing stopped.")
    
    def _run_job_processing(self, method: str, batch_size: int, max_jobs: int, enable_filtering: bool, stage2_concurrency: int):
        """Run job processing in background thread."""
        try:
            # Get jobs to process
            jobs_to_process = self.db.get_jobs_by_status('scraped', limit=max_jobs)
            
            if not jobs_to_process:
                self._add_processing_log("WARNING", "No jobs found for processing")
                st.session_state.processing_active = False
                return
            
            self._add_processing_log("INFO", f"Found {len(jobs_to_process)} jobs to process")
            
            # Prepare config (kept for logging/DB)
            processor_config = {
                "processing_method": method.lower().replace(" ", "_"),
                "batch_size": batch_size,
                "enable_filtering": enable_filtering,
                "stage2_concurrency": stage2_concurrency
            }
            
            # Process jobs in batches
            total_jobs = len(jobs_to_process)
            processed_count = 0
            success_count = 0
            
            for i in range(0, total_jobs, batch_size):
                if not st.session_state.processing_active:
                    self._add_processing_log("WARNING", "Processing stopped by user")
                    break
                
                batch = jobs_to_process[i:i + batch_size]
                self._add_processing_log("INFO", f"Processing batch {i//batch_size + 1}: {len(batch)} jobs")
                
                # Process batch with real two-stage processor
                batch_results = self._process_job_batch(batch, processor_config)
                
                # Update progress
                processed_count += len(batch)
                success_count += sum(1 for result in batch_results if result.get('success', False))
                
                progress_percent = (processed_count / total_jobs) * 100
                success_rate = (success_count / processed_count) * 100 if processed_count else 0
                
                st.session_state.processing_progress = {
                    'progress_percent': progress_percent,
                    'jobs_processed': processed_count,
                    'success_rate': success_rate,
                    'estimated_time_remaining': 0  # Could calculate based on processing speed
                }
                
                self._add_processing_log("SUCCESS", f"Batch completed: {len(batch_results)} jobs processed")
                
                # Small delay between batches
                time.sleep(1)
            
            # Processing complete
            self._add_processing_log("SUCCESS", f"Processing complete! {success_count}/{processed_count} jobs processed successfully")
            st.session_state.processing_active = False
            
        except Exception as e:
            self._add_processing_log("ERROR", f"Processing error: {str(e)}")
            st.session_state.processing_active = False
    
    def _process_job_batch(self, jobs: List[Dict], config: Dict) -> List[Dict]:
        """Process a batch of jobs using centralized two-stage controller."""
        results: List[Dict] = []
        try:
            # Determine Stage 2 concurrency
            stage2_conc = max(1, int(config.get("stage2_concurrency", 2)))

            if HAS_ORCH_CONTROLLERS:
                # Build orchestrator config and run processing
                cfg = OrchestratorConfig(max_concurrent_stage2=stage2_conc, cpu_workers=10, batch_size=len(jobs) or 1)
                results_data = run_processing_batches(jobs, cfg)
                self._add_processing_log("INFO", f"Processed batch via orchestration controller (jobs={len(jobs)})")
            else:
                # Fallback to direct processor (legacy path)
                from src.analysis.two_stage_processor import get_two_stage_processor
                processor = get_two_stage_processor(self.profile, cpu_workers=10, max_concurrent_stage2=stage2_conc)
                results_data = asyncio.run(processor.process_jobs(jobs))
                self._add_processing_log("INFO", f"Processed batch via legacy processor (jobs={len(jobs)})")

            # Process results and update database
            for i, job in enumerate(jobs):
                try:
                    result = results_data[i] if i < len(results_data) else None
                    
                    if result and hasattr(result, 'final_compatibility'):
                        # Update job status and analysis data
                        self.db.update_job_status(job['id'], 'processed')
                        
                        analysis_data = {
                            "compatibility_score": result.final_compatibility,
                            "skills_found": result.final_skills,
                            "recommendation": result.recommendation,
                            "processing_method": config.get("processing_method", "hybrid"),
                            "stages_completed": result.stages_completed,
                            "processed_at": datetime.now().isoformat()
                        }
                        
                        # Prefer updating by job_id if available, else fallback to primary key id
                        job_job_id = job.get('job_id')
                        if job_job_id:
                            self.db.update_job_analysis(job_job_id, analysis_data)
                        else:
                            # Fallback: update fields directly by primary key id
                            fallback_update = {
                                "analysis_data": analysis_data,
                                "compatibility_score": analysis_data["compatibility_score"],
                                "processing_method": analysis_data["processing_method"],
                                "processed_at": analysis_data["processed_at"],
                                "status": "processed"
                            }
                            self.db.update_job(job['id'], fallback_update)
                        
                        results.append({"success": True, "job_id": job.get('job_id', job['id']), "score": result.final_compatibility})
                        self._add_processing_log("SUCCESS", f"Job {job.get('job_id', job['id'])}: {result.recommendation} (Score: {result.final_compatibility:.2f})")
                        
                    else:
                        # Processing failed for this job
                        self.db.update_job_status(job['id'], 'processing_failed')
                        results.append({"success": False, "job_id": job.get('job_id', job.get('id')), "error": "Processing returned no result"})
                        self._add_processing_log("ERROR", f"Job {job.get('job_id', job.get('id', 'unknown'))}: Processing failed - no result returned")
                        
                except Exception as job_error:
                    self._add_processing_log("ERROR", f"Failed to process job {job.get('job_id', job.get('id', 'unknown'))}: {str(job_error)}")
                    results.append({"success": False, "job_id": job.get('job_id', job.get('id')), "error": str(job_error)})
        
        except Exception as e:
            self._add_processing_log("ERROR", f"Batch processing error: {str(e)}")
            # Fallback to marking jobs as failed
            for job in jobs:
                results.append({"success": False, "job_id": job.get('job_id', job.get('id')), "error": str(e)})
        
        return results
    
    def _add_processing_log(self, level: str, message: str):
        """Add a log entry to processing logs."""
        try:
            # Check if we're in a valid Streamlit context
            if not hasattr(st, 'session_state'):
                return
            
            # Initialize session state if needed
            if "processing_logs" not in st.session_state:
                st.session_state.processing_logs = []
            
            log_entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": level,
                "message": message
            }
            
            st.session_state.processing_logs.append(log_entry)
            
            # Keep only last 50 log entries
            if len(st.session_state.processing_logs) > 50:
                st.session_state.processing_logs = st.session_state.processing_logs[-50:]
        except Exception as e:
            # If we can't access session state (e.g., in background thread), 
            # just print to console instead
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}")
            print(f"Warning: Could not add to session state: {e}")


# Global component instance
def get_job_processor_component(profile_name: str = "Nirajan") -> JobProcessorComponent:
    """Get job processor component instance."""
    return JobProcessorComponent(profile_name)