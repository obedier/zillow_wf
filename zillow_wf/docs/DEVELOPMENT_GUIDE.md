# Zillow Waterfront Extractor - Development Guide

## Overview
This guide provides comprehensive information for developers who want to contribute to, extend, or maintain the Zillow Waterfront Property Extractor codebase. It covers the development environment setup, code structure, testing, and contribution guidelines.

## Development Environment Setup

### 1. **Prerequisites**
```bash
# Required software
- Python 3.9+ (3.13 recommended)
- PostgreSQL 12+
- Git
- Virtual environment tool (venv or conda)

# System requirements
- 8GB+ RAM (16GB recommended for large extractions)
- 10GB+ free disk space
- Stable internet connection for API access
```

### 2. **Repository Setup**
```bash
# Clone the repository
git clone <repository-url>
cd zillow_wf

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available
```

### 3. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Required variables
ZYTE_API_KEY=your_zyte_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/zillow_wf

# Optional variables
LOG_LEVEL=INFO
CACHE_DIR=./data/cache
TIMEOUT_SECONDS=60
```

### 4. **Database Setup**
```bash
# Create database
createdb zillow_wf

# Run database initialization
python -c "
from flexible_waterfront_extractor import FlexibleWaterfrontExtractor
extractor = FlexibleWaterfrontExtractor(enable_db_storage=True)
extractor._initialize_database()
print('Database initialized successfully')
"
```

## Code Structure and Organization

### 1. **Project Layout**
```
zillow_wf/
├── flexible_waterfront_extractor.py  # Main extractor class
├── requirements.txt                   # Python dependencies
├── .env                              # Environment configuration
├── .gitignore                        # Git ignore patterns
├── README.md                         # Project overview
├── docs/                             # Documentation
│   ├── prompt_context.md             # Project context
│   ├── DATABASE_SCHEMA.md            # Database documentation
│   ├── CODEBASE_ARCHITECTURE.md      # Architecture overview
│   ├── USAGE_GUIDE.md                # User guide
│   └── DEVELOPMENT_GUIDE.md          # This file
├── zillow_wf/                        # Package directory
│   ├── __init__.py                   # Package initialization
│   ├── data/                         # Data storage
│   │   ├── cache/                    # HTML and JSON cache
│   │   ├── html/                     # Raw HTML files
│   │   ├── next_data/                # JSON payloads
│   │   ├── processed/                # Processed data
│   │   └── summary/                  # Analysis reports
│   ├── logs/                         # Application logs
│   └── venv/                         # Virtual environment
└── tests/                            # Test suite
    ├── __init__.py
    ├── test_extractor.py
    ├── test_database.py
    └── test_integration.py
```

### 2. **Core Module Structure**

#### **Main Extractor Class**
```python
class FlexibleWaterfrontExtractor:
    """Main extractor class with comprehensive functionality"""
    
    def __init__(self, **config):
        """Initialize extractor with configuration"""
        
    async def extract_property(self, url: str):
        """Main extraction workflow"""
        
    async def _extract_single_property(self, url: str):
        """Process individual property"""
        
    async def _extract_properties_concurrent(self, urls: List[str]):
        """Concurrent processing implementation"""
        
    def store_property_to_database(self, property_data: Dict):
        """Database storage operations"""
```

#### **Data Extraction Methods**
```python
def _extract_from_html(self, html_content: str) -> Dict[str, Any]:
    """Extract data from HTML content"""
    
def _extract_from_json(self, html_content: str) -> Dict[str, Any]:
    """Extract data from JSON payloads"""
    
