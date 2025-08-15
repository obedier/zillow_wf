# Zillow Waterfront Extractor - Complete Usage Guide

## Overview
This guide provides comprehensive instructions for using the Zillow Waterfront Property Extractor system. The system is designed to extract, process, and store waterfront property data from Zillow with advanced features for efficiency, reliability, and data quality.

## Quick Start

### 1. **Environment Setup**
```bash
# Navigate to project directory
cd zillow_wf

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Zyte API key and database credentials
```

### 2. **Basic Usage**
```bash
# Extract properties from a search URL
python flexible_waterfront_extractor.py \
  --urls-file <(echo "https://www.zillow.com/homes/for_sale/?searchQueryState=...") \
  --enable-db-storage \
  --simple
```

## Command Line Interface

### Core Arguments

#### **Required Arguments**
- `--urls-file`: File containing URLs to process (or use `<()` for inline URLs)

#### **Mode Selection**
- `--mode {urls,search,cache}`: Operation mode
  - `urls`: Process existing URLs from file
  - `search`: Extract URLs from search results page
  - `cache`: Process cached HTML files

#### **Database Options**
- `--enable-db-storage`: Enable database storage
- `--update-existing`: Update existing database records (default: True)

### Performance and Control

#### **Concurrency Control**
```bash
--max-concurrent-properties 5    # Process 5 properties simultaneously
--max-search-pages 20            # Extract from up to 20 search result pages
--max-properties-per-search 1000 # Limit properties per search
```

#### **Timeout and Rate Limiting**
```bash
--timeout 60                     # HTTP request timeout in seconds
--cache-mode                     # Use cached data only (no API calls)
```

### Logging and Output

#### **Logging Modes**
```bash
--simple                         # Simple progress counters
--save-html                      # Save raw HTML content
--save-processed                 # Save processed data
--save-next-data                # Save __NEXT_DATA__ payloads
--save-summary                   # Save extraction summary
```

#### **File Management**
```bash
--save-urls-list                # Save extracted URLs to file
--continue <filename>            # Continue from saved URLs file
```

## Usage Scenarios

### 1. **Extract URLs from Search Results**

#### **Scenario**: Find all waterfront properties in a specific area
```bash
python flexible_waterfront_extractor.py \
  --mode search \
  --urls-file <(echo "https://www.zillow.com/homes/for_sale/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A26.118743737431902%2C%22south%22%3A23.763020482129413%2C%22east%22%3A-79.72406202369234%2C%22west%22%3A-82.38550001197359%7D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22price%22%3A%7B%22min%22%3A900000%2C%22max%22%3Anull%7D%2C%22mp%22%3A%7B%22min%22%3A4541%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22wat%22%3A%7B%22value%22%3Atrue%7D%7D%2C%22isListVisible%22%3Atrue%2C%22category%22%3A%22cat1%22%2C%22mapZoom%22%3A9%2C%22customRegionId%22%3A%2286951689e1X1-CRf0zcn2veir3p_12be0u%22%7D") \
  --simple \
  --save-urls-list \
  --max-search-pages 20 \
  --max-properties-per-search 1000
```

**What this does**:
- Searches for waterfront properties in the specified geographic area
- Extracts URLs from up to 20 search result pages
- Saves the list of property URLs to a timestamped file
- Uses simple logging for progress tracking

#### **Expected Output**:
```
🔍 Starting search results extraction...
📄 Processing search results page 1/20
✅ Page 1: 40 results, 40 new URLs
📊 Total unique URLs collected: 40
📄 Processing search results page 2/20
✅ Page 2: 40 results, 35 new URLs
📊 Total unique URLs collected: 75
...
📄 Processing search results page 20/20
✅ Page 20: 25 results, 5 new URLs
📊 Total unique URLs collected: 585
💾 Saved 585 URLs to: zillow_wf/data/urls_list_20250815_123456.txt
```

### 2. **Process Saved URLs**

#### **Scenario**: Extract data from previously saved property URLs
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue zillow_wf/data/urls_list_20250815_123456.txt \
  --enable-db-storage \
  --simple \
  --max-concurrent-properties 5 \
  --timeout 60
