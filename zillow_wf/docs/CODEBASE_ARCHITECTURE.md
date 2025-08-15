# Zillow Waterfront Codebase Architecture Documentation

## Overview
This document provides a comprehensive overview of the codebase architecture for the Zillow Waterfront Property Scraping project. The system is designed as a modular, scalable, and maintainable solution for extracting, processing, and storing waterfront property data from Zillow.

## System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Zillow.com   │───▶│  Zyte API Proxy  │───▶│  HTML/JSON     │
│                 │    │                  │    │  Extractor     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL   │◀───│  Data Processor  │◀───│  Cache Manager  │
│   Database     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

#### 1. **Data Extraction Layer**
- **Zyte API Integration**: Handles HTTP requests to Zillow
- **HTML Parser**: Extracts structured data from Zillow pages
- **JSON Extractor**: Parses `__NEXT_DATA__` and `gdpClientCache` payloads
- **Rate Limiting**: Manages API request frequency and timeouts

#### 2. **Data Processing Layer**
- **Field Extractor**: Maps Zillow data to database schema
- **Waterfront Analyzer**: Identifies and extracts waterfront-specific features
- **Data Validator**: Ensures data quality and consistency
- **Content Parser**: Extracts text, photos, and media content

#### 3. **Storage Layer**
- **Database Manager**: Handles PostgreSQL connections and operations
- **Cache Manager**: Stores intermediate results and HTML content
- **File Manager**: Manages local file storage and organization

#### 4. **Application Layer**
- **Command Line Interface**: Provides user interaction and configuration
- **Progress Tracking**: Monitors extraction progress and performance
- **Error Handling**: Manages failures and provides recovery options
- **Logging System**: Comprehensive logging for debugging and monitoring

## Core Classes and Components

### 1. `FlexibleWaterfrontExtractor` - Main Extractor Class

#### Purpose
Central orchestrator for the entire extraction process, handling URL processing, data extraction, and database storage.

#### Key Responsibilities
- **URL Management**: Processes search results and individual property URLs
- **Data Extraction**: Orchestrates HTML parsing and JSON extraction
- **Database Operations**: Manages data storage and updates
- **Error Handling**: Provides robust error recovery and logging
- **Performance Optimization**: Implements concurrent processing and caching

#### Architecture Pattern
```python
class FlexibleWaterfrontExtractor:
    def __init__(self, **config):
        # Configuration management
        # Database initialization
        # Cache setup
        
    async def extract_property(self, url: str):
        # Main extraction workflow
        
    async def _extract_single_property(self, url: str):
        # Individual property processing
        
    async def _extract_properties_concurrent(self, urls: List[str]):
        # Concurrent processing implementation
```

#### Key Methods
- `extract_property()`: Main entry point for property extraction
- `_extract_single_property()`: Processes individual properties
- `_extract_properties_concurrent()`: Handles concurrent processing
- `store_property_to_database()`: Manages database operations
- `_extract_all_property_urls_from_search()`: Extracts URLs from search results

### 2. **Data Extraction Components**

#### HTML Parser
```python
def _extract_from_html(self, html_content: str) -> Dict[str, Any]:
    """Extract data from HTML content using multiple strategies"""
    # BeautifulSoup parsing
    # Regex pattern matching
    # Meta tag extraction
    # Structured data extraction
```

#### JSON Extractor
```python
def _extract_from_json(self, html_content: str) -> Dict[str, Any]:
    """Extract data from embedded JSON payloads"""
    # __NEXT_DATA__ extraction
    # gdpClientCache parsing
    # Deep field searching
    # Fallback strategies
```

#### Waterfront Feature Detector
```python
def _detect_waterfront_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Identify and extract waterfront-specific features"""
    # Keyword matching
    # Regex pattern detection
    # Contextual analysis
    # Confidence scoring
```

### 3. **Database Management**

#### Connection Management
```python
class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.connection_pool = self.engine.pool
        
    def get_connection(self):
        """Get database connection from pool"""
        
    def execute_query(self, query: str, params: Dict = None):
        """Execute database query with parameters"""
```

#### Schema Management
```python
def _initialize_database(self):
    """Create database tables if they don't exist"""
    # Table creation
    # Index setup
    # Constraint definition
    # Initial data population
```

### 4. **Caching and Performance**

#### Cache Strategy
```python
class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.html_cache = {}
        self.json_cache = {}
        
    def get_cached_content(self, url: str) -> Optional[str]:
        """Retrieve cached content for URL"""
        
    def cache_content(self, url: str, content: str):
        """Cache content for future use"""
```

#### Concurrent Processing
```python
async def _extract_properties_concurrent(self, urls: List[str]) -> List[Dict]:
    """Process multiple properties concurrently"""
    semaphore = asyncio.Semaphore(self.max_concurrent_properties)
    
    async def process_url(url: str):
        async with semaphore:
            return await self._extract_single_property(url)
    
    tasks = [process_url(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Design Patterns and Principles

### 1. **Asynchronous Programming**
- **Event Loop**: Uses Python's `asyncio` for non-blocking I/O
- **Concurrent Processing**: Implements semaphore-based concurrency control
- **Async/Await**: Consistent use of async patterns throughout the codebase

### 2. **Factory Pattern**
```python
def create_extractor(config: Dict) -> FlexibleWaterfrontExtractor:
    """Factory method for creating extractor instances"""
    return FlexibleWaterfrontExtractor(**config)