def _detect_waterfront_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Identify waterfront features"""
```

#### **Database Operations**
```python
def _initialize_database(self):
    """Set up database tables and indexes"""
    
def _load_existing_zpids(self):
    """Load existing ZPIDs from database"""
    
def _check_database_for_zpid(self, zpid: str) -> bool:
    """Check if ZPID exists in database"""
```

### 3. **Configuration Management**
```python
# Configuration class structure
@dataclass
class ExtractorConfig:
    api_key: str
    timeout_seconds: int = 30
    max_concurrent_properties: int = 5
    enable_db_storage: bool = False
    cache_mode: bool = False
    simple_logging: bool = False
    save_urls_list: bool = False
    continue_from_file: Optional[str] = None
```

## Development Workflow

### 1. **Feature Development**
```bash
# Create feature branch
git checkout -b feature/new-extraction-method

# Make changes
# Test changes
# Commit with descriptive message
git commit -m "feat: add new waterfront feature detection method

- Implement machine learning-based feature detection
- Add confidence scoring for extracted features
- Update database schema for new fields"

# Push and create pull request
git push origin feature/new-extraction-method
```

### 2. **Bug Fixes**
```bash
# Create bug fix branch
git checkout -b fix/pagination-issue

# Fix the issue
# Add tests to prevent regression
# Commit fix
git commit -m "fix: resolve pagination stopping prematurely

- Fix consecutive empty pages logic
- Increase max_empty_pages threshold
- Add better logging for pagination status"

# Push and create pull request
git push origin fix/pagination-issue
```

### 3. **Code Review Process**
```python
# Code review checklist
- [ ] Code follows PEP 8 style guidelines
- [ ] Functions have proper docstrings
- [ ] Error handling is comprehensive
- [ ] Tests cover new functionality
- [ ] Database schema changes are documented
- [ ] Performance impact is considered
- [ ] Logging is appropriate for production
```

## Testing Strategy

### 1. **Unit Testing**
```python
# test_extractor.py
import pytest
import asyncio
from flexible_waterfront_extractor import FlexibleWaterfrontExtractor

class TestFlexibleWaterfrontExtractor:
    @pytest.fixture
    def extractor(self):
        """Create extractor instance for testing"""
        return FlexibleWaterfrontExtractor(
            api_key="test_key",
            enable_db_storage=False,
            cache_mode=True
        )
    
    def test_extractor_initialization(self, extractor):
        """Test extractor initialization"""
        assert extractor.api_key == "test_key"
        assert extractor.enable_db_storage is False
        assert extractor.cache_mode is True
    
    @pytest.mark.asyncio
    async def test_extract_single_property(self, extractor):
        """Test single property extraction"""
        # Test with mock data
        result = await extractor._extract_single_property("test_url")
        assert result is not None
        assert "zpid" in result
    
    def test_waterfront_feature_detection(self, extractor):
        """Test waterfront feature detection"""
        test_data = {
            "description": "Beautiful waterfront property with dock access",
            "address": "123 Ocean Blvd"
        }
        
        features = extractor._detect_waterfront_features(test_data)
        assert features["is_waterfront"] is True
        assert "dock" in features["waterfront_features"]
```

### 2. **Integration Testing**
```python
# test_integration.py
import pytest
from flexible_waterfront_extractor import FlexibleWaterfrontExtractor

class TestIntegration:
    @pytest.fixture
    def db_extractor(self):
        """Create extractor with database enabled"""
        return FlexibleWaterfrontExtractor(
            api_key="test_key",
            enable_db_storage=True,
            cache_mode=True
        )
    
    def test_database_operations(self, db_extractor):
        """Test database operations end-to-end"""
        # Test property storage
        test_property = {
            "zpid": "test_123",
            "address": "123 Test St",
            "price": 500000
        }
        
        result = db_extractor.store_property_to_database(test_property)
        assert result["success"] is True
        assert result["action"] == "insert"
    
    def test_cache_operations(self, db_extractor):
        """Test cache operations"""
        # Test HTML caching
        test_html = "<html><body>Test content</body></html>"
        db_extractor._cache_html_content("test_url", test_html)
        
        cached = db_extractor._get_cached_html_content("test_url")
        assert cached == test_html
```

### 3. **Performance Testing**
```python
# test_performance.py
import time
import asyncio
import pytest
from flexible_waterfront_extractor import FlexibleWaterfrontExtractor

class TestPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self):
        """Test concurrent processing performance"""
        extractor = FlexibleWaterfrontExtractor(
            api_key="test_key",
            max_concurrent_properties=5,
            cache_mode=True
        )
        
        # Generate test URLs
        test_urls = [f"test_url_{i}" for i in range(100)]
        
        start_time = time.time()
        results = await extractor._extract_properties_concurrent(test_urls)
        end_time = time.time()
        
        processing_time = end_time - start_time
        properties_per_second = len(results) / processing_time
        
        assert properties_per_second > 1.0  # At least 1 property per second
        assert len(results) == 100
    
    def test_memory_usage(self):
        """Test memory usage during large operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform memory-intensive operation
        extractor = FlexibleWaterfrontExtractor(
            api_key="test_key",
            cache_mode=True
        )
        
        # Simulate large data processing
        large_data = ["x" * 1000000 for _ in range(100)]
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 500MB)
        assert memory_increase < 500 * 1024 * 1024
