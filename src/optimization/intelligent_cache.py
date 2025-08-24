"""
Intelligent Cache for HTML fetches and embeddings
Enhanced implementation following AI_STRATEGY_ANALYSIS.md
Profile-aware caching with dashboard analytics support
"""
import hashlib
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cachetools import LRUCache

logger = logging.getLogger(__name__)

# Legacy compatibility caches
HTML_CACHE = LRUCache(maxsize=2000)
EMBED_CACHE = LRUCache(maxsize=2000)


class IntelligentCache:
    """
    Intelligent caching system for HTML content and embeddings.
    
    Features:
    - Content-based hashing for cache keys
    - Profile-aware caching and statistics
    - Dashboard analytics integration
    - Automatic expiration and cleanup
    """
    
    def __init__(self, cache_dir: str = "cache", 
                 html_ttl_hours: int = 24,
                 embedding_ttl_hours: int = 168):  # 1 week
        """Initialize cache system"""
        self.cache_dir = Path(cache_dir)
        self.html_dir = self.cache_dir / "html"
        self.embedding_dir = self.cache_dir / "embeddings"
        self.metadata_dir = self.cache_dir / "metadata"
        
        # Create directories
        for dir_path in [self.html_dir, self.embedding_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.html_ttl = timedelta(hours=html_ttl_hours)
        self.embedding_ttl = timedelta(hours=embedding_ttl_hours)
        
        # Statistics for dashboard
        self._stats = {
            'html_hits': 0,
            'html_misses': 0,
            'embedding_hits': 0,
            'embedding_misses': 0,
            'total_cached_items': 0,
            'cache_size_mb': 0.0
        }
        
        logger.info(f"Intelligent cache initialized at {self.cache_dir}")
    
    def text_hash(self, title: str, company: str, description: str) -> str:
        """Generate hash for job content (backward compatibility)"""
        s = (title or "") + "|" + (company or "") + "|" + (description or "")
        return hashlib.sha256(" ".join(s.split()).lower().encode()).hexdigest()
    
    def cache_html(self, text_h: str, html: str, profile: str = "default"):
        """Cache HTML with profile awareness"""
        try:
            HTML_CACHE[text_h] = html
            
            # Enhanced caching with metadata
            html_path = self.html_dir / f"{text_h}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Store metadata for dashboard analytics
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'profile': profile,
                'content_hash': text_h,
                'content_length': len(html),
                'cache_type': 'html'
            }
            
            metadata_path = self.metadata_dir / f"{text_h}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            self._stats['total_cached_items'] += 1
            logger.debug(f"Cached HTML for profile {profile}: {text_h}")
            
        except Exception as e:
            logger.error(f"Failed to cache HTML: {e}")
    
    def get_cached_html(self, text_h: str) -> Optional[str]:
        """Get cached HTML with hit/miss tracking"""
        result = HTML_CACHE.get(text_h)
        if result:
            self._stats['html_hits'] += 1
            logger.debug(f"Cache hit for HTML: {text_h}")
        else:
            self._stats['html_misses'] += 1
            # Try file cache
            try:
                html_path = self.html_dir / f"{text_h}.html"
                if html_path.exists():
                    with open(html_path, 'r', encoding='utf-8') as f:
                        result = f.read()
                    HTML_CACHE[text_h] = result  # Update memory cache
                    self._stats['html_hits'] += 1
            except Exception as e:
                logger.error(f"Error reading cached HTML: {e}")
        
        return result
    
    def cache_embedding(self, text_h: str, model: str, emb, 
                       profile: str = "default"):
        """Cache embedding with profile and model tracking"""
        try:
            key = f"{text_h}:{model}"
            EMBED_CACHE[key] = emb
            
            # Enhanced caching with persistence
            embedding_path = self.embedding_dir / f"{key.replace(':', '_')}.pkl"
            with open(embedding_path, 'wb') as f:
                pickle.dump(emb, f)
            
            # Store metadata for dashboard analytics
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'profile': profile,
                'content_hash': text_h,
                'model_name': model,
                'cache_type': 'embedding'
            }
            
            metadata_path = self.metadata_dir / f"{key.replace(':', '_')}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            self._stats['total_cached_items'] += 1
            logger.debug(f"Cached embedding for profile {profile}: {key}")
            
        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
    
    def get_cached_embedding(self, text_h: str, model: str):
        """Get cached embedding with hit/miss tracking"""
        key = f"{text_h}:{model}"
        result = EMBED_CACHE.get(key)
        
        if result is not None:
            self._stats['embedding_hits'] += 1
            logger.debug(f"Cache hit for embedding: {key}")
        else:
            self._stats['embedding_misses'] += 1
            # Try file cache
            try:
                embedding_path = self.embedding_dir / f"{key.replace(':', '_')}.pkl"
                if embedding_path.exists():
                    with open(embedding_path, 'rb') as f:
                        result = pickle.load(f)
                    EMBED_CACHE[key] = result  # Update memory cache
                    self._stats['embedding_hits'] += 1
            except Exception as e:
                logger.error(f"Error reading cached embedding: {e}")
        
        return result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for dashboard"""
        total_html = self._stats['html_hits'] + self._stats['html_misses']
        total_embedding = (self._stats['embedding_hits'] + 
                          self._stats['embedding_misses'])
        
        stats = self._stats.copy()
        stats.update({
            'html_hit_rate': (self._stats['html_hits'] / max(total_html, 1)),
            'embedding_hit_rate': (self._stats['embedding_hits'] / 
                                  max(total_embedding, 1)),
            'total_html_items': len(HTML_CACHE),
            'total_embedding_items': len(EMBED_CACHE),
            'cache_size_mb': self._calculate_cache_size()
        })
        return stats
    
    def _calculate_cache_size(self) -> float:
        """Calculate cache size for dashboard display"""
        try:
            total_size = 0
            if self.cache_dir.exists():
                for file_path in self.cache_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache items"""
        cleaned_count = 0
        try:
            current_time = datetime.now()
            
            # Check metadata files for expiration
            for metadata_path in self.metadata_dir.glob('*.json'):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    cached_time = datetime.fromisoformat(metadata['timestamp'])
                    cache_type = metadata.get('cache_type', 'html')
                    ttl = self.html_ttl if cache_type == 'html' else self.embedding_ttl
                    
                    if current_time - cached_time > ttl:
                        # Remove expired item
                        content_hash = metadata.get('content_hash', '')
                        if cache_type == 'html':
                            html_path = self.html_dir / f"{content_hash}.html"
                            if html_path.exists():
                                html_path.unlink()
                        else:
                            model = metadata.get('model_name', 'default')
                            key = f"{content_hash}:{model}"
                            embedding_path = self.embedding_dir / f"{key.replace(':', '_')}.pkl"
                            if embedding_path.exists():
                                embedding_path.unlink()
                        
                        metadata_path.unlink()
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {metadata_path}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} expired cache items")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
            return 0


# Global cache instance for dashboard integration
_cache_instance = None


def get_cache() -> IntelligentCache:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IntelligentCache()
    return _cache_instance


# Legacy compatibility functions
def text_hash(title: str, company: str, description: str) -> str:
    """Legacy function - delegates to cache instance"""
    return get_cache().text_hash(title, company, description)


def cache_html(text_h: str, html: str):
    """Legacy function - delegates to cache instance"""
    get_cache().cache_html(text_h, html)


def get_cached_html(text_h: str) -> Optional[str]:
    """Legacy function - delegates to cache instance"""
    return get_cache().get_cached_html(text_h)


def cache_embedding(text_h: str, model: str, emb):
    """Legacy function - delegates to cache instance"""
    get_cache().cache_embedding(text_h, model, emb)


def get_cached_embedding(text_h: str, model: str):
    """Legacy function - delegates to cache instance"""
    return get_cache().get_cached_embedding(text_h, model)
