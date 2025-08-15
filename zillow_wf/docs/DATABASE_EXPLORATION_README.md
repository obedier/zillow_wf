# Database Exploration Tools - Zillow Waterfront Properties

This directory contains comprehensive tools for exploring and analyzing your Zillow waterfront properties database. These tools will help you understand your data, identify patterns, and gain insights into waterfront property markets.

## 🛠️ Available Tools

### 1. **explore_database_corrected.py** - Comprehensive Database Explorer
**Purpose**: Complete overview of your database with statistics, data quality analysis, and market insights.

**Features**:
- 📊 Table information and record counts
- 🌊 Waterfront property analysis
- 🔍 Data quality assessment
- 📈 Market trends analysis
- 🏠 Sample property inspection
- 📋 Comprehensive summary report

**Usage**:
```bash
cd zillow_wf
python explore_database_corrected.py
```

### 2. **check_db.py** - Database Connection Tester
**Purpose**: Simple script to test database connectivity and check for specific ZPIDs.

**Features**:
- 🔌 Database connection verification
- 🔍 ZPID existence checking
- 🚨 Connection error diagnostics

**Usage**:
```bash
cd zillow_wf
python check_db.py
```

### 3. **get_existing_zpids.py** - ZPID Extractor
**Purpose**: Retrieve all existing ZPIDs from the database for data processing workflows.

**Features**:
- 📋 Extract all ZPIDs from listings_summary
- 💾 Save to JSON file for external processing
- 🔄 Used by data extraction scripts

**Usage**:
```bash
cd zillow_wf
python get_existing_zpids.py
```

### 4. **flexible_waterfront_extractor.py** - Main Data Extraction Engine
**Purpose**: Core component for scraping Zillow URLs and populating the database.

**Features**:
- 🌐 URL scraping with JSON-first approach
- 📁 Cached file processing
- 🔄 Database record updates
- 🌊 Multi-layered waterfront detection
- 📊 Progress tracking and logging

**Usage**:
```bash
cd zillow_wf
python flexible_waterfront_extractor.py --url "https://zillow.com/..." --test
python flexible_waterfront_extractor.py --cached-file "cached_file.html"
```

### 5. **fix_waterfront_flags.py** - Waterfront Flag Corrector
**Purpose**: Fix the `is_waterfront` flag in listings_summary by analyzing existing data.

**Features**:
- 🔍 Analyzes waterfront_features, water_view, and description_raw
- ✅ Updates is_waterfront flag based on content analysis
- 📊 Reports waterfront property count and percentage
- 🔄 Handles transaction rollbacks gracefully

**Usage**:
```bash
cd zillow_wf
python fix_waterfront_flags.py
```

### 6. **waterfront_footage_updater.py** - Waterfront Footage Extractor
**Purpose**: Extract specific waterfront footage measurements and update dock_info field.

**Features**:
- 📏 Regex-based footage extraction (e.g., "100' Canal")
- 🎯 Targets waterfront_features, water_view, description_raw, canal_info
- 💾 Updates dock_info field in listings_summary
- 📊 Reports extraction success rate

**Usage**:
```bash
cd zillow_wf
python waterfront_footage_updater.py
```

### 7. **numerical_sentence_extractor_v2.py** - Numerical Data Extractor
**Purpose**: Extract any sentence containing numbers from text fields for comprehensive analysis.

**Features**:
- 🔢 Identifies numerical data in various text fields
- 📊 Categorizes data by type (year, area, rooms, price, etc.)
- 💾 Updates dock_info with numerical summaries
- 📈 Handles 74.1% of properties with numerical data

**Usage**:
```bash
cd zillow_wf
python numerical_sentence_extractor_v2.py
```

### 8. **export_listings_data_v2.py** - Data Export Tool
**Purpose**: Export specific fields from listings_detail to pipe-delimited and CSV formats.

