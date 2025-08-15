# Zillow Waterfront Properties Data Extraction Project

> **📁 Documentation Structure**: This project now uses a centralized documentation structure. All core documentation is in the `docs/` folder, with historical documentation archived in `docs/archive/`.

## 🎯 What This Application Does

**Zillow Waterfront Properties** is a comprehensive data extraction system that scrapes, processes, and stores detailed information about waterfront properties from Zillow. The system focuses on Fort Lauderdale, FL waterfront areas including ocean access, canal front, intracoastal, and bay front properties.

### Core Functionality
- **Web Scraping**: Extracts property data from Zillow search results and detail pages
- **Data Processing**: Parses complex JSON structures and HTML content
- **Database Storage**: Stores comprehensive property information in PostgreSQL
- **Waterfront Analysis**: Identifies and categorizes waterfront features
- **Progress Tracking**: Monitors extraction success and data quality

### What Gets Extracted
- **Property Details**: ZPID, address, price, bedrooms, bathrooms, square footage
- **Waterfront Features**: Ocean access, canal front, dock information, bridge constraints
- **Market Data**: Zestimate, price history, tax information, days on market
- **Location Data**: Coordinates, parcel numbers, neighborhood information
- **Media Content**: High-resolution photos, property descriptions, contact information

## 🏗️ Architecture & Technology

### Tech Stack
- **Backend**: Python 3.8+ with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Web Scraping**: Zyte API for reliable data extraction
- **Data Processing**: Deep JSON structure searching with multiple fallback methods
- **Caching**: Local file storage for offline processing and data recovery

### System Components
1. **FlexibleWaterfrontExtractor**: Main extraction engine with deep JSON searching
2. **Database Integration**: PostgreSQL storage with field completion tracking
3. **Cache Management**: HTML and JSON caching for offline processing
4. **Progress Monitoring**: Real-time progress bars and completion reports
5. **Duplicate Prevention**: ZPID-based filtering to avoid re-scraping

### Data Flow
```
Zillow Search Results → URL Extraction → Property Scraping → Data Processing → Database Storage
```

## 📁 File Structure & Where to Find Things

### Root Directory (`zillow_wf/`)
```
zillow_wf/
├── docs/                              # Project documentation
│   ├── README.md                      # This file - project overview
│   ├── DATABASE.md                    # Database schema and field explanations
│   ├── PLAN_PROGRESS.md               # Goals, plans, and progress tracking
│   ├── SCRAPE_EXTRACTION_DB.md       # Scraping lessons and technical details
│   └── archive/                       # Historical documentation
├── requirements.txt                    # Python dependencies
├── .env.example                       # Environment configuration template
├── .env.local                         # Local environment variables (create this)
├── flexible_waterfront_extractor.py   # Main extraction engine
├── get_existing_zpids.py             # Database management utility
└── data/                              # Data storage and cache
```

### Data Directory (`zillow_wf/data/`)
```
data/
├── cache/                             # Raw HTML and JSON cache files
│   ├── search_results/                # Search page HTML files
│   └── property_details/              # Property detail page HTML files
├── processed/                         # Processed property data
│   ├── json/                          # Extracted JSON data
│   └── reports/                       # Extraction reports and statistics
├── summary/                           # Run summaries and field completion reports
├── existing_zpids.json               # Database ZPID tracking
└── logs/                             # Processing logs and error reports
```

### Key Scripts & Their Purpose
- **`flexible_waterfront_extractor.py`**: Main extraction engine - processes URLs and cache files
- **`get_existing_zpids.py`**: Database utility - shows existing properties and database status
- **`.env.local`**: Configuration file - contains database credentials and API keys

## 📚 Documentation

### **Essential Guides**
- **[Usage Guide](USAGE_GUIDE.md)** - Comprehensive usage instructions for both scripts
- **[Quick Reference](QUICK_REFERENCE.md)** - Most common commands and quick setup
- **[Database Guide](DATABASE.md)** - Database schema and field explanations
- **[Scraping Guide](SCRAPE_EXTRACTION_DB.md)** - Technical details and lessons learned

### **Scripts Overview**
- **`flexible_waterfront_extractor.py`** - Main extraction engine for processing URLs and search results
- **`extract_urls_only.py`** - Utility script for extracting property URLs from search results

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+ installed
- PostgreSQL database running
- Zyte API key for web scraping
- Git for repository access

### Setup in 5 Minutes
```bash
# 1. Clone and setup
git clone <repository-url>
cd zillow_wf
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env.local
# Edit .env.local with your database and API credentials

# 3. Create database
createdb zillow_wf

# 4. Run first extraction
python flexible_waterfront_extractor.py --mode urls --urls-file <(echo "YOUR_ZILLOW_URL") --limit 5
```

### Basic Usage Examples
```bash
# Extract properties from search results
python flexible_waterfront_extractor.py \
  --mode urls \
  --urls-file <(echo "https://www.zillow.com/fort-lauderdale-fl/waterfront/...") \
  --max-search-pages 3 \
  --timeout 300

# Process existing cache files
python flexible_waterfront_extractor.py \
  --mode cache \
  --cache-dir zillow_wf/data/cache

# Check database status
python get_existing_zpids.py
```

## 📊 Current Status & Performance

### Database Population
- **Total Properties**: 980+ waterfront properties stored
- **Latest Extraction**: 266 new properties processed successfully
- **Success Rate**: 100% database storage success rate
- **Processing Speed**: ~26 minutes for 266 properties

