import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional, Dict, List

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# System Configuration
@dataclass
class SystemConfig:
    # Concurrent Processing
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 30
    CRAWL_DELAY: int = 1
    MAX_RETRIES: int = 3

    # File Paths
    DATA_DIR: str = "data"
    CACHE_DIR: str = "data/cache"
    VECTOR_STORE_DIR: str = "data/vector_store"
    LOG_DIR: str = "logs"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# SEO Configuration
@dataclass
class SEOConfig:
    # Content Requirements
    MIN_WORD_COUNT: int = 300
    TARGET_KEYWORD_DENSITY: float = 0.02
    MIN_READABILITY_SCORE: float = 60
    
    # Meta Tags
    META_DESCRIPTION_LENGTH: int = 160
    META_TITLE_LENGTH: int = 60
    
    # Technical SEO
    MOBILE_FRIENDLY: bool = True
    HTTPS_REQUIRED: bool = True
    
    # Performance Thresholds
    MIN_PERFORMANCE_SCORE: float = 0.7
    MAX_PAGE_SIZE_MB: float = 5.0
    MAX_LOAD_TIME_SEC: float = 3.0

# Link Management Configuration
@dataclass
class LinkConfig:
    # Link Checking
    CHECK_EXTERNAL_LINKS: bool = True
    VERIFY_SSL: bool = True
    CONNECTION_TIMEOUT: int = 10
    
    # Repair Settings
    MIN_SIMILARITY_SCORE: float = 0.8
    MAX_REPAIR_SUGGESTIONS: int = 5
    USE_WAYBACK_MACHINE: bool = True
    
    # Archive Settings
    WAYBACK_MACHINE_URL: str = "http://archive.org/wayback/available"
    ARCHIVE_TODAY_URL: str = "https://archive.today/"

# Content Optimization Configuration
@dataclass
class ContentConfig:
    # AI Settings
    AI_MODEL: str = "gemini-pro"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    
    # Analysis Settings
    ANALYZE_COMPETITORS: bool = True
    NUM_COMPETITORS: int = 5
    MIN_CONTENT_SIMILARITY: float = 0.6
    
    # Optimization Settings
    OPTIMIZE_HEADINGS: bool = True
    OPTIMIZE_IMAGES: bool = True
    ENHANCE_READABILITY: bool = True

# Vector Store Configuration
@dataclass
class VectorConfig:
    MODEL_NAME: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384
    SIMILARITY_THRESHOLD: float = 0.8
    USE_GPU: bool = False
    BATCH_SIZE: int = 32

# Complete Configuration
@dataclass
class Config:
    system: SystemConfig = SystemConfig()
    seo: SEOConfig = SEOConfig()
    link: LinkConfig = LinkConfig()
    content: ContentConfig = ContentConfig()
    vector: VectorConfig = VectorConfig()

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            'system': self.system.__dict__,
            'seo': self.seo.__dict__,
            'link': self.link.__dict__,
            'content': self.content.__dict__,
            'vector': self.vector.__dict__
        }

# Create global configuration instance
config = Config()

# Create required directories
for directory in [config.system.DATA_DIR, config.system.CACHE_DIR, 
                 config.system.VECTOR_STORE_DIR, config.system.LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Validation functions
def validate_api_keys():
    """Validate required API keys are present"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    if not SERP_API_KEY:
        raise ValueError("SERP_API_KEY not found in environment variables")

def validate_config():
    """Validate configuration settings"""
    validate_api_keys()
    # Add additional validation as needed

# Initialize validation
validate_config() 