# Database Documentation - Zillow Waterfront Properties

## 🗄️ Database Overview

**Database Name**: `zillow_wf`  
**Engine**: PostgreSQL 12+  
**ORM**: SQLAlchemy 2.0+  
**Connection**: `postgresql+psycopg://username:password@localhost:5432/zillow_wf`

## 🏗️ Database Schema

### Core Tables
1. **`listings_summary`** - Basic property information from search results
2. **`listings_detail`** - Comprehensive property data from detail pages
3. **`listings_derived`** - Analyzed waterfront features and computed metrics (planned)

## 📋 Table: `listings_summary`

### Purpose
Stores essential property information extracted from Zillow search result pages. This is the primary table for basic property queries and waterfront analysis.

### Schema
```sql
CREATE TABLE listings_summary (
    id SERIAL PRIMARY KEY,
    zpid VARCHAR(50) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100),
    state VARCHAR(10),
    zip_code VARCHAR(20),
    price DECIMAL(15,2),
    price_formatted VARCHAR(50),
    beds INTEGER,
    baths DECIMAL(4,2),
    home_size_sqft INTEGER,
    lot_size VARCHAR(100),
    year_built INTEGER,
    property_type VARCHAR(100),
    is_condo BOOLEAN,
    is_waterfront BOOLEAN,
    water_type VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    zestimate DECIMAL(15,2),
    rent_zestimate DECIMAL(15,2),
    monthly_oa_fee DECIMAL(10,2),
    monthly_hoa_fee DECIMAL(10,2),
    price_per_sqft DECIMAL(10,2),
    lot_area_value DECIMAL(15,2),
    lot_area_unit VARCHAR(20),
    days_on_zillow INTEGER,
    page_view_count INTEGER,
    favorite_count INTEGER,
    home_status VARCHAR(50),
    contingent_type VARCHAR(50),
    listing_provider VARCHAR(100),
    waterfront_features TEXT,
    water_view BOOLEAN,
    ocean_access BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Field-by-Field Explanation

#### Core Property Identifiers
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `zpid` | VARCHAR(50) | Zillow Property ID | Unique Zillow identifier | Primary lookup key, duplicate prevention |
| `url` | TEXT | Zillow URL | Full property URL | Direct access to property page |
| `address` | TEXT | Search results | Street address | Property location identification |
| `city` | VARCHAR(100) | Search results | City name | Geographic filtering and grouping |
| `state` | VARCHAR(10) | Search results | State abbreviation | Geographic filtering |
| `zip_code` | VARCHAR(20) | Search results | ZIP code | Geographic filtering and market analysis |

#### Financial Information
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `price` | DECIMAL(15,2) | Search results | Property price in dollars | Market analysis, price filtering |
| `price_formatted` | VARCHAR(50) | Search results | Formatted price string | Display and user interface |
| `zestimate` | DECIMAL(15,2) | Property details | Zillow's estimated value | Market comparison and analysis |
| `rent_zestimate` | DECIMAL(15,2) | Property details | Estimated rental value | Investment analysis |
| `monthly_oa_fee` | DECIMAL(10,2) | Property details | Monthly owner association fee | Cost analysis |
| `monthly_hoa_fee` | DECIMAL(10,2) | Property details | Monthly HOA fee | Cost analysis |
| `price_per_sqft` | DECIMAL(10,2) | Calculated | Price divided by square footage | Market comparison |

#### Property Characteristics
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `beds` | INTEGER | Search results | Number of bedrooms | Property filtering and comparison |
| `baths` | DECIMAL(4,2) | Search results | Number of bathrooms | Property filtering and comparison |
| `home_size_sqft` | INTEGER | Search results | Living area in square feet | Size analysis and comparison |
| `lot_size` | VARCHAR(100) | Property details | Lot size description | Lot analysis and waterfront calculations |
| `year_built` | INTEGER | Property details | Year property was built | Age analysis and market trends |
| `property_type` | VARCHAR(100) | Property details | Type of property | Property categorization |

#### Waterfront Features
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `is_waterfront` | BOOLEAN | Search results | Waterfront property flag | Waterfront filtering |
| `water_type` | VARCHAR(100) | Search results | Type of water body | Waterfront categorization |
| `waterfront_features` | TEXT | Property details | Detailed waterfront features | Waterfront analysis |
| `water_view` | BOOLEAN | Property details | Has water view | View analysis |
| `ocean_access` | BOOLEAN | Property details | Has ocean access | Boater analysis |

#### Location Data
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `latitude` | DECIMAL(10,8) | Property details | GPS latitude coordinate | Geographic analysis, mapping |
| `longitude` | DECIMAL(11,8) | Property details | GPS longitude coordinate | Geographic analysis, mapping |
| `lot_area_value` | DECIMAL(15,2) | Property details | Lot area numeric value | Lot size calculations |
| `lot_area_unit` | VARCHAR(20) | Property details | Lot area unit (acres, sqft) | Unit conversion and analysis |

#### Market Data
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `days_on_zillow` | INTEGER | Property details | Days listed on Zillow | Market timing analysis |
| `page_view_count` | INTEGER | Property details | Number of page views | Market interest analysis |
| `favorite_count` | INTEGER | Property details | Number of favorites | Market interest analysis |
| `home_status` | VARCHAR(50) | Property details | Current listing status | Market status tracking |
| `contingent_type` | VARCHAR(50) | Property details | Contingency type | Market condition analysis |
| `listing_provider` | VARCHAR(100) | Property details | Listing agent/office | Market source analysis |

#### Metadata
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `created_at` | TIMESTAMP | System | Record creation timestamp | Audit trail, data freshness |
| `updated_at` | TIMESTAMP | System | Record update timestamp | Audit trail, change tracking |

## 📋 Table: `listings_detail`

### Purpose
Stores comprehensive property information extracted from Zillow property detail pages. This table contains rich data including descriptions, photos, and detailed property features.

### Schema
```sql
CREATE TABLE listings_detail (
    id SERIAL PRIMARY KEY,
    zpid VARCHAR(50) UNIQUE NOT NULL,
    title TEXT,
    description_raw TEXT,
    mls_number VARCHAR(100),
    property_subtype VARCHAR(100),
    html_content TEXT,
    html_size_chars INTEGER,
    reso_facts TEXT,
    price_history TEXT,
    tax_history TEXT,
    schools TEXT,
    parking_info TEXT,
    photos TEXT,
    contact_buttons TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zpid) REFERENCES listings_summary(zpid)
);
```

### Field-by-Field Explanation

#### Core Information
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `zpid` | VARCHAR(50) | Property details | Zillow Property ID | Links to summary table |
| `title` | TEXT | Property details | Property title/headline | Property identification |
| `description_raw` | TEXT | Property details | Raw property description | Content analysis, feature extraction |
| `mls_number` | VARCHAR(100) | Property details | MLS listing number | Market tracking |

#### Property Classification
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `property_subtype` | VARCHAR(100) | Property details | Detailed property type | Property categorization |
| `reso_facts` | TEXT | Property details | RESO standard facts | Standardized property data |

#### Rich Content
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `photos` | TEXT | Property details | JSON array of photo URLs | Media analysis, property visualization |
| `contact_buttons` | TEXT | Property details | JSON array of contact options | Contact information extraction |
| `html_content` | TEXT | Property details | Raw HTML content | Backup parsing, content analysis |
| `html_size_chars` | INTEGER | Property details | HTML content size | Content size analysis |

#### Market History
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `price_history` | TEXT | Property details | JSON array of price changes | Market trend analysis |
| `tax_history` | TEXT | Property details | JSON array of tax records | Tax analysis and planning |
| `schools` | TEXT | Property details | JSON array of school information | Education analysis |
| `parking_info` | TEXT | Property details | JSON array of parking details | Parking analysis |

#### Metadata
| Field | Type | Source | Description | Usage |
|-------|------|--------|-------------|-------|
| `created_at` | TIMESTAMP | System | Record creation timestamp | Audit trail |
| `updated_at` | TIMESTAMP | System | Record update timestamp | Change tracking |

## 🔗 Table Relationships

### Primary Relationships
```
listings_summary (1) ←→ (1) listings_detail
```

- **One-to-One Relationship**: Each property in `listings_summary` has exactly one corresponding record in `listings_detail`
- **Foreign Key**: `listings_detail.zpid` references `listings_summary.zpid`
- **Referential Integrity**: Ensures data consistency between summary and detail information

### Data Flow
1. **Search Results** → `listings_summary` (basic info)
2. **Property Details** → `listings_detail` (comprehensive info)
3. **Analysis** → Queries across both tables for complete property profiles

## 📊 Data Sources & Extraction Methods

### Primary Data Sources
1. **Zillow Search Results**: Basic property information, pricing, basic features
2. **Zillow Property Details**: Comprehensive property data, photos, descriptions
3. **Next.js Hydration Payloads**: Rich JSON data embedded in HTML pages

### Extraction Methods
1. **JSON-First Approach**: Extract from `__NEXT_DATA__` → `gdpClientCache` → `property` objects
2. **HTML Fallback**: Parse HTML content when JSON data is unavailable
3. **Multiple Fallback Strategies**: Ensure data extraction even when page structure changes

### Field Completion Strategy
- **Priority 1**: Extract from primary JSON sources (highest quality)
- **Priority 2**: Parse from HTML content (medium quality)
- **Priority 3**: Use regex patterns and text analysis (lowest quality)

## 🎯 Data Quality & Validation

### Field Completion Targets
- **Core Fields**: 100% completion (ZPID, address, price, etc.)
- **Waterfront Features**: 95%+ completion
- **Market Data**: 90%+ completion
- **Location Data**: 95%+ completion
- **Media Content**: 80%+ completion

### Data Validation Rules
1. **ZPID**: Must be unique, non-null, valid format
2. **Price**: Must be positive number, reasonable range
3. **Coordinates**: Must be valid latitude/longitude values
4. **Dates**: Must be valid timestamps, not in future

### Quality Monitoring
- **Field Completion Reports**: Generated after each extraction run
- **Data Validation**: Automated checks for data integrity
- **Error Tracking**: Logging of extraction failures and data issues

## 🔍 Query Examples

### Basic Property Queries
```sql
-- Get all waterfront properties
SELECT zpid, address, price, waterfront_features 
FROM listings_summary 
WHERE is_waterfront = true;

