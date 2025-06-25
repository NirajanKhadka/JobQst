from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
import hashlib

@dataclass
class DataChunk:
    """Data chunk for batch processing."""
    id: str
    data: List[Dict]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    priority: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(f"{self.timestamp}{len(self.data)}".encode()).hexdigest()[:8]

@dataclass
class ProcessingMetrics:
    """Real-time processing metrics."""
    start_time: datetime = field(default_factory=datetime.now)
    records_processed: int = 0
    records_failed: int = 0
    processing_time: float = 0.0
    throughput: float = 0.0
    
    def update_throughput(self, records: int, time_taken: float):
        """Update throughput metrics."""
        self.records_processed += records
        self.processing_time += time_taken
        self.throughput = self.records_processed / self.processing_time if self.processing_time > 0 else 0