### Data Quality
- **Field Completion Rate**: 96.7% overall across 49 tracked fields
- **Excellent Fields (90-100%)**: 46 out of 49 fields
- **Good Fields (70-89%)**: 1 field
- **Poor Fields (30-49%)**: 2 fields (lot_size, lot_area_value)

### Key Achievements
- ✅ Smart duplicate prevention with ZPID-based filtering
- ✅ Comprehensive field extraction with multiple fallback methods
- ✅ Robust error handling and timeout management
- ✅ Real-time progress tracking and completion reporting

## 🎯 Goals & Requirements

### Primary Goals
1. **Data Collection**: Extract comprehensive waterfront property data from Zillow
2. **Data Quality**: Achieve 98%+ field completion rate across all tracked fields
3. **Scalability**: Process 1000+ properties efficiently with intelligent duplicate prevention
4. **Waterfront Analysis**: Identify and categorize waterfront features for boater analysis

### Technical Requirements
- **Reliability**: 95%+ extraction success rate
- **Performance**: Process 300+ properties in under 20 minutes
- **Data Integrity**: Maintain referential integrity and data consistency
- **Error Recovery**: Graceful handling of network issues and data structure changes

### Business Requirements
- **Waterfront Focus**: Prioritize properties with ocean access, canal front, and boat access
- **Market Analysis**: Support price analysis and market trend identification
- **Geographic Coverage**: Focus on Fort Lauderdale, FL with expansion potential
- **Data Export**: Enable data analysis and reporting capabilities

## 🔧 Configuration & Customization

### Environment Variables (`.env.local`)
```bash
# Database connection
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/zillow_wf

# Zyte API for web scraping
ZYTE_API_KEY=your_zyte_api_key_here

# Scraping behavior
CRAWL_DELAY_SECONDS=2.0
REQUEST_TIMEOUT=300
```

### Command Line Options
```bash
--mode {urls,cache}           # Processing mode
--urls-file URLS_FILE         # File containing URLs to process
--max-search-pages N          # Maximum search pages (default: 3)
--timeout SECONDS             # Request timeout (default: 300)
--limit N                     # Limit properties for testing
--dry-run                     # Process without database updates
```

## 📚 Documentation & Resources

### Core Documentation
- **`docs/README.md`** (this file): Project overview and quick start
- **`docs/DATABASE.md`**: Database schema and field explanations
- **`docs/PLAN_PROGRESS.md`**: Goals, plans, and progress tracking
- **`docs/SCRAPE_EXTRACTION_DB.md`**: Technical lessons and implementation details

### Additional Resources
- **Requirements**: See `requirements.txt` for Python dependencies
- **Environment**: Copy `.env.example` to `.env.local` and configure
- **Logs**: Check `zillow_wf/data/logs/` for processing details
- **Reports**: View field completion reports in `zillow_wf/data/summary/`
- **Archive**: Historical documentation in `docs/archive/`

## 🚨 Troubleshooting & Support

### Common Issues
1. **Database Connection**: Verify PostgreSQL is running and credentials are correct
2. **API Key Issues**: Ensure `ZYTE_API_KEY` is set in `.env.local`
3. **Timeout Errors**: Increase `--timeout` value for complex pages
4. **Missing Dependencies**: Run `pip install -r requirements.txt`

### Getting Help
1. **Check Logs**: Review recent extraction logs in `zillow_wf/data/logs/`
2. **Database Status**: Run `python get_existing_zpids.py` to check connectivity
3. **Documentation**: Review the four main documentation files
4. **Error Messages**: Check console output for specific error details

### Monitoring & Debugging
```bash
# Check extraction status
tail -f zillow_wf/data/summary/run_summary_*.log

# View field completion
cat zillow_wf/data/summary/field_completion_report_*.txt

# Check database
python -c "import psycopg; conn = psycopg.connect('postgresql://username@localhost:5432/zillow_wf'); print('✅ Connected'); conn.close()"
```

## 🤝 Contributing & Development

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Set up local environment with `.env.local`
4. Make changes and test thoroughly
5. Submit a pull request

### Code Standards
- **Python 3.8+**: Use modern Python features and type hints
- **Error Handling**: Implement comprehensive try-catch blocks
- **Documentation**: Add clear docstrings and inline comments
- **Testing**: Create tests for critical extraction logic

### Testing & Validation
```bash
# Test with small dataset
python flexible_waterfront_extractor.py --mode urls --limit 5 --dry-run

# Validate database storage
python get_existing_zpids.py

# Check data quality
cat zillow_wf/data/summary/field_completion_report_*.txt
```

## 📄 License & Legal

### License
This project is licensed under the MIT License - see the LICENSE file for details.

### Legal Considerations
- **Terms of Service**: Respect Zillow's ToS and robots.txt
- **Rate Limiting**: Implement appropriate delays and respect API limits
- **Data Usage**: Internal research use only
- **Privacy**: Do not collect or store personal information

---

## 🎉 Ready to Get Started?

1. **Follow the Quick Start Guide** above to set up your environment
2. **Read the Documentation** to understand the system architecture
3. **Run Your First Extraction** with a small test dataset
4. **Monitor Progress** using the built-in tracking and reporting tools

## 📞 Need Help?

- **Check the Documentation**: Start with this README, then dive into the specialized docs
- **Review the Logs**: Check `zillow_wf/data/logs/` for detailed error information
- **Test Database Connection**: Use `python get_existing_zpids.py`
- **Start Small**: Use `--limit 5` and `--dry-run` for testing

---

**Last Updated**: August 13, 2025  
**Status**: 🟢 **ACTIVE DEVELOPMENT** - Major milestone achieved, ready for expansion  
**Next Milestone**: Process 1000+ total waterfront properties