```

**What this does**:
- Loads property URLs from the saved file
- Processes 5 properties concurrently for speed
- Stores extracted data in the database
- Uses simple logging with progress counters

#### **Expected Output**:
```
🔍 Loading 585 URLs from: zillow_wf/data/urls_list_20250815_123456.txt
🔍 Processing 585 properties (limited to 1000)
🚀 Using concurrent extraction with 5 threads
✅ Properties Scraped: 1
✅ Properties Extracted: 1
✅ Properties Added: 1
✅ Properties Updated: 0
✅ Properties Skipped: 0
❌ Errors: 0
...
📊 EXTRACTION COMPLETE
   Total Properties: 585
   Successfully Processed: 580
   Failed: 5
   Success Rate: 99.1%
   Total Time: 55 minutes
```

### 3. **Process Cached Data**

#### **Scenario**: Reprocess cached HTML files to fill database gaps
```bash
python flexible_waterfront_extractor.py \
  --mode cache \
  --enable-db-storage \
  --update-existing \
  --simple
```

**What this does**:
- Processes all cached HTML files in the data directory
- Updates existing database records with missing fields
- Useful for filling gaps after initial extraction

### 4. **High-Performance Extraction**

#### **Scenario**: Fast extraction with maximum concurrency
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue zillow_wf/data/urls_list_20250815_123456.txt \
  --enable-db-storage \
  --simple \
  --max-concurrent-properties 10 \
  --timeout 30 \
  --save-summary
```

**What this does**:
- Processes 10 properties simultaneously
- Reduces timeout for faster failure detection
- Saves detailed extraction summary for analysis

## Advanced Features

### 1. **Resume Interrupted Operations**

#### **Save URLs During Search**:
```bash
python flexible_waterfront_extractor.py \
  --mode search \
  --urls-file <(echo "YOUR_SEARCH_URL") \
  --save-urls-list \
  --simple
```

#### **Continue from Saved URLs**:
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue zillow_wf/data/urls_list_TIMESTAMP.txt \
  --enable-db-storage \
  --simple
```

### 2. **Data Quality Control**

#### **Update Existing Records**:
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue urls_list.txt \
  --enable-db-storage \
  --update-existing \
  --simple
```

#### **Dry Run Mode**:
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue urls_list.txt \
  --dry-run \
  --simple
```

### 3. **Comprehensive Data Extraction**

#### **Save All Data Types**:
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue urls_list.txt \
  --enable-db-storage \
  --save-html \
  --save-processed \
  --save-next-data \
  --save-summary \
  --simple
```

## Configuration Examples

### 1. **Development/Testing Configuration**
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue test_urls.txt \
  --max-concurrent-properties 2 \
  --timeout 120 \
  --save-html \
  --save-processed \
  --simple
```

### 2. **Production Configuration**
```bash
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue production_urls.txt \
  --enable-db-storage \
  --max-concurrent-properties 5 \
  --timeout 60 \
  --simple \
  --save-summary
```

### 3. **Cache-Only Configuration**
```bash
python flexible_waterfront_extractor.py \
  --mode cache \
  --enable-db-storage \
  --update-existing \
  --simple
```

## Monitoring and Debugging

### 1. **Progress Tracking**

#### **Simple Mode Output**:
```
✅ Search Results Found: 585
✅ Properties Scraped: 100
✅ Properties Extracted: 98
✅ Properties Added: 95
✅ Properties Updated: 3
✅ Properties Skipped: 0
❌ Errors: 2
```

#### **Detailed Logging**:
```bash
# Remove --simple flag for detailed logging
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue urls_list.txt \
  --enable-db-storage
```

### 2. **Error Handling**

#### **Common Error Scenarios**:
- **API Rate Limiting**: Automatic retry with exponential backoff
- **Network Timeouts**: Configurable timeout values
- **Parsing Errors**: Graceful degradation with fallback strategies
- **Database Errors**: Connection retry and transaction rollback

#### **Error Recovery**:
```bash
# Resume from last successful point
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue urls_list.txt \
  --enable-db-storage \
  --simple
```

### 3. **Performance Monitoring**

#### **Key Metrics**:
- **Processing Speed**: Properties per minute
- **Success Rate**: Percentage of successful extractions
- **Error Rate**: Types and frequency of errors
- **Resource Usage**: Memory and CPU utilization

#### **Performance Optimization**:
```bash
# Increase concurrency for faster processing
--max-concurrent-properties 10

# Reduce timeout for faster failure detection
--timeout 30