**Features**:
- 📤 Exports zpid, description_raw, dock_info, waterfront_features, canal_info, reso_facts
- 🧹 Cleans field values (replaces problematic characters)
- 📁 Generates both .txt and .csv outputs
- 🔧 Handles newlines and delimiter conflicts

**Usage**:
```bash
cd zillow_wf
python export_listings_data_v2.py
```

### 9. **find_waterfront_footage_v3.py** - Enhanced Waterfront Feature Extractor
**Purpose**: Extract and categorize waterfront measurements using advanced regex patterns.

**Features**:
- 📏 Categorizes measurements into dock_length, waterfront_length, seawall_length, etc.
- 🔍 Advanced regex patterns for various measurement formats
- 📊 Handles complex patterns like "25'x135'"
- 💾 Robust error handling for malformed data

**Usage**:
```bash
cd zillow_wf
python find_waterfront_footage_v3.py
```

### 10. **find_waterfront_footage_v4.py** - Comprehensive Waterfront Feature Extractor
**Purpose**: Extract a wide array of structured waterfront and dock-related features.

**Features**:
- 🌊 Comprehensive waterfront type classification
- 📏 Multiple measurement fields (waterfront_linear_ft, dock_linear_ft, slip_count, etc.)
- 🚢 Vessel specifications (max_vessel_length_ft, max_vessel_beam_ft, lift_capacity_lbs)
- 🌊 Water conditions (depth_at_mlw_ft, no_fixed_bridges, bridge_clearance_ft)
- 📁 Outputs both JSON and CSV formats
- 🎯 634 properties analyzed with detailed feature extraction

**Usage**:
```bash
cd zillow_wf
python find_waterfront_footage_v4.py
```

### 11. **create_wf_data_table.py** - WF Data Table Creator
**Purpose**: Create and populate the new wf_data table in the database.

**Features**:
- 🏗️ Creates wf_data table with proper schema
- 📊 Handles mixed data types and text-to-number conversions
- 🔗 Creates indexes for efficient joins
- ✅ Verifies data insertion and tests table joins
- 📈 Reports join success rates with existing tables

**Usage**:
```bash
cd zillow_wf
python create_wf_data_table.py
```

## 🗄️ Database Schema

### Core Tables

#### **`listings_summary`** - Basic Property Information
- **zpid**: Unique Zillow property identifier (PRIMARY KEY)
- **address, city, state, zipcode**: Location information
- **price**: Property listing price
- **beds, baths**: Bedroom and bathroom counts
- **home_size_sqft**: Property square footage
- **lot_size_sqft**: Lot size in square feet
- **latitude, longitude**: GPS coordinates
- **is_waterfront**: Boolean flag for waterfront properties
- **dock_info**: Extracted waterfront/dock information
- **created_at, updated_at**: Timestamps

#### **`listings_detail`** - Comprehensive Property Data
- **zpid**: References listings_summary.zpid (FOREIGN KEY)
- **description_raw**: Raw property description text
- **waterfront_features**: JSON array of waterfront features
- **water_view**: Water view information
- **canal_info**: Canal-specific information
- **reso_facts**: RESO standard property facts
- **created_at, updated_at**: Timestamps

#### **`wf_data`** - Waterfront Features Analysis (NEW!)
- **id**: Auto-incrementing primary key
- **zpid**: Property identifier (indexed for efficient joins)
- **description_length**: Extracted numeric length from description
- **waterfront_linear_ft**: Waterfront footage in feet
- **dock_linear_ft**: Dock footage in feet
- **no_fixed_bridges**: Boolean flag for no fixed bridges
- **waterfront_type**: Categorized waterfront types (e.g., "ocean; canal; waterfront")
- **any_length**: General length measurements
- **created_at, updated_at**: Timestamps

### Table Relationships
- **One-to-One**: `listings_summary` ↔ `listings_detail` (via zpid)
- **One-to-One**: `listings_summary` ↔ `wf_data` (via zpid)
- **Indexed Joins**: All tables have zpid indexes for efficient queries

## 📊 Data Processing Workflows

