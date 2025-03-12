from .vector_store import VectorStore
from .seo_utils import SEOUtils
from .link_utils import LinkUtils

__all__ = [
    'VectorStore',
    'SEOUtils',
    'LinkUtils'
]

# Utility configurations
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class VectorStoreConfig:
    """FAISS vector store configuration"""
    model_name: str = 'all-MiniLM-L6-v2'
    dimension: int = 384
    similarity_threshold: float = 0.8
    index_path: str = 'data/vector_store'
    batch_size: int = 32
    use_gpu: bool = False

@dataclass
class CrawlerConfig:
    """Web crawler configuration"""
    max_retries: int = 3
    timeout: int = 30
    user_agent: str = 'SnapSEO Bot 1.0'
    respect_robots: bool = True
    crawl_delay: int = 1
    max_concurrent_requests: int = 10
    max_depth: int = 3
    allowed_domains: Optional[list] = None
    excluded_patterns: Optional[list] = None

@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    ttl: int = 3600  # 1 hour
    max_size: int = 1000
    persistence_path: str = 'data/cache'

@dataclass
class UtilsConfig:
    """General utilities configuration"""
    vector_store: VectorStoreConfig = VectorStoreConfig()
    crawler: CrawlerConfig = CrawlerConfig()
    cache: CacheConfig = CacheConfig()
    debug_mode: bool = False

class Cache:
    """Simple cache implementation"""
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.config.enabled:
            return None
            
        if key in self._cache:
            timestamp = self._timestamps[key]
            if datetime.now() - timestamp < timedelta(seconds=self.config.ttl):
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None
        
    def set(self, key: str, value: Any):
        """Set value in cache"""
        if not self.config.enabled:
            return
            
        if len(self._cache) >= self.config.max_size:
            # Remove oldest entry
            oldest_key = min(self._timestamps.items(), key=lambda x: x[1])[0]
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
            
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        
    def clear(self):
        """Clear cache"""
        self._cache.clear()
        self._timestamps.clear()

# Default configurations
DEFAULT_CONFIG = UtilsConfig()

# Global cache instance
_cache = Cache(DEFAULT_CONFIG.cache)

def configure_utils(config: UtilsConfig = DEFAULT_CONFIG):
    """Configure utility-wide settings"""
    global _config, _cache
    _config = config
    
    # Update cache configuration
    _cache = Cache(config.cache)
    
    if config.debug_mode:
        logger.setLevel(logging.DEBUG)
    
    # Create necessary directories
    os.makedirs(config.vector_store.index_path, exist_ok=True)
    os.makedirs(config.cache.persistence_path, exist_ok=True)
    
    logger.info(f"Configured utilities with settings: {config}")

def get_cache() -> Cache:
    """Get cache instance"""
    return _cache

def clear_cache():
    """Clear utility cache"""
    _cache.clear()
    logger.info("Utility cache cleared")

class UtilsError(Exception):
    """Base exception for utils module"""
    pass

class CacheError(UtilsError):
    """Cache-related errors"""
    pass

class VectorStoreError(UtilsError):
    """Vector store related errors"""
    pass

class CrawlerError(UtilsError):
    """Crawler related errors"""
    pass

# Initialize with default configuration
_config = DEFAULT_CONFIG

# Export error classes
__all__ += ['UtilsError', 'CacheError', 'VectorStoreError', 'CrawlerError']

# Export configuration classes
__all__ += ['UtilsConfig', 'VectorStoreConfig', 'CrawlerConfig', 'CacheConfig']

# Export utility functions
__all__ += ['configure_utils', 'get_cache', 'clear_cache']

# Version information
__version__ = '1.0.0' 