-- Find properties by price range
SELECT zpid, address, price, beds, baths 
FROM listings_summary 
WHERE price BETWEEN 500000 AND 1000000;

-- Get properties with ocean access
SELECT zpid, address, price, water_type 
FROM listings_summary 
WHERE ocean_access = true;
```

### Waterfront Analysis
```sql
-- Count properties by water type
SELECT water_type, COUNT(*) as property_count 
FROM listings_summary 
WHERE is_waterfront = true 
GROUP BY water_type;

-- Average price by waterfront type
SELECT water_type, AVG(price) as avg_price 
FROM listings_summary 
WHERE is_waterfront = true 
GROUP BY water_type;
```

### Market Analysis
```sql
-- Price trends by property type
SELECT property_type, AVG(price) as avg_price, COUNT(*) as count 
FROM listings_summary 
GROUP BY property_type 
ORDER BY avg_price DESC;

-- Days on market analysis
SELECT 
    CASE 
        WHEN days_on_zillow <= 30 THEN '0-30 days'
        WHEN days_on_zillow <= 90 THEN '31-90 days'
        ELSE '90+ days'
    END as market_time,
    COUNT(*) as property_count,
    AVG(price) as avg_price
FROM listings_summary 
GROUP BY market_time;
```

### Complex Joins
```sql
-- Get complete property profiles
SELECT 
    s.zpid, s.address, s.price, s.beds, s.baths,
    d.description_raw, d.photos, d.price_history