### Phase 1: Initial Data Extraction
1. **URL Scraping**: Use `flexible_waterfront_extractor.py` to scrape Zillow URLs
2. **Data Storage**: Store in both `listings_summary` and `listings_detail` tables
3. **Waterfront Detection**: Basic waterfront flagging during extraction

### Phase 2: Data Enhancement
1. **Waterfront Flag Correction**: Use `fix_waterfront_flags.py` to activate waterfront detection
2. **Footage Extraction**: Use `waterfront_footage_updater.py` for basic measurements
3. **Numerical Analysis**: Use `numerical_sentence_extractor_v2.py` for comprehensive data

### Phase 3: Advanced Feature Extraction
1. **Data Export**: Use `export_listings_data_v2.py` to create analysis files
2. **Feature Analysis**: Use `find_waterfront_footage_v4.py` for detailed features
3. **Database Integration**: Use `create_wf_data_table.py` to create wf_data table

## 🚀 Getting Started

### Prerequisites
1. **PostgreSQL Database**: Ensure your `zillow_wf` database is running
2. **Python Virtual Environment**: Activate with `source venv/bin/activate`
3. **Dependencies**: Install required packages (`psycopg`, `pandas`, etc.)
4. **Database Connection**: Verify connection string in scripts

### Installation
```bash
# Navigate to the zillow_wf directory
cd zillow_wf

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install psycopg pandas tqdm

# Verify database connection
python check_db.py
```

### Quick Start Guide
1. **Check database connectivity**:
   ```bash
   python check_db.py
   ```

2. **Get database overview**:
   ```bash
   python explore_database_corrected.py
   ```

3. **Verify waterfront flags**:
   ```bash
   python fix_waterfront_flags.py
   ```

4. **Extract waterfront features**:
   ```bash
   python find_waterfront_footage_v4.py
   ```

5. **Create wf_data table**:
   ```bash
   python create_wf_data_table.py
   ```

## 📈 Sample Queries for Analysis

### Waterfront Property Overview
```sql
-- Total properties and waterfront count
SELECT 
    COUNT(*) as total_properties,
    COUNT(CASE WHEN is_waterfront = true THEN 1 END) as waterfront_count,
    ROUND(COUNT(CASE WHEN is_waterfront = true THEN 1 END)::decimal / COUNT(*) * 100, 2) as waterfront_percentage
FROM listings_summary;
```

### Waterfront Features Analysis
```sql
-- Waterfront properties with extracted features
SELECT 
    l.address, l.city, l.state,
    w.waterfront_type, w.waterfront_linear_ft, w.dock_linear_ft,
    w.no_fixed_bridges, w.any_length
FROM listings_summary l
JOIN wf_data w ON l.zpid = w.zpid
WHERE w.waterfront_linear_ft IS NOT NULL
ORDER BY w.waterfront_linear_ft DESC
LIMIT 10;
```

### Waterfront Type Distribution
```sql
-- Properties by waterfront type
SELECT 
    waterfront_type,
    COUNT(*) as property_count,
    ROUND(AVG(price), 2) as avg_price
FROM listings_summary l
JOIN wf_data w ON l.zpid = w.zpid
WHERE w.waterfront_type IS NOT NULL
GROUP BY waterfront_type
ORDER BY property_count DESC;
```

### Dock and Slip Analysis
```sql
-- Properties with dock information
SELECT 
    l.address, l.city,
    w.dock_linear_ft, w.any_length,
    l.dock_info
FROM listings_summary l
JOIN wf_data w ON l.zpid = w.zpid
WHERE w.dock_linear_ft IS NOT NULL
ORDER BY w.dock_linear_ft DESC
LIMIT 15;
```

### Data Quality Assessment
```sql
-- Field completion rates for waterfront data
SELECT 
    COUNT(*) as total_waterfront,
    COUNT(CASE WHEN w.waterfront_linear_ft IS NOT NULL THEN 1 END) as has_linear_ft,
    COUNT(CASE WHEN w.dock_linear_ft IS NOT NULL THEN 1 END) as has_dock_ft,
    COUNT(CASE WHEN w.waterfront_type IS NOT NULL THEN 1 END) as has_type
FROM listings_summary l
JOIN wf_data w ON l.zpid = w.zpid
WHERE l.is_waterfront = true;
```