```

### 4. **Test Configuration**
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
```

## Code Quality and Standards

### 1. **Style Guidelines**
```python
# Follow PEP 8 style guide
# Use 4 spaces for indentation
# Maximum line length: 88 characters (black formatter)
# Use descriptive variable names
# Add type hints where possible

def extract_property_data(
    html_content: str,
    extraction_config: ExtractionConfig
) -> Dict[str, Any]:
    """
    Extract property data from HTML content.
    
    Args:
        html_content: Raw HTML content from Zillow
        extraction_config: Configuration for extraction
        
    Returns:
        Dictionary containing extracted property data
        
    Raises:
        ExtractionError: If extraction fails
    """
    # Implementation here
    pass
```

### 2. **Documentation Standards**
```python
class FlexibleWaterfrontExtractor:
    """
    Flexible extractor for waterfront properties with deep JSON searching.
    
    This class provides comprehensive functionality for extracting waterfront
    property data from Zillow, including:
    
    - HTML and JSON data extraction
    - Waterfront feature detection
    - Database storage and updates
    - Concurrent processing
    - Caching and resume functionality
    
    Attributes:
        api_key: Zyte API key for web scraping
        enable_db_storage: Whether to store data in database
        timeout_seconds: HTTP request timeout
        max_concurrent_properties: Maximum concurrent processing
        
    Example:
        >>> extractor = FlexibleWaterfrontExtractor(
        ...     api_key="your_key",
        ...     enable_db_storage=True
        ... )
        >>> await extractor.extract_property("https://zillow.com/property")
    """
```

### 3. **Error Handling**
```python
class ExtractionError(Exception):
    """Base exception for extraction errors"""
    pass

class NetworkError(ExtractionError):
    """Network-related errors"""
    pass

class ParsingError(ExtractionError):
    """Data parsing errors"""
    pass

def safe_extraction(func):
    """Decorator for safe extraction with error handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NetworkError as e:
            logger.error(f"Network error during extraction: {e}")
            raise
        except ParsingError as e:
            logger.error(f"Parsing error during extraction: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            raise ExtractionError(f"Extraction failed: {e}")
    return wrapper
```

## Database Development

### 1. **Schema Changes**
```sql
-- Example schema migration
-- Create new table for enhanced waterfront features

CREATE TABLE IF NOT EXISTS enhanced_waterfront_features (
    id SERIAL PRIMARY KEY,
    zpid VARCHAR(50) NOT NULL REFERENCES listings_summary(zpid),
    water_depth_measurement DECIMAL(8,2),
    bridge_clearance_ft INTEGER,
    boat_slip_size VARCHAR(20),
    marina_distance_miles DECIMAL(5,2),
    water_access_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_enhanced_waterfront_features_zpid ON enhanced_waterfront_features(zpid);
CREATE INDEX idx_enhanced_waterfront_features_water_depth ON enhanced_waterfront_features(water_depth_measurement);
```

### 2. **Database Testing**
```python
# test_database.py
import pytest
from sqlalchemy import create_engine, text
from flexible_waterfront_extractor import FlexibleWaterfrontExtractor

class TestDatabase:
    @pytest.fixture
    def test_db(self):
        """Create test database"""
        engine = create_engine("postgresql://test:test@localhost:5432/test_zillow_wf")
        
        # Create test tables
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_listings_summary (
                    zpid VARCHAR(50) PRIMARY KEY,
                    address VARCHAR(255),
                    price INTEGER
                )
            """))
            conn.commit()
        
        yield engine
        
        # Cleanup
        engine.dispose()
    
    def test_property_insertion(self, test_db):
        """Test property insertion"""
        extractor = FlexibleWaterfrontExtractor(
            api_key="test",
            enable_db_storage=True
        )
        extractor.db_engine = test_db
        
        test_property = {
            "zpid": "test_123",
            "address": "123 Test St",
            "price": 500000
        }
        
        result = extractor.store_property_to_database(test_property)
        assert result["success"] is True
```

