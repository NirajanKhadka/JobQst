"""
Queue management components for the AutoJobAgent Dashboard.

This module provides comprehensive queue management functionality including
Redis queue operations, job manipulation, batch operations, and queue optimization.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from src.pipeline.redis_queue import RedisQueue
from src.core.job_database import get_job_db
from src.dashboard.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)


class QueueOperation(Enum):
    """Enum for queue operations."""
    MOVE_TO_MAIN = "move_to_main"
    MOVE_TO_DEADLETTER = "move_to_deadletter"
    DELETE = "delete"
    RETRY = "retry"
    PAUSE = "pause"
    RESUME = "resume"
    CLEAR = "clear"
    REORDER = "reorder"


@dataclass
class QueueStats:
    """Data class for queue statistics."""
    timestamp: str
    queue_name: str
    main_queue_length: int
    deadletter_queue_length: int
    processing_rate: float
    average_wait_time: float
    oldest_job_age: Optional[str]
    newest_job_age: Optional[str]
    queue_health: str


@dataclass
class JobQueueItem:
    """Data class for job queue item."""
    position: int
    job_id: str
    title: str
    company: str
    queued_at: str
    retry_count: int
    correlation_id: Optional[str]
    priority: int
    estimated_processing_time: float
    raw_data: str


@dataclass
class BatchOperationResult:
    """Data class for batch operation results."""
    operation: str
    total_items: int
    successful: int
    failed: int
    errors: List[str]
    duration_seconds: float
    timestamp: str


class QueueManager:
    """
    Comprehensive queue management system.
    
    Features:
    - Queue statistics and monitoring
    - Job manipulation and batch operations
    - Queue optimization and reordering
    - Dead-letter queue management
    - Queue health monitoring
    - Performance analytics
    """
    
    def __init__(self, default_queue: str = "jobs:main"):
        self.default_queue = default_queue
        self.operation_history = []
        self.queue_snapshots = []
        
        logger.info(f"Queue manager initialized for queue: {default_queue}")
    
    async def get_queue_stats(self, queue_name: Optional[str] = None) -> QueueStats:
        """
        Get comprehensive queue statistics.
        
        Args:
            queue_name: Name of the queue to analyze
            
        Returns:
            QueueStats containing detailed queue information
        """
        queue_name = queue_name or self.default_queue
        
        try:
            redis_queue = RedisQueue(queue_name=queue_name)
            await redis_queue.connect()
            
            # Get basic queue lengths
            main_length = await redis_queue.redis.llen(queue_name)
            deadletter_length = await redis_queue.redis.llen(redis_queue.deadletter_name)
            
            # Get oldest and newest job timestamps
            oldest_job_age = None
            newest_job_age = None
            
            if main_length > 0:
                # Get oldest job (first in queue)
                oldest_job_data = await redis_queue.redis.lindex(queue_name, 0)
                if oldest_job_data:
                    try:
                        oldest_job = json.loads(oldest_job_data)
                        oldest_job_age = oldest_job.get("queued_at", oldest_job.get("created_at"))
                    except:
                        pass
                
                # Get newest job (last in queue)
                newest_job_data = await redis_queue.redis.lindex(queue_name, -1)
                if newest_job_data:
                    try:
                        newest_job = json.loads(newest_job_data)
                        newest_job_age = newest_job.get("queued_at", newest_job.get("created_at"))
                    except:
                        pass
            
            # Calculate processing rate (jobs per minute)
            processing_rate = await self._calculate_processing_rate(queue_name)
            
            # Calculate average wait time
            average_wait_time = await self._calculate_average_wait_time(queue_name)
            
            # Determine queue health
            queue_health = self._determine_queue_health(main_length, deadletter_length, processing_rate)
            
            await redis_queue.close()
            
            return QueueStats(
                timestamp=datetime.now().isoformat(),
                queue_name=queue_name,
                main_queue_length=main_length,
                deadletter_queue_length=deadletter_length,
                processing_rate=processing_rate,
                average_wait_time=average_wait_time,
                oldest_job_age=oldest_job_age,
                newest_job_age=newest_job_age,
                queue_health=queue_health
            )
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return QueueStats(
                timestamp=datetime.now().isoformat(),
                queue_name=queue_name,
                main_queue_length=0,
                deadletter_queue_length=0,
                processing_rate=0.0,
                average_wait_time=0.0,
                oldest_job_age=None,
                newest_job_age=None,
                queue_health="error"
            )
    
    async def get_queue_contents(self, queue_name: Optional[str] = None, 
                               queue_type: str = "main", limit: int = 50, 
                               offset: int = 0) -> Dict[str, Any]:
        """
        Get contents of a queue with pagination.
        
        Args:
            queue_name: Name of the queue
            queue_type: Type of queue ("main" or "deadletter")
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            Dictionary containing queue contents
        """
        queue_name = queue_name or self.default_queue
        
        try:
            redis_queue = RedisQueue(queue_name=queue_name)
            await redis_queue.connect()
            
            # Determine actual queue name
            actual_queue_name = queue_name if queue_type == "main" else redis_queue.deadletter_name
            
            # Get total length
            total_length = await redis_queue.redis.llen(actual_queue_name)
            
            # Get items with pagination
            end_index = offset + limit - 1
            items_data = await redis_queue.redis.lrange(actual_queue_name, offset, end_index)
            
            # Parse items
            items = []
            for i, item_data in enumerate(items_data):
                try:
                    job_data = json.loads(item_data)
                    
                    item = JobQueueItem(
                        position=offset + i,
                        job_id=job_data.get("job_id", f"unknown_{i}"),
                        title=job_data.get("title", "Unknown"),
                        company=job_data.get("company", "Unknown"),
                        queued_at=job_data.get("queued_at", job_data.get("created_at", datetime.now().isoformat())),
                        retry_count=job_data.get("retry_count", 0),
                        correlation_id=job_data.get("correlation_id"),
                        priority=job_data.get("priority", 0),
                        estimated_processing_time=job_data.get("estimated_processing_time", 30.0),
                        raw_data=item_data
                    )
                    
                    items.append(item)
                    
                except json.JSONDecodeError:
                    # Handle corrupted data
                    item = JobQueueItem(
                        position=offset + i,
                        job_id=f"corrupted_{i}",
                        title="Corrupted Data",
                        company="Unknown",
                        queued_at=datetime.now().isoformat(),
                        retry_count=0,
                        correlation_id=None,
                        priority=0,
                        estimated_processing_time=0.0,
                        raw_data=item_data
                    )
                    items.append(item)
            
            await redis_queue.close()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "queue_name": queue_name,
                "queue_type": queue_type,
                "total_items": total_length,
                "returned_items": len(items),
                "offset": offset,
                "limit": limit,
                "has_more": (offset + len(items)) < total_length,
                "items": [asdict(item) for item in items]
            }
            
        except Exception as e:
            logger.error(f"Error getting queue contents: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "items": []
            }
    
    async def perform_batch_operation(self, operation: QueueOperation, 
                                    job_positions: List[int], 
                                    queue_name: Optional[str] = None,
                                    source_queue_type: str = "main",
                                    target_queue_type: Optional[str] = None) -> BatchOperationResult:
        """
        Perform batch operations on queue items.
        
        Args:
            operation: Type of operation to perform
            job_positions: List of job positions to operate on
            queue_name: Name of the queue
            source_queue_type: Source queue type ("main" or "deadletter")
            target_queue_type: Target queue type for move operations
            
        Returns:
            BatchOperationResult containing operation results
        """
        queue_name = queue_name or self.default_queue
        start_time = datetime.now()
        
        try:
            redis_queue = RedisQueue(queue_name=queue_name)
            await redis_queue.connect()
            
            # Determine queue names
            source_queue = queue_name if source_queue_type == "main" else redis_queue.deadletter_name
            target_queue = None
            
            if target_queue_type:
                target_queue = queue_name if target_queue_type == "main" else redis_queue.deadletter_name
            
            successful = 0
            failed = 0
            errors = []
            
            # Sort positions in reverse order for deletion operations
            if operation in [QueueOperation.DELETE, QueueOperation.MOVE_TO_MAIN, QueueOperation.MOVE_TO_DEADLETTER]:
                job_positions = sorted(job_positions, reverse=True)
            
            for position in job_positions:
                try:
                    if operation == QueueOperation.DELETE:
                        # Get item and remove it
                        item_data = await redis_queue.redis.lindex(source_queue, position)
                        if item_data:
                            await redis_queue.redis.lrem(source_queue, 1, item_data)
                            successful += 1
                        else:
                            failed += 1
                            errors.append(f"Item at position {position} not found")
                    
                    elif operation == QueueOperation.MOVE_TO_MAIN:
                        if source_queue_type != "main":
                            item_data = await redis_queue.redis.lindex(source_queue, position)
                            if item_data:
                                # Remove from source and add to target
                                await redis_queue.redis.lrem(source_queue, 1, item_data)
                                await redis_queue.redis.rpush(queue_name, item_data)
                                successful += 1
                            else:
                                failed += 1
                                errors.append(f"Item at position {position} not found")
                        else:
                            failed += 1
                            errors.append(f"Item at position {position} already in main queue")
                    
                    elif operation == QueueOperation.MOVE_TO_DEADLETTER:
                        if source_queue_type != "deadletter":
                            item_data = await redis_queue.redis.lindex(source_queue, position)
                            if item_data:
                                # Remove from source and add to deadletter
                                await redis_queue.redis.lrem(source_queue, 1, item_data)
                                await redis_queue.redis.rpush(redis_queue.deadletter_name, item_data)
                                successful += 1
                            else:
                                failed += 1
                                errors.append(f"Item at position {position} not found")
                        else:
                            failed += 1
                            errors.append(f"Item at position {position} already in dead-letter queue")
                    
                    elif operation == QueueOperation.RETRY:
                        item_data = await redis_queue.redis.lindex(source_queue, position)
                        if item_data:
                            try:
                                job_data = json.loads(item_data)
                                # Update retry information
                                job_data["retry_count"] = job_data.get("retry_count", 0) + 1
                                job_data["retried_at"] = datetime.now().isoformat()
                                job_data["correlation_id"] = str(uuid.uuid4())
                                
                                # Remove from current position and add to main queue
                                await redis_queue.redis.lrem(source_queue, 1, item_data)
                                await redis_queue.redis.rpush(queue_name, json.dumps(job_data))
                                successful += 1
                            except json.JSONDecodeError:
                                failed += 1
                                errors.append(f"Corrupted data at position {position}")
                        else:
                            failed += 1
                            errors.append(f"Item at position {position} not found")
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Error processing position {position}: {str(e)}")
            
            await redis_queue.close()
            
            # Record operation in history
            duration = (datetime.now() - start_time).total_seconds()
            result = BatchOperationResult(
                operation=operation.value,
                total_items=len(job_positions),
                successful=successful,
                failed=failed,
                errors=errors,
                duration_seconds=duration,
                timestamp=start_time.isoformat()
            )
            
            self.operation_history.append(result)
            if len(self.operation_history) > 100:  # Keep last 100 operations
                self.operation_history = self.operation_history[-100:]
            
            # Broadcast operation result
            await websocket_manager.broadcast({
                "type": "queue_operation_completed",
                "result": asdict(result)
            })
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error performing batch operation: {e}")
            return BatchOperationResult(
                operation=operation.value,
                total_items=len(job_positions),
                successful=0,
                failed=len(job_positions),
                errors=[str(e)],
                duration_seconds=duration,
                timestamp=start_time.isoformat()
            )
    
    async def clear_queue(self, queue_name: Optional[str] = None, 
                         queue_type: str = "deadletter") -> Dict[str, Any]:
        """
        Clear all items from a queue.
        
        Args:
            queue_name: Name of the queue
            queue_type: Type of queue to clear ("main" or "deadletter")
            
        Returns:
            Dictionary containing clear operation results
        """
        queue_name = queue_name or self.default_queue
        
        try:
            redis_queue = RedisQueue(queue_name=queue_name)
            await redis_queue.connect()
            
            # Determine actual queue name
            actual_queue_name = queue_name if queue_type == "main" else redis_queue.deadletter_name
            
            # Get count before clearing
            items_count = await redis_queue.redis.llen(actual_queue_name)
            
            # Clear the queue
            await redis_queue.redis.delete(actual_queue_name)
            
            await redis_queue.close()
            
            result = {
                "success": True,
                "queue_name": queue_name,
                "queue_type": queue_type,
                "items_removed": items_count,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast clear operation
            await websocket_manager.broadcast({
                "type": "queue_cleared",
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def reorder_queue(self, queue_name: Optional[str] = None, 
                           new_order: List[int] = None,
                           sort_by: str = "priority") -> Dict[str, Any]:
        """
        Reorder queue items based on criteria.
        
        Args:
            queue_name: Name of the queue
            new_order: Specific order of positions (if provided)
            sort_by: Sorting criteria ("priority", "retry_count", "queued_at")
            
        Returns:
            Dictionary containing reorder operation results
        """
        queue_name = queue_name or self.default_queue
        
        try:
            redis_queue = RedisQueue(queue_name=queue_name)
            await redis_queue.connect()
            
            # Get all items from queue
            all_items = await redis_queue.redis.lrange(queue_name, 0, -1)
            
            if not all_items:
                await redis_queue.close()
                return {
                    "success": True,
                    "message": "Queue is empty",
                    "items_reordered": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Parse items for sorting
            parsed_items = []
            for i, item_data in enumerate(all_items):
                try:
                    job_data = json.loads(item_data)
                    parsed_items.append({
                        "original_position": i,
                        "data": job_data,
                        "raw": item_data
                    })
                except json.JSONDecodeError:
                    # Keep corrupted items at the end
                    parsed_items.append({
                        "original_position": i,
                        "data": {"priority": -1, "retry_count": 999, "queued_at": "9999-12-31"},
                        "raw": item_data
                    })
            
            # Sort items based on criteria
            if new_order:
                # Use specific order provided
                reordered_items = []
                for pos in new_order:
                    if 0 <= pos < len(parsed_items):
                        reordered_items.append(parsed_items[pos])
            else:
                # Sort by criteria
                if sort_by == "priority":
                    parsed_items.sort(key=lambda x: x["data"].get("priority", 0), reverse=True)
                elif sort_by == "retry_count":
                    parsed_items.sort(key=lambda x: x["data"].get("retry_count", 0))
                elif sort_by == "queued_at":
                    parsed_items.sort(key=lambda x: x["data"].get("queued_at", ""))
                
                reordered_items = parsed_items
            
            # Clear queue and add items in new order
            await redis_queue.redis.delete(queue_name)
            
            for item in reordered_items:
                await redis_queue.redis.rpush(queue_name, item["raw"])
            
            await redis_queue.close()
            
            result = {
                "success": True,
                "queue_name": queue_name,
                "sort_by": sort_by,
                "items_reordered": len(reordered_items),
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast reorder operation
            await websocket_manager.broadcast({
                "type": "queue_reordered",
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error reordering queue: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of queue operations."""
        history = self.operation_history[-limit:] if self.operation_history else []
        return [asdict(op) for op in history]
    
    async def _calculate_processing_rate(self, queue_name: str) -> float:
        """Calculate processing rate in jobs per minute."""
        try:
            # This would typically integrate with metrics collection
            # For now, return a placeholder calculation
            return 0.0
        except Exception:
            return 0.0
    
    async def _calculate_average_wait_time(self, queue_name: str) -> float:
        """Calculate average wait time for jobs in queue."""
        try:
            # This would typically analyze job timestamps
            # For now, return a placeholder calculation
            return 0.0
        except Exception:
            return 0.0
    
    def _determine_queue_health(self, main_length: int, deadletter_length: int, 
                               processing_rate: float) -> str:
        """Determine overall queue health."""
        if deadletter_length > 50:
            return "critical"
        elif main_length > 1000 or deadletter_length > 10:
            return "degraded"
        elif processing_rate < 1.0 and main_length > 100:
            return "slow"
        else:
            return "healthy"


# Global queue manager instance
queue_manager = QueueManager()