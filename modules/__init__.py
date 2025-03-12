from .website_optimizer import WebsiteOptimizer, OptimizationResults
from .content_optimizer import ContentOptimizer, ContentOptimizationResults
from .link_manager import LinkManager, LinkStatus, RepairSuggestion
from .seo_analyzer import SEOAnalyzer, SEOAnalysisResults

__all__ = [
    # Website Optimizer
    'WebsiteOptimizer',
    'OptimizationResults',
    
    # Content Optimizer
    'ContentOptimizer',
    'ContentOptimizationResults',
    
    # Link Manager
    'LinkManager',
    'LinkStatus',
    'RepairSuggestion',
    
    # SEO Analyzer
    'SEOAnalyzer',
    'SEOAnalysisResults'
]

# Version information
__version__ = '1.0.0'

# Module level logger
import logging
logger = logging.getLogger(__name__)

# Initialize logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Module metadata
__author__ = 'Shanjan Makkar'
__description__ = 'SnapSEO: Autonomous Web Intelligence System'
__url__ = 'https://github.com/shnjnmkkr/Agent_X'

# Data classes for type hints
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ModuleConfig:
    """Configuration for module initialization"""
    debug_mode: bool = False
    max_concurrent_tasks: int = 10
    timeout: int = 30
    retry_attempts: int = 3

# Default configuration
DEFAULT_CONFIG = ModuleConfig()

def configure(config: ModuleConfig = DEFAULT_CONFIG):
    """Configure module-wide settings"""
    global _config
    _config = config
    
    if config.debug_mode:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
        
    logger.info(f"Configured {__name__} with settings: {config}")

# Initialize with default configuration
_config = DEFAULT_CONFIG 