# Use cache mode for repeated processing
--cache-mode
```

## Data Output and Storage

### 1. **Database Storage**

#### **Tables Created**:
- `listings_summary`: Core property information
- `listings_detail`: Detailed property data
- `listings_derived`: Computed and analyzed fields
- `property_photos`: Photo metadata and URLs
- `listing_text_content`: Extracted text content
- `wf_data`: Waterfront analysis data

#### **Data Quality**:
- **Field Completion**: 89.4% overall completion rate
- **Validation**: Automatic data validation and cleaning
- **Updates**: Incremental updates for existing records

### 2. **File Outputs**

#### **Generated Files**:
- `urls_list_TIMESTAMP.txt`: Extracted property URLs
- `run_summary_TIMESTAMP.json`: Extraction summary
- `field_completion_report_TIMESTAMP.txt`: Data quality report
- `combined_TIMESTAMP.json`: Complete extracted data

#### **Cache Files**:
- `zillow_wf/data/html/`: Raw HTML content
- `zillow_wf/data/next_data/`: JSON payloads
- `zillow_wf/data/processed/`: Processed data
- `zillow_wf/data/summary/`: Analysis reports

## Troubleshooting

### 1. **Common Issues**

#### **API Key Errors**:
```bash
# Check environment variable
echo $ZYTE_API_KEY

# Verify .env file
cat .env | grep ZYTE_API_KEY
```

#### **Database Connection Issues**:
```bash
# Test database connection
python -c "
import psycopg
conn = psycopg.connect('postgresql://user:pass@host:port/db')
print('Database connection successful')
conn.close()
"
```

#### **Memory Issues**:
```bash
# Reduce concurrency for lower memory usage
--max-concurrent-properties 2

# Use cache mode to avoid storing HTML in memory
--cache-mode
```

### 2. **Performance Issues**

#### **Slow Processing**:
```bash
# Increase concurrency
--max-concurrent-properties 10

# Reduce timeout for faster failure detection
--timeout 30

# Use simple logging to reduce overhead
--simple
```

#### **High Error Rate**:
```bash
# Increase timeout for stability
--timeout 120

# Reduce concurrency for reliability
--max-concurrent-properties 2

# Enable detailed logging for debugging
# (remove --simple flag)
```

### 3. **Data Quality Issues**

#### **Missing Fields**:
```bash
# Update existing records
--update-existing

# Reprocess cached data
--mode cache

# Check field completion report
cat zillow_wf/data/summary/field_completion_report_*.txt
```

## Best Practices

### 1. **Efficient Processing**
- Start with `--max-concurrent-properties 5` and adjust based on performance
- Use `--simple` logging for production runs
- Save URLs list during search to enable resumption
- Use cache mode for repeated processing

### 2. **Data Quality**
- Regularly update existing records with `--update-existing`
- Monitor field completion reports
- Use `--dry-run` to test configurations
- Validate database schema before large extractions

### 3. **Resource Management**
- Monitor memory usage during large extractions
- Use appropriate timeout values for your network
- Implement regular database maintenance
- Archive old cache files periodically

### 4. **Error Handling**
- Always use `--save-urls-list` for large extractions
- Implement retry logic for failed properties
- Monitor error logs for patterns
- Use `--continue` to resume interrupted operations

## Integration Examples

### 1. **Automated Processing**
```bash
#!/bin/bash
# daily_extraction.sh

cd /path/to/zillow_wf
source venv/bin/activate

# Extract new URLs
python flexible_waterfront_extractor.py \
  --mode search \
  --urls-file <(echo "$SEARCH_URL") \
  --save-urls-list \
  --simple

# Process extracted URLs
python flexible_waterfront_extractor.py \
  --mode urls \
  --continue zillow_wf/data/urls_list_$(date +%Y%m%d)*.txt \
  --enable-db-storage \
  --simple
```

### 2. **Scheduled Updates**
```bash
# crontab entry for daily updates
0 2 * * * /path/to/daily_extraction.sh >> /var/log/zillow_extractor.log 2>&1
```

### 3. **Monitoring Integration**
```bash
# Check extraction status
python -c "
import json
import glob
import os

# Find latest summary
summaries = glob.glob('zillow_wf/data/summary/run_summary_*.json')
if summaries:
    latest = max(summaries, key=os.path.getctime)
    with open(latest) as f:
        data = json.load(f)
    print(f'Last extraction: {data[\"extraction_timestamp\"]}')
    print(f'Success rate: {data[\"success_rate_percent\"]}%')
    print(f'Total properties: {data[\"total_properties\"]}')
"
```

---

*Last Updated: August 15, 2025*
*Version: 2.0*
*Status: Production Ready*
*For Support: Check logs and field completion reports*