FROM listings_summary s
JOIN listings_detail d ON s.zpid = d.zpid
WHERE s.is_waterfront = true
ORDER BY s.price DESC;
```

## 🚀 Performance & Optimization

### Indexing Strategy
```sql
-- Primary indexes for performance
CREATE INDEX idx_listings_summary_zpid ON listings_summary(zpid);
CREATE INDEX idx_listings_summary_waterfront ON listings_summary(is_waterfront);
CREATE INDEX idx_listings_summary_price ON listings_summary(price);
CREATE INDEX idx_listings_summary_location ON listings_summary(latitude, longitude);

-- Composite indexes for common queries
CREATE INDEX idx_listings_summary_waterfront_price ON listings_summary(is_waterfront, price);
CREATE INDEX idx_listings_summary_city_price ON listings_summary(city, price);
```

### Query Optimization
1. **Use Indexes**: Always query on indexed fields when possible
2. **Limit Results**: Use LIMIT clauses for large result sets
3. **Efficient Joins**: Join on indexed foreign keys
4. **Avoid SELECT ***: Specify only needed fields

### Maintenance
- **Regular VACUUM**: Clean up deleted records and update statistics
- **ANALYZE**: Update table statistics for query planning
- **Index Maintenance**: Monitor index usage and rebuild when needed

## 🔧 Database Administration

### Connection Management
```python
# Example connection string
DATABASE_URL = "postgresql+psycopg://username:password@localhost:5432/zillow_wf"

# Connection pooling
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
```

### Backup & Recovery
```bash
# Create backup
pg_dump zillow_wf > zillow_wf_backup_$(date +%Y%m%d).sql

# Restore backup
psql zillow_wf < zillow_wf_backup_20250813.sql
```

### Monitoring
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
```

---

**Last Updated**: August 13, 2025  
**Database Version**: PostgreSQL 12+  
**Schema Version**: 1.0  
**Next Update**: When new fields or tables are added
