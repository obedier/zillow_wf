# Zillow Waterfront Database Schema Documentation

## Overview
This document provides a complete reference for the database schema used in the Zillow Waterfront Property Scraping project. The database is designed to store comprehensive property data extracted from Zillow listings, with a focus on waterfront properties and their unique characteristics.

## Database Tables

### 1. `listings_summary` - Core Property Information
**Purpose**: Primary table storing essential property details and metadata
**Size**: ~1984 kB (as of August 2025)

| Column Name | Data Type | Nullable | Default | Description |
|-------------|-----------|----------|---------|-------------|
| `zpid` | character varying | NO | NULL | Zillow Property ID (Primary Key) |
| `url` | text | NO | NULL | Full Zillow property URL |
| `address` | character varying | NO | NULL | Street address |
| `city` | character varying | NO | NULL | City name |
| `county` | character varying | YES | NULL | County name |
| `state` | character varying | NO | NULL | State abbreviation |
| `zip_code` | character varying | YES | NULL | ZIP code |
| `price` | integer | YES | NULL | Property price in dollars |
| `d_price_formatted` | character varying | YES | NULL | Formatted price string |
| `beds` | integer | YES | NULL | Number of bedrooms |
| `baths` | integer | YES | NULL | Number of bathrooms |
| `home_size_sqft` | integer | YES | NULL | Home size in square feet |
| `year_built` | integer | YES | NULL | Year the property was built |
| `is_condo` | boolean | YES | NULL | Whether property is a condominium |
| `is_waterfront` | boolean | YES | NULL | Whether property has waterfront access |
| `created_at` | timestamp with time zone | YES | now() | Record creation timestamp |
| `updated_at` | timestamp with time zone | YES | NULL | Record last update timestamp |
| `price_per_sqft` | integer | YES | NULL | Price per square foot |
| `hoa_fee` | text | YES | NULL | HOA fee information |
| `latitude` | numeric | YES | NULL | Geographic latitude |
| `longitude` | numeric | YES | NULL | Geographic longitude |
| `zestimate` | integer | YES | NULL | Zillow's estimated value |
| `rent_zestimate` | integer | YES | NULL | Zillow's estimated rental value |
| `monthly_hoa_fee` | integer | YES | NULL | Monthly HOA fee amount |
| `lot_area_value` | numeric | YES | NULL | Lot area numeric value |
| `lot_area_unit` | character varying | YES | NULL | Lot area unit (sqft, acres, etc.) |
| `days_on_zillow` | integer | YES | NULL | Days property has been on Zillow |
| `page_view_count` | integer | YES | NULL | Number of page views |
| `favorite_count` | integer | YES | NULL | Number of favorites |
| `home_status` | character varying | YES | NULL | Current home status |
| `contingent_type` | character varying | YES | NULL | Contingency type if any |
| `mls_id` | character varying | YES | NULL | MLS identifier |
| `mls_name` | character varying | YES | NULL | MLS name |
| `lot_area_units` | character varying | YES | NULL | Lot area units |
| `home_type` | character varying | YES | NULL | Type of home |
| `property_type_dimension` | character varying | YES | NULL | Property type dimension |
| `listing_provider` | text | YES | NULL | Listing provider information |
| `waterfront_footage` | character varying | YES | NULL | Waterfront footage details |
| `dock_info` | character varying | YES | NULL | Dock information |