## 🔍 Understanding Your Data

### Key Insights from Analysis
1. **Waterfront Coverage**: 82.3% of properties have waterfront flags activated
2. **Feature Extraction**: 634 properties analyzed with detailed waterfront features
3. **Data Quality**: High completion rates for core waterfront attributes
4. **Geographic Distribution**: Focus on Florida waterfront properties
5. **Property Types**: Mix of residential and commercial waterfront properties

### Data Sources and Processing
- **Primary Source**: Zillow property detail pages
- **Extraction Method**: JSON-first approach with HTML fallback
- **Data Enhancement**: Multi-phase processing with regex-based feature extraction
- **Quality Control**: Transaction-level error handling and rollback mechanisms

### Recent Achievements
- ✅ **Waterfront Flag Activation**: 82.3% of properties now properly flagged
- ✅ **Dock Info Population**: 110 properties with structured footage data
- ✅ **Numerical Data Extraction**: 74.1% of properties with numerical summaries
- ✅ **Advanced Feature Extraction**: 634 properties with comprehensive waterfront features
- ✅ **WF Data Table**: New table with 634 records, 100% joinable with existing data

## 🚨 Troubleshooting

### Common Issues and Solutions
1. **Connection Errors**: 
   - Verify PostgreSQL is running
   - Check virtual environment activation
   - Use `python3` instead of `python`

2. **Transaction Abortions**:
   - Scripts now handle individual transaction rollbacks
   - Each update is committed separately
   - Check logs for specific error details

3. **Missing Fields**:
   - Use `explore_database_corrected.py` to see actual schema
   - Check for field name variations
   - Verify table structure with `check_schema.py`

4. **Data Type Issues**:
   - Scripts now handle mixed data types gracefully
   - Text-to-number conversion with error handling
   - NULL values for unparseable data

### Getting Help
1. **Check Script Output**: Review detailed logging and progress reports
2. **Verify Database State**: Use exploration tools to understand current data
3. **Test Individual Components**: Run scripts step-by-step to isolate issues
4. **Review Error Messages**: Most scripts provide detailed error information

## 🔄 Regular Maintenance

### Recommended Schedule
- **Daily**: Check data freshness with basic queries
- **Weekly**: Run comprehensive analysis with `explore_database_corrected.py`
- **After Data Updates**: Run `fix_waterfront_flags.py` and feature extractors
- **Monthly**: Deep waterfront analysis with `find_waterfront_footage_v4.py`

### Data Quality Monitoring
- Monitor waterfront flag accuracy
- Track feature extraction success rates
- Validate join relationships between tables
- Check for data consistency issues

## 📚 Additional Resources

### Documentation
- **`docs/DATABASE.md`**: Complete database schema documentation
- **`docs/README.md`**: Project overview and setup
- **`docs/PLAN_PROGRESS.md`**: Project goals and progress

### Data Files
- **`data/summary/`**: Extraction run summaries and reports
- **`data/existing_zpids.json`**: Current ZPIDs in database
- **`logs/`**: Processing logs and error tracking
- **`waterfront_features_v4_634_properties2.csv`**: Latest waterfront features data

### Output Files
- **`waterfront_features_v4_634_properties.json`**: Detailed JSON analysis (415.4 KB)
- **`waterfront_features_v4_634_properties.csv`**: CSV for external analysis (36.9 KB)
- **`waterfront_features_v4_634_properties2.csv`**: Processed data for database (28.6 KB)

---

**Happy Exploring!** 🚀

Use these tools to unlock insights from your waterfront property data and discover market opportunities you might have missed. The new `wf_data` table provides a powerful foundation for advanced waterfront property analysis and market insights.