## Performance Optimization

### 1. **Profiling and Monitoring**
```python
import cProfile
import pstats
import io
from flexible_waterfront_extractor import FlexibleWaterfrontExtractor

def profile_extraction():
    """Profile extraction performance"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run extraction
    extractor = FlexibleWaterfrontExtractor(api_key="test")
    # ... run extraction code ...
    
    profiler.disable()
    
    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())
```

### 2. **Memory Optimization**
```python
def optimize_memory_usage():
    """Optimize memory usage during large extractions"""
    import gc
    
    # Clear caches periodically
    if len(self.html_cache) > 1000:
        self.html_cache.clear()
        gc.collect()
    
    # Use generators for large datasets
    def url_generator(urls):
        for url in urls:
            yield url
    
    # Process URLs in batches
    batch_size = 100
    for batch in zip(*[iter(urls)] * batch_size):
        # Process batch
        pass
```

## Deployment and CI/CD

### 1. **Docker Configuration**
```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p zillow_wf/data/{cache,html,next_data,processed,summary,logs}

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "flexible_waterfront_extractor.py"]
```

### 2. **GitHub Actions Workflow**
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      run: |
        pytest tests/ -v
```

## Contributing Guidelines

### 1. **Issue Reporting**
```markdown
## Bug Report Template

**Description**
Clear description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., macOS 13.0]
- Python: [e.g., 3.13.0]
- Database: [e.g., PostgreSQL 13]

**Additional Context**
Any other relevant information
```

### 2. **Feature Request Template**
```markdown
## Feature Request Template

**Problem Statement**
Clear description of the problem this feature would solve

**Proposed Solution**
Description of the proposed feature

**Alternative Solutions**
Other approaches considered

**Additional Context**
Any other relevant information

**Acceptance Criteria**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### 3. **Pull Request Process**
```markdown
## Pull Request Template

**Description**
Brief description of changes

**Type of Change**
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

**Testing**
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

**Checklist**
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
- [ ] No breaking changes
```

## Troubleshooting Development Issues

### 1. **Common Development Problems**

#### **Import Errors**
```bash
# Check Python path
echo $PYTHONPATH

# Install package in development mode
pip install -e .

# Check virtual environment
which python
pip list
```

#### **Database Connection Issues**
```bash
# Test database connection
psql -h localhost -U username -d zillow_wf

# Check PostgreSQL service
sudo systemctl status postgresql

# Verify connection string
echo $DATABASE_URL
```

#### **Memory Issues**
```bash
# Monitor memory usage
htop
free -h

# Check Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

### 2. **Debugging Tools**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use Python debugger
import pdb; pdb.set_trace()

# Profile specific functions
from line_profiler import LineProfiler
profiler = LineProfiler()
profiler.add_function(FlexibleWaterfrontExtractor._extract_from_html)
profiler.run('extractor._extract_from_html(html_content)')
profiler.print_stats()
```

## Future Development Roadmap

### 1. **Short-term Goals (1-3 months)**
- [ ] Improve error handling and recovery
- [ ] Add more comprehensive testing
- [ ] Optimize database queries
- [ ] Enhance logging and monitoring

### 2. **Medium-term Goals (3-6 months)**
- [ ] Implement machine learning for feature extraction
- [ ] Add real-time processing capabilities
- [ ] Create RESTful API endpoints
- [ ] Implement advanced caching strategies

### 3. **Long-term Goals (6+ months)**
- [ ] Microservices architecture
- [ ] Cloud-native deployment
- [ ] Advanced analytics and reporting
- [ ] Integration with external systems

---

*Last Updated: August 15, 2025*
*Development Version: 2.0*
*Status: Active Development*
*Contributors: Open to contributions*
*License: [Specify License]*