### 2. `listings_detail` - Detailed Property Data
**Purpose**: Stores comprehensive property details, descriptions, and extended information

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `id` | integer | Auto-incrementing primary key |
| `zpid` | character varying | Zillow Property ID (Foreign Key) |
| `description_raw` | text | Raw property description text |
| `lot_size_acres` | character varying | Lot size in acres |
| `property_subtype` | character varying | Detailed property subtype |
| `boat_access` | boolean | Whether property has boat access |
| `d_mls_number` | character varying | MLS number |
| `listing_agent` | character varying | Listing agent name |
| `listing_office` | character varying | Listing office name |
| `html_content` | text | Raw HTML content from Zillow |
| `created_at` | timestamp with time zone | Record creation timestamp |
| `updated_at` | timestamp with time zone | Record last update timestamp |
| `price_history` | text | JSON/text of price history |
| `tax_history` | text | JSON/text of tax history |
| `listing_agent_phone` | character varying | Listing agent phone number |
| `reso_facts` | text | RESO standard facts |
| `schools` | text | School information |
| `parking_info` | text | Parking information |
| `on_market_date` | timestamp with time zone | Date property came on market |
| `ownership_type` | character varying | Type of ownership |
| `parcel_number` | character varying | Parcel number |
| `living_area_units` | character varying | Living area units |
| `price_per_sqft` | character varying | Price per square foot |
| `d_description_preview` | character varying | Description preview |
| `d_reso_facts_preview` | character varying | RESO facts preview |
| `d_price_history_preview` | character varying | Price history preview |
| `d_tax_history_preview` | character varying | Tax history preview |
| `d_schools_preview` | character varying | Schools preview |
| `d_parking_info_preview` | character varying | Parking info preview |
| `waterfront_features` | text | Waterfront features description |
| `water_view` | text | Water view information |
| `rooms` | text | Room details |
| `view` | text | View information |
| `dock_info` | text | Detailed dock information |
| `bridge_height` | text | Bridge height information |
| `water_depth` | text | Water depth information |
| `living_area` | text | Living area details |
| `living_area_value` | text | Living area value |
| `canal_info` | text | Canal information |
| `ocean_access` | text | Ocean access details |

### 3. `listings_derived` - Computed and Analyzed Fields
**Purpose**: Stores derived data, calculations, and analysis results

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `id` | integer | Auto-incrementing primary key |
| `zpid` | character varying | Zillow Property ID (Foreign Key) |
| `waterfront_length_ft` | integer | Waterfront length in feet |
| `has_boat_dock` | boolean | Whether property has boat dock |
| `has_boat_lift` | boolean | Whether property has boat lift |
| `has_boat_ramp` | boolean | Whether property has boat ramp |
| `has_marina_access` | boolean | Whether property has marina access |
| `bridge_height_ft` | integer | Bridge height in feet |
| `water_depth_ft` | integer | Water depth in feet |
| `canal_width_ft` | integer | Canal width in feet |
| `water_type_primary` | character varying | Primary water type |
| `water_type_secondary` | character varying | Secondary water type |
| `price_per_waterfront_foot` | numeric | Price per waterfront foot |
| `price_per_building_sqft` | numeric | Price per building square foot |
| `price_per_lot_sqft` | numeric | Price per lot square foot |
| `analysis_confidence` | numeric | Confidence level of analysis |
| `analysis_method` | character varying | Method used for analysis |
| `analysis_notes` | text | Analysis notes and comments |
| `created_at` | timestamp with time zone | Record creation timestamp |
| `updated_at` | timestamp with time zone | Record last update timestamp |

### 4. `property_photos` - Photo Metadata and URLs
**Purpose**: Stores property photo information and multiple resolution URLs

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `id` | integer | Auto-incrementing primary key |
| `zpid` | character varying | Zillow Property ID (Foreign Key) |
| `caption` | text | Photo caption/description |
| `main_url` | text | Main photo URL |
| `jpeg_resolutions` | text | JSON of JPEG resolution URLs |
| `webp_resolutions` | text | JSON of WebP resolution URLs |
| `photo_order` | integer | Photo display order |
| `created_at` | timestamp with time zone | Record creation timestamp |
| `updated_at` | timestamp with time zone | Record last update timestamp |

### 5. `listing_text_content` - Text Content Storage
**Purpose**: Stores extracted text content from property listings

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `id` | integer | Auto-incrementing primary key |
| `zpid` | character varying | Zillow Property ID (Foreign Key) |
| `content_type` | character varying | Type of content |
| `content_text` | text | Extracted text content |
| `extraction_method` | character varying | Method used for extraction |
| `confidence_score` | numeric | Confidence in extraction accuracy |
| `created_at` | timestamp with time zone | Record creation timestamp |
| `updated_at` | timestamp with time zone | Record last update timestamp |