```

### 3. **Strategy Pattern**
```python
class ExtractionStrategy:
    """Base class for extraction strategies"""
    
class HTMLStrategy(ExtractionStrategy):
    """HTML-based extraction strategy"""
    
class JSONStrategy(ExtractionStrategy):
    """JSON-based extraction strategy"""
```

### 4. **Observer Pattern**
```python
class ProgressObserver:
    """Observes and reports extraction progress"""
    def update(self, progress: ProgressUpdate):
        # Update progress display
        # Log progress information
        # Trigger notifications
```

### 5. **Repository Pattern**
```python
class PropertyRepository:
    """Data access layer for property data"""
    def save(self, property_data: Dict):
        """Save property to database"""
        
    def find_by_zpid(self, zpid: str) -> Optional[Dict]:
        """Find property by ZPID"""
        
    def update(self, zpid: str, updates: Dict):
        """Update existing property"""
```

## Configuration Management

### Environment Variables
```bash
# Required
ZYTE_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional
TIMEOUT_SECONDS=60
MAX_CONCURRENT_PROPERTIES=5
CACHE_MODE=false
ENABLE_DB_STORAGE=true
```

### Configuration Classes
```python
@dataclass
class ExtractorConfig:
    api_key: str
    timeout_seconds: int = 30
    max_concurrent_properties: int = 5
    enable_db_storage: bool = False
    cache_mode: bool = False
    simple_logging: bool = False
```

## Error Handling and Resilience

### 1. **Error Categories**
- **Network Errors**: API timeouts, connection failures
- **Parsing Errors**: Malformed HTML, invalid JSON
- **Database Errors**: Connection failures, constraint violations
- **Validation Errors**: Invalid data formats, missing required fields

### 2. **Error Recovery Strategies**
```python
async def _extract_with_retry(self, url: str, max_retries: int = 3):
    """Extract data with automatic retry logic"""
    for attempt in range(max_retries):
        try:
            return await self._extract_single_property(url)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 3. **Circuit Breaker Pattern**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
```

## Performance Optimization

### 1. **Concurrent Processing**
- **Semaphore Control**: Limits concurrent requests to prevent overwhelming
- **Connection Pooling**: Reuses database connections efficiently
- **Async I/O**: Non-blocking operations for better throughput

### 2. **Caching Strategies**
- **HTML Cache**: Stores raw HTML content for reprocessing
- **JSON Cache**: Caches parsed JSON data
- **Database Cache**: Maintains frequently accessed data in memory

### 3. **Memory Management**
```python
def _cleanup_memory(self):
    """Clean up memory usage during long-running operations"""
    import gc
    gc.collect()
    
    # Clear caches
    self.html_cache.clear()
    self.json_cache.clear()
```

## Testing and Quality Assurance

### 1. **Unit Testing**
```python
class TestFlexibleWaterfrontExtractor:
    def test_extract_property(self):
        """Test property extraction functionality"""
        
    def test_database_storage(self):
        """Test database storage operations"""
        
    def test_concurrent_processing(self):
        """Test concurrent processing capabilities"""
```

### 2. **Integration Testing**
```python
class TestIntegration:
    def test_end_to_end_extraction(self):
        """Test complete extraction workflow"""
        
    def test_database_integration(self):
        """Test database integration"""
```

### 3. **Performance Testing**
```python
class TestPerformance:
    def test_concurrent_performance(self):
        """Test concurrent processing performance"""
        
    def test_memory_usage(self):
        """Test memory usage patterns"""
```

## Deployment and Operations

### 1. **Environment Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with actual values
```

### 2. **Database Setup**
```sql
-- Create database
CREATE DATABASE zillow_wf;

-- Run migrations
python -m alembic upgrade head
```

### 3. **Monitoring and Logging**
```python
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extractor.log'),
        logging.StreamHandler()
    ]
)
```

## Future Enhancements

### 1. **Scalability Improvements**
- **Microservices Architecture**: Split into smaller, focused services
- **Message Queue Integration**: Use Redis/RabbitMQ for job distribution
- **Horizontal Scaling**: Support multiple extractor instances

### 2. **Advanced Features**
- **Machine Learning**: Intelligent data extraction and validation
- **Real-time Processing**: Stream processing for live data updates
- **Advanced Analytics**: Property market analysis and insights

### 3. **Integration Capabilities**
- **API Endpoints**: RESTful API for external access
- **Webhook Support**: Real-time notifications for data updates
- **Third-party Integrations**: CRM, MLS, and other real estate systems

---

*Last Updated: August 15, 2025*
*Architecture Version: 2.0*
*Status: Production Ready*
*Next Major Version: 3.0 (Microservices)*