### 6. `wf_data` - Waterfront Analysis Data
**Purpose**: Stores waterfront-specific analysis and measurements

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `id` | integer | Auto-incrementing primary key |
| `zpid` | character varying | Zillow Property ID (Foreign Key) |
| `waterfront_length` | numeric | Waterfront length measurement |
| `water_type` | character varying | Type of water body |
| `access_type` | character varying | Type of water access |
| `analysis_date` | timestamp with time zone | Date of analysis |
| `created_at` | timestamp with time zone | Record creation timestamp |
| `updated_at` | timestamp with time zone | Record last update timestamp |

## Database Relationships

### Primary Keys
- `listings_summary.zpid` - Primary identifier for all properties
- `listings_detail.id` - Auto-incrementing ID for detail records
- `listings_derived.id` - Auto-incrementing ID for derived records
- `property_photos.id` - Auto-incrementing ID for photo records
- `listing_text_content.id` - Auto-incrementing ID for text content
- `wf_data.id` - Auto-incrementing ID for waterfront data

### Foreign Keys
- `listings_detail.zpid` → `listings_summary.zpid`
- `listings_derived.zpid` → `listings_summary.zpid`
- `property_photos.zpid` → `listings_summary.zpid`
- `listing_text_content.zpid` → `listings_summary.zpid`
- `wf_data.zpid` → `listings_summary.zpid`

## Data Flow Architecture

```
Zillow Property Page → HTML Extraction → JSON Parsing → Data Processing → Database Storage
                                    ↓
                              Multiple Tables
                                    ↓
                              Analysis & Reporting
```

## Indexing Strategy

### Recommended Indexes
1. **Primary Index**: `listings_summary.zpid` (already indexed as primary key)
2. **Geographic Index**: `listings_summary.latitude, listings_summary.longitude`
3. **Price Index**: `listings_summary.price`
4. **Waterfront Index**: `listings_summary.is_waterfront`
5. **Date Index**: `listings_summary.created_at`
6. **Location Index**: `listings_summary.city, listings_summary.state`

### Performance Considerations
- Use `zpid` for all joins (most efficient)
- Consider composite indexes for common query patterns
- Monitor query performance with `EXPLAIN ANALYZE`

## Data Quality Metrics

### Field Completion Rates (as of August 2025)
- **Core Fields**: 100% (zpid, address, price, basic details)
- **Financial Data**: 95%+ (estimates, taxes, fees)
- **Property Features**: 90%+ (amenities, waterfront features)
- **Media Content**: 85%+ (photos, virtual tours)
- **Overall Completion**: 89.4%

### Data Validation Rules
1. **Required Fields**: zpid, url, address, city, state
2. **Numeric Validation**: price, beds, baths, home_size_sqft
3. **Geographic Validation**: latitude (-90 to 90), longitude (-180 to 180)
4. **Date Validation**: created_at, updated_at, on_market_date

## Maintenance and Optimization

### Regular Maintenance Tasks
1. **Vacuum**: Run `VACUUM ANALYZE` weekly
2. **Statistics Update**: Update table statistics monthly
3. **Index Rebuild**: Rebuild fragmented indexes quarterly
4. **Data Archiving**: Archive old data annually

### Performance Monitoring
1. **Query Performance**: Monitor slow queries
2. **Table Sizes**: Track growth patterns
3. **Index Usage**: Monitor index effectiveness
4. **Connection Pool**: Monitor connection usage

## Backup and Recovery

### Backup Strategy
1. **Daily Incremental**: Back up changed data daily
2. **Weekly Full**: Complete database backup weekly
3. **Monthly Archive**: Long-term archival backup monthly

### Recovery Procedures
1. **Point-in-Time Recovery**: Restore to specific timestamp
2. **Table-Level Recovery**: Restore individual tables
3. **Data Validation**: Verify data integrity after recovery

---

*Last Updated: August 15, 2025*
*Database Version: Production*
*Total Tables: 6*
*Total Records: 580+ waterfront properties*
*Schema Status: Stable and Production Ready*
