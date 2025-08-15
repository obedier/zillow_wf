#!/usr/bin/env python3
"""
Flexible waterfront property extractor that searches deeper in the JSON structure
and saves JSON snippets for comparison across sessions.
This version is much more resilient to Zillow's data structure changes.

NEW FEATURES:
- Process existing cache files to fill database gaps
- Update existing database records with missing fields
- Support both URL scraping and file processing modes
- Batch processing with progress tracking
"""

import asyncio
import httpx
import json
import re
import base64
from pathlib import Path
from typing import Any, Dict, Optional, List, Set, Tuple, Union
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
import hashlib
from sqlalchemy import create_engine, text
import time
from tqdm import tqdm
import argparse
import glob

# Set up logging
import logging.handlers

# Create logs directory if it doesn't exist
log_dir = Path('zillow_wf/logs')
log_dir.mkdir(parents=True, exist_ok=True)

# Set up file handler with rotation
log_file = log_dir / 'flexible_waterfront_extractor.log'
file_handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# Set up console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Set up root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Suppress SQLAlchemy logging (SQL queries)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

class FlexibleWaterfrontExtractor:
    """Flexible extractor for waterfront properties with deep JSON searching and direct DB storage"""
    
    def __init__(self, api_key: str = None, enable_db_storage: bool = False, timeout_seconds: int = 30, cache_mode: bool = False, max_search_pages: int = 20, max_properties_per_search: int = 1000, save_html: bool = False, save_processed: bool = False, save_next_data: bool = False, save_summary: bool = False, save_cache: bool = True, simple_logging: bool = False, max_concurrent_properties: int = 5, save_urls_list: bool = False, continue_from_file: str = None):
        # Load environment variables (prefer .env.local if present)
        load_dotenv('.env.local')
        load_dotenv('.env')
        
        self.api_key = api_key or os.getenv('ZYTE_API_KEY')
        if not self.api_key and not cache_mode:
            raise ValueError("ZYTE_API_KEY environment variable is required for URL scraping mode")
        
        self.enable_db_storage = enable_db_storage
        self.timeout_seconds = timeout_seconds
        self.cache_mode = cache_mode
        self.max_search_pages = max_search_pages
        self.max_properties_per_search = max_properties_per_search
        
        # File saving options
        self.save_html = save_html
        self.save_processed = save_processed
        self.save_next_data = save_next_data
        self.save_summary = save_summary
        self.save_cache = save_cache
        
        # Simple logging and counter tracking
        self.simple_logging = simple_logging
        self.max_concurrent_properties = max_concurrent_properties
        self.save_urls_list = save_urls_list
        self.continue_from_file = continue_from_file
        self.counters = {
            'search_results_found': 0,
            'properties_scraped': 0,
            'properties_extracted': 0,
            'properties_added': 0,
            'properties_updated': 0,
            'properties_skipped': 0,
            'errors': 0
        }
        
        # Field tracking for completion analysis
        self.field_tracker = {
            'total_properties': 0,
            'fields_found': {},
            'fields_missing': set(),
            'field_completion': {}
        }
        
        # Load existing ZPIDs to avoid duplicate scraping
        self.existing_zpids = set()
        # Create data_dir if it doesn't exist
        self.data_dir = Path('data')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing ZPIDs (this will also initialize database if needed)
        self._load_existing_zpids()
        
        # Define field mappings for database updates
        self.summary_fields = [
            'zpid', 'address', 'city', 'state', 'zip_code', 'price', 'beds', 'baths', 'home_size_sqft',
            'year_built', 'property_type', 'home_type', 'property_type_dimension',
            'lot_area_value', 'lot_area_units', 'county', 'mls_id', 'mls_name', 'mls_number',
            'contingent_type', 'listing_provider', 'water_body_name', 'hoa_fee', 'tax_annual_amount',
            'tax_assessed_value', 'waterfront_features', 'water_view', 'view', 'rooms',
            'price_per_sqft', 'on_market_date', 'ownership_type', 'parcel_number'
        ]
        
        self.detail_fields = [
            'zpid', 'description_raw', 'dock_info', 'bridge_height', 'water_depth', 'canal_info',
            'ocean_access', 'ownership_type', 'd_mls_number', 'listing_agent', 'listing_office',
            'listing_agent_phone', 'lot_size_acres', 'price_history', 'tax_history', 
            'reso_facts', 'schools', 'parking_info'
        ]
        
        # Define all expected fields for tracking
        self.expected_fields = {
            'zpid': ['zpid'],
            'url': ['url'],
            'address': ['address'],
            'price': ['price'],
            'bedrooms': ['bedrooms'],
            'bathrooms': ['bathrooms'],
            'livingArea': ['livingArea'],
            'title': ['title'],
            'property_subtype': ['property_subtype'],
            'home_type': ['home_type'],
            'property_type_dimension': ['property_type_dimension'],
            'lot_size': ['lot_size'],
            'listing_agent': ['listing_agent'],
            'listing_office': ['listing_office'],
            'listing_agent_phone': ['listing_agent_phone'],
            'home_status': ['home_status'],
            'is_condo': ['is_condo'],
            'is_waterfront': ['is_waterfront'],
            'latitude': ['latitude'],
            'longitude': ['longitude'],
            'zestimate': ['zestimate'],
            'rent_zestimate': ['rent_zestimate'],
            'days_on_zillow': ['days_on_zillow'],
            'page_view_count': ['page_view_count'],
            'favorite_count': ['favorite_count'],
            'on_market_date': ['on_market_date'],
            'waterfront_features': ['waterfront_features'],
            'water_view': ['water_view'],
            'view': ['view'],
            'rooms': ['rooms'],
            'price_per_sqft': ['price_per_sqft'],
            'photos': ['photos'],
            'photo_count': ['photo_count'],
            'description': ['description'],
            'price_history': ['price_history'],
            'tax_history': ['tax_history'],
            'schools': ['schools'],
            'parking_info': ['parking_info'],
            'additional_features': ['additional_features'],
            'community_info': ['community_info'],
            'listing_details': ['listing_details'],
            'year_built': ['year_built'],
            'ownership_type': ['ownership_type'],
            'parcel_number': ['parcel_number'],
            'listing_provider': ['listing_provider'],
            'mls_id': ['mls_id'],
            'mls_name': ['mls_name'],
            'lot_area_value': ['lot_area_value'],
            'lot_area_units': ['lot_area_units']
        }
        
        # Initialize field tracking
        self._initialize_field_tracking()
        
        # Log configuration
        if self.api_key:
            logger.info(f"🔑 Using Zyte API key: {self.api_key[:8]}...")
        else:
            logger.info("🔑 No Zyte API key provided (cache mode only)")
        
        logger.info(f"⏱️ Timeout set to {self.timeout_seconds} seconds")
        
        # Database connection
        if enable_db_storage:
            database_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://osamabedier@localhost:5432/zillow_wf')
            self.db_engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=300)
            logger.info(f"🗄️ Database storage enabled: {database_url}")
        else:
            self.db_engine = None
            logger.info("🗄️ Database storage disabled")
        
        # Standard data directories
        root = Path('.')
        self.data_dir = root / 'zillow_wf' / 'data'
        self.html_dir = self.data_dir / 'html'
        self.next_dir = self.data_dir / 'next_data'
        self.cache_dir = self.data_dir / 'cache'
        self.processed_dir = self.data_dir / 'processed'
        self.summary_dir = self.data_dir / 'summary'
        for d in [self.html_dir, self.next_dir, self.cache_dir, self.processed_dir, self.summary_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Waterfront keywords to search for
        self.waterfront_keywords = {
            'waterfront': ['waterfront', 'water front', 'water-front', 'water frontage'],
            'ocean': ['ocean', 'oceanfront', 'ocean front', 'ocean-front', 'ocean access', 'ocean-access'],
            'intracoastal': ['intracoastal', 'intra-coastal', 'icw'],
            'canal': ['canal', 'canal front', 'canal-front', 'canal access'],
            'river': ['river', 'riverfront', 'river front', 'river-front'],
            'lake': ['lake', 'lakefront', 'lake front', 'lake-front'],
            'bay': ['bay', 'bayfront', 'bay front', 'bay-front'],
            'dock': ['dock', 'docking', 'boat dock', 'yacht dock', 'private dock'],
            'boat': ['boat', 'boat access', 'boat-access', 'yacht', 'yacht access'],
            'marina': ['marina', 'marina access', 'marina-access'],
            'water_depth': ['water depth', 'water-depth', 'deep water', 'deep-water', 'shallow draft'],
            'bridge_height': ['bridge height', 'bridge-height', 'fixed bridge', 'no fixed bridge'],
            'water_view': ['water view', 'water-view', 'water vista', 'panoramic water', 'waterfront view']
        }
        
        # Fields to extract with multiple possible paths
        self.extraction_paths = {
            'waterfront_features': [
                'resoFacts.waterfrontFeatures',
                'waterfrontFeatures',
                'property.waterfrontFeatures',
                'listing.waterfrontFeatures'
            ],
            'water_view': [
                'resoFacts.waterView',
                'waterView',
                'property.waterView',
                'listing.waterView'
            ],
            'on_market_date': [
                'resoFacts.onMarketDate',
                'onMarketDate',
                'property.onMarketDate',
                'listing.onMarketDate',
                'comingSoonOnMarketDate'
            ],
            'ownership_type': [
                'resoFacts.ownershipType',
                'ownershipType',
                'property.ownershipType',
                'listing.ownershipType'
            ],
            'parcel_number': [
                'resoFacts.parcelNumber',
                'parcelNumber',
                'property.parcelNumber',
                'listing.parcelNumber'
            ],
            'rooms': [
                'resoFacts.rooms',
                'rooms',
                'property.rooms',
                'listing.rooms'
            ],
            'view': [
                'resoFacts.view',
                'view',
                'property.view',
                'listing.view'
            ],
            'price_per_sqft': [
                'resoFacts.pricePerSquareFoot',
                'pricePerSquareFoot',
                'property.pricePerSquareFoot',
                'listing.pricePerSquareFoot'
            ],
            'lot_size': [
                'resoFacts.lotSize',
                'lotSize',
                'property.lotSize',
                'listing.lotSize'
            ],
            'year_built': [
                'resoFacts.yearBuilt',
                'yearBuilt',
                'property.yearBuilt',
                'listing.yearBuilt'
            ],
            # Additional summary/detail fields
            'zestimate': [
                'zestimate', 'property.zestimate'
            ],
            'rent_zestimate': [
                'rentZestimate', 'property.rentZestimate'
            ],
            'monthly_hoa_fee': [
                'monthlyHoaFee', 'property.monthlyHoaFee', 'resoFacts.monthlyHoaFee'
            ],
            'days_on_zillow': [
                'daysOnZillow', 'property.daysOnZillow'
            ],
            'page_view_count': [
                'pageViewCount', 'property.pageViewCount'
            ],
            'favorite_count': [
                'favoriteCount', 'property.favoriteCount'
            ],
            'home_status': [
                'homeStatus', 'property.homeStatus'
            ],
            'listing_provider': [
                'listingProvider', 'property.listingProvider'
            ],
            'mls_id': [
                'mlsid', 'mlsId', 'property.mlsid'
            ],
            'mls_name': [
                'attributionInfo.mlsName', 'mlsName'
            ],
            'lot_area_value': [
                'lotAreaValue', 'property.lotAreaValue'
            ],
            'lot_area_units': [
                'lotAreaUnits', 'property.lotAreaUnits', 'lotAreaUnit'
            ],
            'home_type': [
                'homeType', 'property.homeType'
            ],
            'property_type_dimension': [
                'propertyTypeDimension', 'property.propertyTypeDimension'
            ]
        }
    
    def _initialize_field_tracking(self):
        """Initialize field tracking structure"""
        for category, fields in self.expected_fields.items():
            for field in fields:
                self.field_tracker['fields_found'][field] = 0
                self.field_tracker['field_completion'][field] = 0.0
    
    def _track_field_completion(self, property_data: Dict[str, Any]):
        """Track which fields were found for this property"""
        # Add property data to tracking
        if 'properties_processed' not in self.field_tracker:
            self.field_tracker['properties_processed'] = []
        self.field_tracker['properties_processed'].append(property_data)
        self.field_tracker['total_properties'] = len(self.field_tracker['properties_processed'])
        
        for field_name, field_paths in self.expected_fields.items():
            # Check if field exists and has non-empty value
            value = property_data.get(field_name)
            if value is not None and value != '' and value != [] and value != {}:
                self.field_tracker['fields_found'][field_name] += 1
            else:
                # Track missing field for this property
                if field_name not in self.field_tracker['fields_missing']:
                    self.field_tracker['fields_missing'].add(field_name)
        
        # Update completion percentages
        for field in self.field_tracker['fields_found']:
            if self.field_tracker['total_properties'] > 0:
                self.field_tracker['field_completion'][field] = (
                    self.field_tracker['fields_found'][field] / self.field_tracker['total_properties']
                ) * 100
    
    def _load_existing_zpids(self):
        """Load existing ZPIDs from the database to avoid duplicate scraping"""
        try:
            if self.enable_db_storage and hasattr(self, 'db_engine'):
                # Query database directly for existing ZPIDs
                with self.db_engine.connect() as conn:
                    result = conn.execute(text("SELECT zpid FROM listings_summary"))
                    zpids = [str(row[0]) for row in result.fetchall()]
                    self.existing_zpids = set(zpids)
                    logger.info(f"📋 Loaded {len(self.existing_zpids)} existing ZPIDs from database")
            else:
                # Fallback to file-based loading
                zpids_file = self.data_dir / 'existing_zpids.json'
                if zpids_file.exists():
                    with open(zpids_file, 'r') as f:
                        zpids = json.load(f)
                        self.existing_zpids = set(zpids)
                        logger.info(f"📋 Loaded {len(self.existing_zpids)} existing ZPIDs from {zpids_file}")
                else:
                    logger.warning(f"⚠️ No existing ZPIDs file found at {zpids_file}")
        except Exception as e:
            logger.error(f"❌ Error loading existing ZPIDs: {e}")
            self.existing_zpids = set()
    
    def _is_property_already_scraped(self, zpid: str) -> bool:
        """Check if a property has already been scraped (legacy method - use _is_property_already_scraped_db instead)"""
        return zpid in self.existing_zpids
    
    def _simple_log(self, message: str):
        """Simple logging that just shows key progress updates"""
        if self.simple_logging:
            print(f"📊 {message}")
    
    def _update_counter(self, counter_name: str, increment: int = 1):
        """Update counter and log if simple logging is enabled"""
        if counter_name in self.counters:
            self.counters[counter_name] += increment
            if self.simple_logging:
                self._simple_log(f"{counter_name.replace('_', ' ').title()}: {self.counters[counter_name]}")

    def _save_urls_list(self, urls: List[str], search_url: str):
        """Save extracted URLs to a file for later continuation"""
        if not self.save_urls_list:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/urls_list_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write(f"# URLs extracted from: {search_url}\n")
                f.write(f"# Extracted on: {datetime.now().isoformat()}\n")
                f.write(f"# Total URLs: {len(urls)}\n\n")
                for url in urls:
                    f.write(f"{url}\n")
            
            logger.info(f"✅ Saved {len(urls)} URLs to {filename}")
            if self.simple_logging:
                self._simple_log(f"Saved {len(urls)} URLs to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save URLs list: {e}")

    def _load_urls_from_file(self, filename: str) -> List[str]:
        """Load URLs from a previously saved file"""
        try:
            with open(filename, 'r') as f:
                urls = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        urls.append(line)
            
            logger.info(f"✅ Loaded {len(urls)} URLs from {filename}")
            if self.simple_logging:
                self._simple_log(f"Loaded {len(urls)} URLs from {filename}")
            return urls
        except Exception as e:
            logger.error(f"❌ Failed to load URLs from {filename}: {e}")
            return []

    def _show_simple_summary(self):
        """Display a simple summary of extraction results"""
        if not self.simple_logging:
            return
        
        print("\n" + "="*60)
        print("📊 EXTRACTION SUMMARY")
        print("="*60)
        print(f"🔍 Search Results Found: {self.counters['search_results_found']}")
        print(f"🌐 Properties Scraped: {self.counters['properties_scraped']}")
        print(f"✅ Properties Extracted: {self.counters['properties_extracted']}")
        print(f"🆕 Properties Added: {self.counters['properties_added']}")
        print(f"🔄 Properties Updated: {self.counters['properties_updated']}")
        print(f"⏭️ Properties Skipped: {self.counters['properties_skipped']}")
        print(f"❌ Errors: {self.counters['errors']}")
        print("="*60)

    async def _is_property_already_scraped_db(self, zpid: str) -> bool:
        """Check database directly for existing property"""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM listings_summary WHERE zpid = :zpid"), {'zpid': zpid})
                count = result.scalar()
                logger.info(f"🔍 Database check for ZPID {zpid}: found {count} records")
                return count > 0
        except Exception as e:
            logger.error(f"Error checking database for ZPID {zpid}: {e}")
            return False  # If we can't check, assume it's new
    
    def _generate_completion_report(self) -> str:
        """Generate a comprehensive field completion report"""
        if not self.field_tracker:
            return "No field tracking data available"
        
        total_properties = len(self.field_tracker.get('properties_processed', []))
        if total_properties == 0:
            return "No properties processed yet"
        
        # Calculate completion rates for each field
        field_stats = {}
        for field_name in self.expected_fields.keys():
            found_count = sum(1 for prop_data in self.field_tracker['properties_processed'] 
                            if prop_data.get(field_name) is not None and 
                            prop_data.get(field_name) != '' and 
                            prop_data.get(field_name) != [] and
                            prop_data.get(field_name) != {})
            
            completion_rate = (found_count / total_properties) * 100
            field_stats[field_name] = {
                'found_count': found_count,
                'completion_rate': completion_rate
            }
        
        # Sort fields by completion rate
        sorted_fields = sorted(field_stats.items(), key=lambda x: x[1]['completion_rate'], reverse=True)
        
        # Categorize fields by completion rate
        excellent = [(f, s) for f, s in sorted_fields if s['completion_rate'] >= 90]
        good = [(f, s) for f, s in sorted_fields if 70 <= s['completion_rate'] < 90]
        fair = [(f, s) for f, s in sorted_fields if 50 <= s['completion_rate'] < 70]
        poor = [(f, s) for f, s in sorted_fields if 30 <= s['completion_rate'] < 50]
        missing = [(f, s) for f, s in sorted_fields if s['completion_rate'] < 30]
        
        # Calculate overall completion rate
        overall_completion = sum(s['completion_rate'] for s in field_stats.values()) / len(field_stats)
        
        # Database success tracking
        db_success_count = sum(1 for prop_data in self.field_tracker['properties_processed'] 
                              if prop_data.get('_database_stored', False))
        db_success_rate = (db_success_count / total_properties) * 100 if total_properties > 0 else 0
        
        report = f"""================================================================================
📊 FIELD COMPLETION ANALYSIS REPORT
================================================================================
📈 Total Properties Processed: {total_properties}

🗄️ DATABASE STORAGE SUCCESS RATE: {db_success_rate:.1f}% ({db_success_count}/{total_properties})
   ✅ Successfully Stored: {db_success_count}
   ❌ Failed to Store: {total_properties - db_success_count}

🏆 EXCELLENT COMPLETION (90-100%): {len(excellent)} fields"""
        
        for field_name, stats in excellent:
            report += f"\n  ✅ {field_name}: {stats['completion_rate']:.1f}%"
        
        if good:
            report += f"\n\n👍 GOOD COMPLETION (70-89%): {len(good)} fields"
            for field_name, stats in good:
                report += f"\n  ✅ {field_name}: {stats['completion_rate']:.1f}%"
        
        if fair:
            report += f"\n\n⚠️ FAIR COMPLETION (50-69%): {len(fair)} fields"
            for field_name, stats in fair:
                report += f"\n  ⚠️ {field_name}: {stats['completion_rate']:.1f}%"
        
        if poor:
            report += f"\n\n❌ POOR COMPLETION (30-49%): {len(poor)} fields"
            for field_name, stats in poor:
                report += f"\n  ❌ {field_name}: {stats['completion_rate']:.1f}%"
        
        if missing:
            report += f"\n\n🚫 MISSING/EMPTY FIELDS (0-29%): {len(missing)} fields"
            for field_name, stats in missing:
                report += f"\n  🚫 {field_name}: {stats['completion_rate']:.1f}%"
        
        report += f"""

📊 SUMMARY STATISTICS:
  Total Fields Tracked: {len(field_stats)}
  Excellent (90-100%): {len(excellent)} fields
  Good (70-89%): {len(good)} fields
  Fair (50-69%): {len(fair)} fields
  Poor (30-49%): {len(poor)} fields
  Missing (0-29%): {len(missing)} fields
  Overall Completion Rate: {overall_completion:.1f}%

🎯 RECOMMENDATIONS:
  • Focus on improving extraction for {len(missing)} missing fields
  • Investigate why {len(poor)} fields have low completion rates
  • Consider enhancing extraction logic for {len(fair)} fair fields
  • Database storage success rate: {db_success_rate:.1f}% - {'Excellent' if db_success_rate >= 90 else 'Good' if db_success_rate >= 70 else 'Fair' if db_success_rate >= 50 else 'Poor'} performance
================================================================================
"""
        return report
    
    async def fetch_property_page_zyte(self, url: str) -> Optional[str]:
        """Fetch property page via Zyte API"""
        try:
            logger.info(f"Fetching property page via Zyte: {url}")
            payload = {
                "url": url, 
                "httpResponseBody": True
            }
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    "https://api.zyte.com/v1/extract",
                    auth=(self.api_key, ""),
                    json=payload
                )
                logger.info(f"Zyte response status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    body_b64 = data.get('httpResponseBody')
                    if body_b64:
                        html_content = base64.b64decode(body_b64).decode("utf-8")
                        logger.info(f"✅ Successfully fetched HTML via Zyte ({len(html_content)} characters)")
                        return html_content
                    else:
                        logger.warning("No httpResponseBody in Zyte response")
                        return None
                else:
                    logger.error(f"Zyte API error: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching property page via Zyte: {e}")
            return None
    
    def extract_next_data_payload(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract __NEXT_DATA__ payload from HTML"""
        try:
            # Find the __NEXT_DATA__ script tag
            pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                payload_text = match.group(1)
                payload = json.loads(payload_text)
                logger.info(f"✅ Extracted __NEXT_DATA__ payload ({len(payload_text)} characters)")
                return payload
            else:
                logger.warning("No __NEXT_DATA__ script tag found")
                return None
        except Exception as e:
            logger.error(f"Error extracting __NEXT_DATA__ payload: {e}")
            return None
    
    def extract_raw_next_data(self, html_content: str) -> Optional[str]:
        """Extract raw __NEXT_DATA__ script content as string (with backslashes, quotes, etc.)"""
        try:
            pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                raw_text = match.group(1)
                logger.info(f"✅ Extracted raw __NEXT_DATA__ content ({len(raw_text)} characters)")
                return raw_text
            else:
                logger.warning("No __NEXT_DATA__ script tag found for raw extraction")
                return None
        except Exception as e:
            logger.error(f"Error extracting raw __NEXT_DATA__ content: {e}")
            return None
    
    def extract_processed_next_data(self, html_content: str) -> Optional[str]:
        """Extract processed __NEXT_DATA__ content with cleaned backslashes and quotes"""
        try:
            pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                raw_text = match.group(1)
                # Clean up common JSON escaping issues
                processed_text = raw_text.replace('\\"', '"').replace('\\\\', '\\')
                logger.info(f"✅ Extracted processed __NEXT_DATA__ content ({len(processed_text)} characters)")
                return processed_text
            else:
                logger.warning("No __NEXT_DATA__ script tag found for processed extraction")
                return None
        except Exception as e:
            logger.error(f"Error extracting processed __NEXT_DATA__ content: {e}")
            return None
    
    def extract_gdp_client_cache(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract gdpClientCache from Next.js payload"""
        try:
            # Navigate to gdpClientCache
            page_props = payload.get('props', {}).get('pageProps', {})
            component_props = page_props.get('componentProps', {})
            gdp_cache = component_props.get('gdpClientCache')
            
            if gdp_cache:
                # Parse the stringified JSON
                cache_data = json.loads(gdp_cache)
                logger.info(f"✅ Extracted gdpClientCache with {len(cache_data)} keys")
                return cache_data
            else:
                logger.warning("No gdpClientCache found in componentProps")
                return None
        except Exception as e:
            logger.error(f"Error extracting gdpClientCache: {e}")
            return None
    
    def get_nested_value(self, obj: Any, path: str) -> Any:
        """Get nested value from object using dot notation path"""
        try:
            keys = path.split('.')
            current = obj
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except:
            return None
    
    def search_for_waterfront_info(self, data: Any, path: str = "") -> List[str]:
        """Recursively search for waterfront-related keywords in the data"""
        keywords = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, str):
                    # Check if the string contains waterfront keywords
                    if any(keyword in value.lower() for keyword in ['waterfront', 'ocean', 'intracoastal', 'canal', 'dock', 'boat', 'marina', 'slip', 'bridge', 'depth']):
                        keywords.append(f"{current_path}: {value}")
                elif isinstance(value, (dict, list)):
                    keywords.extend(self.search_for_waterfront_info(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                keywords.extend(self.search_for_waterfront_info(item, current_path))
        
        return keywords
    
    def apply_regex_patterns(self, text: str, pattern: str) -> List[str]:
        """Apply regex patterns to extract specific information from text"""
        if not text or not pattern:
            return []
        
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            return matches if matches else []
        except re.error:
            return []
    
    def apply_enhanced_regex_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Apply a list of regex patterns to extract specific information from text"""
        matches = []
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matches.append(f"{match.group(0)}") # Capture the full match
        return matches

    def apply_multi_source_regex(self, field_name: str, patterns: List[str], 
                                description: str = None, next_data_raw: str = None, 
                                next_data_processed: str = None) -> Dict[str, List[str]]:
        """
        Apply regex patterns to multiple data sources and return results for each source
        
        Args:
            field_name: Name of the field being extracted
            patterns: List of regex patterns to apply
            description: Clean description text from Next.js data
            next_data_raw: Raw Next.js data string (with backslashes, quotes, etc.)
            next_data_processed: Processed/cleaned Next.js data string
        
        Returns:
            Dictionary with results from each data source
        """
        results = {
            'regex_description': [],
            'regex_nextdata': [],
            'regex_processed': []
        }
        
        # Apply to description field (current method)
        if description:
            results['regex_description'] = self.apply_enhanced_regex_patterns(description, patterns)
        
        # Apply to raw Next.js data
        if next_data_raw:
            results['regex_nextdata'] = self.apply_enhanced_regex_patterns(next_data_raw, patterns)
        
        # Apply to processed Next.js data
        if next_data_processed:
            results['regex_processed'] = self.apply_enhanced_regex_patterns(next_data_processed, patterns)
        
        # Log which sources found matches
        sources_with_matches = [source for source, matches in results.items() if matches]
        if sources_with_matches:
            logger.info(f"🔍 Regex matches for {field_name} found in: {', '.join(sources_with_matches)}")
        
        return results

    def generate_field_name_variations(self, field_name: str) -> List[str]:
        """
        Generate various field name variations for flexible matching
        
        Args:
            field_name: Base field name (e.g., 'year_built')
        
        Returns:
            List of field name variations to search for
        """
        variations = []
        
        # Original field name
        variations.append(field_name)
        
        # Convert snake_case to camelCase
        if '_' in field_name:
            camel_case = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(field_name.split('_')))
            variations.append(camel_case)
        
        # Convert camelCase to snake_case
        if any(c.isupper() for c in field_name) and not field_name.startswith('_'):
            snake_case = ''.join(['_' + c.lower() if c.isupper() else c for c in field_name]).lstrip('_')
            variations.append(snake_case)
        
        # Common Zillow variations
        field_variations = {
            'year_built': ['yearBuilt', 'Year Built', 'yearBuilt', 'constructionYear'],
            'mls_id': ['mlsId', 'mlsID', 'mls_number', 'mlsNumber'],
            'price_history': ['priceHistory', 'price_history', 'priceHistoryData'],
            'price_per_sqft': ['pricePerSqft', 'pricePerSquareFoot', 'pricePerSqFt', 'pricePerSquareFeet'],
            'lot_size': ['lotSize', 'lot_size', 'lotSizeAcres', 'lotSizeSqFt'],
            'home_size_sqft': ['livingArea', 'homeSize', 'home_size', 'squareFootage'],
            'bedrooms': ['beds', 'bedrooms', 'bedRooms', 'bed_count'],
            'bathrooms': ['baths', 'bathrooms', 'bathRooms', 'bath_count'],
            'dock_info': ['dockInfo', 'dock_info', 'dockDetails', 'dockFeatures'],
            'bridge_height': ['bridgeHeight', 'bridge_height', 'bridgeClearance', 'bridgeInfo'],
            'water_depth': ['waterDepth', 'water_depth', 'depth', 'waterLevel'],
            'canal_info': ['canalInfo', 'canal_info', 'canalDetails', 'canalFeatures'],
            'ocean_access': ['oceanAccess', 'ocean_access', 'oceanView', 'oceanFront'],
            'waterfront_features': ['waterfrontFeatures', 'waterfront_features', 'waterfrontInfo'],
            'water_view': ['waterView', 'water_view', 'waterfrontView', 'waterViewType']
        }
        
        if field_name in field_variations:
            variations.extend(field_variations[field_name])
        
        # Add partial name variations (for multi-word fields)
        words = field_name.replace('_', ' ').split()
        if len(words) > 1:
            # Search for partial matches (e.g., "year" + "built" variations)
            for word in words:
                variations.append(word.lower())
                variations.append(word.capitalize())
        
        return list(set(variations))  # Remove duplicates

    def extract_field_flexible(self, field_name: str, cache_data: Dict[str, Any], 
                              next_data_raw: str = None, next_data_processed: str = None,
                              html_content: str = None) -> Any:
        """
        Extract field value using multiple strategies and data sources
        
        Args:
            field_name: Name of the field to extract
            cache_data: Parsed gdpClientCache data
            next_data_raw: Raw Next.js data string
            next_data_processed: Processed Next.js data string
            html_content: Raw HTML content
        
        Returns:
            Extracted field value or None
        """
        field_variations = self.generate_field_name_variations(field_name)
        logger.info(f"🔍 Searching for field '{field_name}' with variations: {field_variations[:5]}...")
        
        # Strategy 1: JSON path search in cache data (most reliable)
        value = self.search_json_paths_flexible(cache_data, field_variations)
        if value is not None:
            # Truncate long values to keep logs readable
            display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            logger.info(f"✅ Found '{field_name}' via JSON path: {display_value}")
            return value
        
        # Strategy 2: Regex search in processed cache data (cleaner)
        if next_data_processed:
            value = self.search_regex_in_text(next_data_processed, field_variations, field_name)
            if value is not None:
                display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                logger.info(f"✅ Found '{field_name}' via regex in processed data: {display_value}")
                return value
        
        # Strategy 3: Regex search in raw Next.js data (fallback)
        if next_data_raw:
            value = self.search_regex_in_text(next_data_raw, field_variations, field_name)
            if value is not None:
                display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                logger.info(f"✅ Found '{field_name}' via regex in raw data: {display_value}")
                return value
        
        # Strategy 4: HTML content search (last resort)
        if html_content:
            value = self.search_regex_in_text(html_content, field_variations, field_name)
            if value is not None:
                display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                logger.info(f"✅ Found '{field_name}' via HTML regex: {display_value}")
                return value
        
        logger.warning(f"⚠️ Field '{field_name}' not found in any data source")
        return None

    def search_json_paths_flexible(self, cache_data: Dict[str, Any], field_variations: List[str]) -> Any:
        """
        Search for field value in cache data using multiple JSON paths
        
        Args:
            cache_data: Parsed gdpClientCache data
            field_variations: List of field name variations to search for
        
        Returns:
            First non-empty value found or None
        """
        # Common JSON paths to search
        search_paths = [
            'property',
            'listing',
            'address',
            'resoFacts',
            'propertyDetails',
            'listingDetails',
            'propertyInfo'
        ]
        
        for path in search_paths:
            if path in cache_data:
                section = cache_data[path]
                if isinstance(section, dict):
                    for variation in field_variations:
                        if variation in section:
                            value = section[variation]
                            if value is not None and value != "" and value != []:
                                return value
        
        # Search recursively in nested structures
        return self.search_recursive_json(cache_data, field_variations)

    def search_recursive_json(self, data: Any, field_variations: List[str], max_depth: int = 5, current_depth: int = 0) -> Any:
        """
        Recursively search for field value in nested JSON structures
        
        Args:
            data: Data to search in
            field_variations: List of field name variations to search for
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
        
        Returns:
            First non-empty value found or None
        """
        if current_depth >= max_depth:
            return None
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Check if key matches any field variation
                if any(variation.lower() in key.lower() or key.lower() in variation.lower() for variation in field_variations):
                    if value is not None and value != "" and value != []:
                        return value
                
                # Recursively search nested structures
                if isinstance(value, (dict, list)):
                    result = self.search_recursive_json(value, field_variations, max_depth, current_depth + 1)
                    if result is not None:
                        return result
        
        elif isinstance(data, list):
            for item in data:
                result = self.search_recursive_json(item, field_variations, max_depth, current_depth + 1)
                if result is not None:
                    return result
        
        return None

    def search_regex_in_text(self, text: str, field_variations: List[str], field_name: str) -> Any:
        """
        Search for field value in text using regex patterns
        
        Args:
            text: Text to search in
            field_variations: List of field name variations to search for
            field_name: Base field name for pattern generation
        
        Returns:
            First non-empty value found or None
        """
        # Generate regex patterns for the field
        patterns = self.generate_regex_patterns_for_field(field_name, field_variations)
        
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Filter out empty matches and take first non-empty
                    for match in matches:
                        if isinstance(match, tuple):
                            # Handle multiple capture groups
                            for group in match:
                                if group and group.strip() and group.lower() not in ['null', 'undefined', '']:
                                    return group.strip()
                        else:
                            # Single match
                            if match and match.strip() and match.lower() not in ['null', 'undefined', '']:
                                return match.strip()
            except re.error:
                continue
        
        return None

    def generate_regex_patterns_for_field(self, field_name: str, field_variations: List[str]) -> List[str]:
        """
        Generate regex patterns for field extraction
        
        Args:
            field_name: Base field name
            field_variations: List of field name variations
        
        Returns:
            List of regex patterns to try
        """
        patterns = []
        
        for variation in field_variations:
            # Pattern 1: "fieldName": "value" (with quotes)
            patterns.append(f'"{re.escape(variation)}"\\s*:\\s*"([^"]+)"')
            
            # Pattern 2: "fieldName": value (without quotes)
            patterns.append(f'"{re.escape(variation)}"\\s*:\\s*([^,\\s\\}}]+)')
            
            # Pattern 3: fieldName: "value" (without quotes around field name)
            patterns.append(f'{re.escape(variation)}\\s*:\\s*"([^"]+)"')
            
            # Pattern 4: fieldName: value (without quotes)
            patterns.append(f'{re.escape(variation)}\\s*:\\s*([^,\\s\\}}]+)')
            
            # Pattern 5: Partial name matching (for multi-word fields)
            if ' ' in variation or '_' in variation:
                words = variation.replace('_', ' ').split()
                if len(words) > 1:
                    # Look for partial matches with word boundaries
                    partial_pattern = f'\\b({"|".join(words)})\\b.*?\\b({"|".join(words)})\\b'
                    patterns.append(partial_pattern)
        
        return patterns

    def store_property_to_database(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store extracted property data directly to PostgreSQL database with timeout
        Returns: {'success': bool, 'action': 'insert'|'update'|'no_change', 'zpid': str, 'details': str}
        """
        if not self.enable_db_storage or not self.db_engine:
            logger.warning("Database storage not enabled")
            return {'success': False, 'action': 'error', 'zpid': '', 'details': 'Database storage not enabled'}
        
        try:
            zpid = str(property_data.get('zpid', ''))
            if not zpid:
                logger.warning("No ZPID found in property data")
                return False
            
            # Set a timeout for database operations
            start_time = time.time()
            
            with self.db_engine.begin() as conn:
                # Store to listings_summary
                addr = property_data.get('address', {})
                url = property_data.get('url')
                full_url = f"https://www.zillow.com{url}" if url and not str(url).startswith('http') else url
                
                # First check if property exists and what data we have
                existing_data = None
                try:
                    result = conn.execute(text("SELECT * FROM listings_summary WHERE zpid = :zpid"), {'zpid': zpid})
                    existing_data = result.fetchone()
                except Exception as e:
                    logger.warning(f"Could not check existing data for {zpid}: {e}")
                
                # Check if data actually changed
                data_changed = False
                if existing_data:
                    # Get column names from the result
                    columns = result.keys()
                    # Compare key fields to see if anything meaningful changed
                    key_fields = ['price', 'beds', 'baths', 'home_size_sqft', 'home_status', 'days_on_zillow']
                    for field in key_fields:
                        if field in columns:
                            field_index = list(columns).index(field)
                            if existing_data[field_index] != property_data.get(field):
                                data_changed = True
                                break
                
                # Upsert summary
                conn.execute(text('''
                    INSERT INTO listings_summary (zpid, price, beds, baths, home_size_sqft, address, city, state, zip_code, url,
                                                latitude, longitude, zestimate, rent_zestimate, monthly_hoa_fee, days_on_zillow,
                                                page_view_count, favorite_count, home_status, listing_provider, mls_id, mls_name,
                                                lot_area_value, lot_area_units, home_type, property_type_dimension)
                    VALUES (:zpid, :price, :beds, :baths, :home_size_sqft, :address, :city, :state, :zip_code, :url,
                           :latitude, :longitude, :zestimate, :rent_zestimate, :monthly_hoa_fee, :days_on_zillow,
                           :page_view_count, :favorite_count, :home_status, :listing_provider, :mls_id, :mls_name,
                           :lot_area_value, :lot_area_units, :home_type, :property_type_dimension)
                    ON CONFLICT (zpid) DO UPDATE SET
                        price = EXCLUDED.price, beds = EXCLUDED.beds, baths = EXCLUDED.baths,
                        home_size_sqft = EXCLUDED.home_size_sqft, address = EXCLUDED.address,
                        city = EXCLUDED.city, state = EXCLUDED.state, zip_code = EXCLUDED.zip_code,
                        url = EXCLUDED.url, latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude,
                        zestimate = EXCLUDED.zestimate, rent_zestimate = EXCLUDED.rent_zestimate,
                        monthly_hoa_fee = EXCLUDED.monthly_hoa_fee, days_on_zillow = EXCLUDED.days_on_zillow,
                        page_view_count = EXCLUDED.page_view_count, favorite_count = EXCLUDED.favorite_count,
                        home_status = EXCLUDED.home_status, listing_provider = EXCLUDED.listing_provider,
                        mls_id = EXCLUDED.mls_id, mls_name = EXCLUDED.mls_name,
                        lot_area_value = EXCLUDED.lot_area_value, lot_area_units = EXCLUDED.lot_area_units,
                        home_type = EXCLUDED.home_type, property_type_dimension = EXCLUDED.property_type_dimension
                '''), {
                    'zpid': zpid,
                    'price': property_data.get('price'),
                    'beds': property_data.get('bedrooms'),
                    'baths': property_data.get('bathrooms'),
                    'home_size_sqft': property_data.get('livingArea'),
                    'address': ', '.join([addr.get('streetAddress',''), addr.get('city',''), addr.get('state','')]).strip(', '),
                    'city': addr.get('city'),
                    'state': addr.get('state'),
                    'zip_code': addr.get('zipcode'),
                    'url': full_url,
                    'latitude': property_data.get('latitude') or property_data.get('coord_latitude'),
                    'longitude': property_data.get('longitude') or property_data.get('coord_longitude'),
                    'zestimate': self._safe_convert_for_db(property_data.get('zestimate')),
                    'rent_zestimate': self._safe_convert_rent_zestimate(property_data.get('rent_zestimate')),
                    'monthly_hoa_fee': self._safe_convert_for_db(property_data.get('monthly_hoa_fee')),
                    'days_on_zillow': property_data.get('days_on_zillow'),
                    'page_view_count': property_data.get('page_view_count'),
                    'favorite_count': property_data.get('favorite_count'),
                    'home_status': property_data.get('home_status'),
                    'listing_provider': self._safe_convert_for_db(property_data.get('listing_provider')),
                    'mls_id': self._safe_convert_for_db(property_data.get('mlsID') or property_data.get('extracted_mls_id')),
                    'mls_name': self._safe_convert_for_db(property_data.get('mlsNname') or property_data.get('extracted_mls_name')),
                    'lot_area_value': property_data.get('lot_area_value'),
                    'lot_area_units': property_data.get('lot_area_units'),
                    'home_type': property_data.get('home_type'),
                    'property_type_dimension': property_data.get('property_type_dimension')
                })
                
                # Check timeout
                if time.time() - start_time > self.timeout_seconds:
                    logger.warning(f"⚠️ Database storage taking too long for {zpid}, continuing...")
                    return False
                
                # Store to listings_detail
                desc_preview = (property_data.get('description', '')[:200] if property_data.get('description') else None)
                desc_raw = property_data.get('description')  # Full description for description_raw column
                waterfront_features = property_data.get('extracted_waterfront_features')
                water_view = property_data.get('extracted_water_view')
                on_market_date = property_data.get('extracted_on_market_date')
                ownership_type = property_data.get('extracted_ownership_type')
                parcel_number = property_data.get('extracted_parcel_number')
                living_area = property_data.get('extracted_living_area') or property_data.get('livingArea')
                rooms = property_data.get('extracted_rooms')
                view = property_data.get('extracted_view')
                price_per_sqft = property_data.get('extracted_price_per_sqft')
                
                # Convert Unix timestamp to datetime if needed
                if on_market_date and isinstance(on_market_date, (int, float)):
                    try:
                        from datetime import datetime
                        on_market_date = datetime.fromtimestamp(on_market_date / 1000)  # Convert from milliseconds
                    except (ValueError, OSError):
                        on_market_date = None
                
                # Determine waterfront features
                boat_access = bool(property_data.get('waterfront_keywords') and 
                                 any(t in ' '.join(property_data['waterfront_keywords']).lower() 
                                     for t in ['dock', 'boat', 'marina']))
                
                # Clean up data types for database storage using safe conversion
                waterfront_features_clean = self._safe_convert_for_db(waterfront_features)
                water_view_clean = self._safe_convert_for_db(water_view)
                rooms_clean = self._safe_convert_for_db(rooms)
                view_clean = self._safe_convert_for_db(view)
                dock_info_clean = self._safe_convert_for_db(property_data.get('regex_dock_info'))
                bridge_height_clean = self._safe_convert_for_db(property_data.get('regex_bridge_height'))
                water_depth_clean = self._safe_convert_for_db(property_data.get('regex_water_depth'))
                
                # Store additional fields to listing_text_content
                additional_fields_to_store = {
                    'title': property_data.get('title'),
                    'lot_size_acres': property_data.get('lot_size_acres'),
                    'property_subtype': property_data.get('property_subtype'),
                    'mls_number': property_data.get('mls_number'),
                    'listing_agent': property_data.get('listing_agent'),
                    'listing_office': property_data.get('listing_office'),
                    'price_history': property_data.get('price_history'),
                    'tax_history': property_data.get('tax_history'),
                    'tax_annual_amount': property_data.get('tax_annual_amount'),
                    'tax_assessed_value': property_data.get('tax_assessed_value'),
                    'schools': property_data.get('schools'),
                    'parking_info': property_data.get('parking_info'),
                    'additional_features': property_data.get('additional_features'),
                    'community_info': property_data.get('community_info'),
                    'listing_details': property_data.get('listing_details'),
                    'extracted_lot_features': property_data.get('extracted_lot_features'),
                    'extracted_exterior_features': property_data.get('extracted_exterior_features'),
                    'extracted_interior_features': property_data.get('extracted_interior_features'),
                    'extracted_appliances': property_data.get('extracted_appliances'),
                    'extracted_heating': property_data.get('extracted_heating'),
                    'extracted_cooling': property_data.get('extracted_cooling'),
                    'extracted_parking_features': property_data.get('extracted_parking_features'),
                    'extracted_security_features': property_data.get('extracted_security_features'),
                    'extracted_community_features': property_data.get('extracted_community_features')
                }
                
                # Store additional comprehensive fields
                for field_name, field_value in additional_fields_to_store.items():
                    if field_value is not None:
                        content_preview = str(field_value)[:200] if field_value else None
                        conn.execute(text('''
                            INSERT INTO listing_text_content (zpid, content_type, content_full, content_preview)
                            VALUES (:zpid, :content_type, :content_full, :content_preview)
                            ON CONFLICT (zpid, content_type) DO UPDATE SET
                                content_full = EXCLUDED.content_full,
                                content_preview = EXCLUDED.content_preview
                        '''), {
                            'zpid': zpid,
                            'content_type': field_name,
                            'content_full': json.dumps(field_value) if isinstance(field_value, (dict, list)) else str(field_value),
                            'content_preview': content_preview
                        })
                
                # Store enhanced waterfront information
                enhanced_waterfront_fields = {
                    'waterfront_type': property_data.get('waterfront_type'),
                    'canal_info': property_data.get('regex_canal_info'),
                    'ocean_access': property_data.get('regex_ocean_access'),
                    'enhanced_dock_info': property_data.get('regex_dock_info'),
                    'enhanced_bridge_height': property_data.get('regex_bridge_height'),
                    'enhanced_water_depth': property_data.get('regex_water_depth')
                }
                
                for field_name, field_value in enhanced_waterfront_fields.items():
                    if field_value is not None:
                        content_preview = str(field_value)[:200] if field_value else None
                        conn.execute(text('''
                            INSERT INTO listing_text_content (zpid, content_type, content_full, content_preview)
                            VALUES (:zpid, :content_type, :content_full, :content_preview)
                            ON CONFLICT (zpid, content_type) DO UPDATE SET
                                content_full = EXCLUDED.content_full,
                                content_preview = EXCLUDED.content_preview
                        '''), {
                            'zpid': zpid,
                            'content_type': field_name,
                            'content_full': json.dumps(field_value) if isinstance(field_value, (dict, list)) else str(field_value),
                            'content_preview': content_preview
                        })
                
                # Upsert details with description_raw
                conn.execute(text('''
                    INSERT INTO listings_detail (zpid, description_raw, waterfront_features, water_view,
                                               on_market_date, ownership_type, parcel_number, living_area,
                                               living_area_value, living_area_units, rooms, view, price_per_sqft,
                                               boat_access, dock_info, bridge_height, water_depth)
                    VALUES (:zpid, :description_raw, :waterfront_features, :water_view,
                           :on_market_date, :ownership_type, :parcel_number, :living_area,
                           :living_area_value, :living_area_units, :rooms, :view, :price_per_sqft,
                           :boat_access, :dock_info, :bridge_height, :water_depth)
                    ON CONFLICT (zpid) DO UPDATE SET
                        description_raw = EXCLUDED.description_raw,
                        waterfront_features = EXCLUDED.waterfront_features,
                        water_view = EXCLUDED.water_view,
                        on_market_date = EXCLUDED.on_market_date,
                        ownership_type = EXCLUDED.ownership_type,
                        parcel_number = EXCLUDED.parcel_number,
                        living_area = EXCLUDED.living_area,
                        living_area_value = EXCLUDED.living_area_value,
                        living_area_units = EXCLUDED.living_area_units,
                        rooms = EXCLUDED.rooms,
                        view = EXCLUDED.view,
                        price_per_sqft = EXCLUDED.price_per_sqft,
                        boat_access = EXCLUDED.boat_access,
                        dock_info = EXCLUDED.dock_info,
                        bridge_height = EXCLUDED.bridge_height,
                        water_depth = EXCLUDED.water_depth
                '''), {
                    'zpid': zpid,
                    'description_raw': desc_raw,
                    'waterfront_features': waterfront_features_clean,
                    'water_view': water_view_clean,
                    'on_market_date': on_market_date,
                    'ownership_type': ownership_type,
                    'parcel_number': parcel_number,
                    'living_area': str(living_area) if living_area else None,
                    'living_area_value': living_area,
                    'living_area_units': 'sqft' if living_area else None,
                    'rooms': rooms_clean,
                    'view': view_clean,
                    'price_per_sqft': str(price_per_sqft) if price_per_sqft else None,
                    'boat_access': boat_access,
                    'dock_info': dock_info_clean,
                    'bridge_height': bridge_height_clean,
                    'water_depth': water_depth_clean
                })
                
                # Check timeout again
                if time.time() - start_time > self.timeout_seconds:
                    logger.warning(f"⚠️ Database storage taking too long for {zpid}, continuing...")
                    return False
                
                # Store photos (limit to prevent hanging)
                photos = property_data.get('photos', [])
                if photos:
                    # Delete existing photos for this property
                    conn.execute(text('DELETE FROM property_photos WHERE zpid = :zpid'), {'zpid': zpid})
                    
                    # Limit photos to prevent hanging
                    max_photos = min(len(photos), 10)
                    for i, photo in enumerate(photos[:max_photos]):
                        mixed_sources = photo.get('mixedSources', {})
                        jpeg_urls = mixed_sources.get('jpeg', [])
                        webp_urls = mixed_sources.get('webp', [])
                        main_url = jpeg_urls[0].get('url', '') if jpeg_urls else ''
                        
                        conn.execute(text('''
                            INSERT INTO property_photos (zpid, caption, main_url, jpeg_resolutions, webp_resolutions, photo_order)
                            VALUES (:zpid, :caption, :main_url, :jpeg_resolutions, :webp_resolutions, :photo_order)
                        '''), {
                            'zpid': zpid,
                            'caption': photo.get('caption', ''),
                            'main_url': main_url,
                            'jpeg_resolutions': json.dumps(jpeg_urls),
                            'webp_resolutions': json.dumps(webp_urls),
                            'photo_order': i
                        })
                        
                        # Check timeout during photo processing
                        if time.time() - start_time > self.timeout_seconds:
                            logger.warning(f"⚠️ Photo processing taking too long for {zpid}, stopping...")
                            break
                
                # Store text content (limit size to prevent hanging)
                if property_data.get('description'):
                    desc_content = property_data['description'][:10000]  # Limit description size
                    conn.execute(text('''
                        INSERT INTO listing_text_content (zpid, content_type, content_full, content_preview)
                        VALUES (:zpid, :content_type, :content_full, :content_preview)
                        ON CONFLICT (zpid, content_type) DO UPDATE SET
                            content_full = EXCLUDED.content_full,
                            content_preview = EXCLUDED.content_preview
                    '''), {
                        'zpid': zpid,
                        'content_type': 'description',
                        'content_full': desc_content,
                        'content_preview': desc_content[:500]
                    })
                
                if property_data.get('waterfront_keywords'):
                    conn.execute(text('''
                        INSERT INTO listing_text_content (zpid, content_type, content_full, content_preview)
                        VALUES (:zpid, :content_type, :content_full, :content_preview)
                        ON CONFLICT (zpid, content_type) DO UPDATE SET
                            content_full = EXCLUDED.content_full,
                            content_preview = EXCLUDED.content_preview
                    '''), {
                        'zpid': zpid,
                        'content_type': 'waterfront_keywords',
                        'content_full': json.dumps(property_data['waterfront_keywords']),
                        'content_preview': ', '.join(property_data['waterfront_keywords'][:3])
                    })
                
                # Store extracted fields as reso_facts (limit size)
                extracted_fields = {k: v for k, v in property_data.items() if k.startswith('extracted_') and v is not None}
                if extracted_fields:
                    # Limit the size of extracted fields to prevent hanging
                    limited_fields = dict(list(extracted_fields.items())[:20])  # Max 20 fields
                    conn.execute(text('''
                        INSERT INTO listing_text_content (zpid, content_type, content_full, content_preview)
                        VALUES (:zpid, :content_type, :content_full, :content_preview)
                        ON CONFLICT (zpid, content_type) DO UPDATE SET
                            content_full = EXCLUDED.content_full,
                            content_preview = EXCLUDED.content_preview
                    '''), {
                        'zpid': zpid,
                        'content_type': 'reso_facts',
                        'content_full': json.dumps(limited_fields),
                        'content_preview': ', '.join([f"{k}: {v}" for k, v in list(limited_fields.items())[:5]])
                    })
                
                # Store additional comprehensive fields
                for field_name, field_value in additional_fields_to_store.items():
                    if field_value is not None:
                        content_preview = str(field_value)[:200] if field_value else None
                        conn.execute(text('''
                            INSERT INTO listing_text_content (zpid, content_type, content_full, content_preview)
                            VALUES (:zpid, :content_type, :content_full, :content_preview)
                            ON CONFLICT (zpid, content_type) DO UPDATE SET
                                content_full = EXCLUDED.content_full,
                                content_preview = EXCLUDED.content_preview
                        '''), {
                            'zpid': zpid,
                            'content_type': field_name,
                            'content_full': json.dumps(field_value) if isinstance(field_value, (dict, list)) else str(field_value),
                            'content_preview': content_preview
                        })
            
            db_time = time.time() - start_time
            logger.info(f"✅ Successfully stored property {zpid} to database in {db_time:.2f}s")
            
            # Mark successful database storage in field tracker
            if hasattr(self, 'field_tracker') and self.field_tracker:
                # Find the property in the tracker and mark it as stored
                for prop_data in self.field_tracker.get('properties_processed', []):
                    if prop_data.get('zpid') == zpid:
                        prop_data['_database_stored'] = True
                        break
            
            # Determine what action was taken
            if not existing_data:
                action = 'insert'
                details = f"New property {zpid} inserted successfully"
                logger.info(f"✅ New property {zpid} inserted to database")
                self._update_counter('properties_added')
            elif data_changed:
                action = 'update'
                details = f"Property {zpid} updated with new data"
                logger.info(f"🔄 Property {zpid} updated in database (data changed)")
                self._update_counter('properties_updated')
            else:
                action = 'no_change'
                details = f"Property {zpid} already exists with same data - no changes made"
                logger.warning(f"⚠️ WASTED SCRAPE: Property {zpid} already exists with identical data")
            
            return {
                'success': True,
                'action': action,
                'zpid': zpid,
                'details': details,
                'data_changed': data_changed
            }
            
        except Exception as e:
            logger.error(f"❌ Error storing property to database: {e}")
            return {
                'success': False,
                'action': 'error',
                'zpid': zpid,
                'details': f"Database error: {e}",
                'data_changed': False
            }
    
    def extract_property_data_flexible(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract property data using multiple flexible strategies"""
        property_data = {}
        
        # Find the main property object
        property_obj = None
        for key, value in cache_data.items():
            if isinstance(value, dict) and 'property' in value:
                property_obj = value['property']
                break
        
        if not property_obj:
            logger.warning("No property object found in cache data")
            return {}
        
        # Basic property info
        property_data['zpid'] = property_obj.get('zpid')
        property_data['url'] = property_obj.get('url') or property_obj.get('hdpUrl') or f"https://www.zillow.com/homedetails/{property_obj.get('zpid')}_zpid/"
        
        # Address information
        address = property_obj.get('address', {})
        property_data['address'] = address
        property_data['city'] = address.get('city')
        property_data['state'] = address.get('state')
        property_data['zip_code'] = address.get('zipcode')
        
        # Basic property details - use flexible extraction for better coverage
        property_data['price'] = property_obj.get('price')
        property_data['bedrooms'] = property_obj.get('bedrooms')
        property_data['bathrooms'] = property_obj.get('bathrooms')
        property_data['livingArea'] = property_obj.get('livingArea')
        
        # Enhanced property details
        property_data['title'] = property_obj.get('title') or f"{address.get('streetAddress', '')} {address.get('city', '')} {address.get('state', '')}"
        property_data['property_subtype'] = property_obj.get('propertySubType', [])
        property_data['home_type'] = property_obj.get('homeType')
        property_data['property_type_dimension'] = property_obj.get('propertyTypeDimension')
        
        # Lot and size information
        property_data['lot_size'] = property_obj.get('lotSize')
        property_data['lot_size_acres'] = property_obj.get('lotSizeAcres')
        property_data['lot_area_value'] = property_obj.get('lotAreaValue')
        property_data['lot_area_units'] = property_obj.get('lotAreaUnits')
        
        # MLS and listing information
        property_data['mls_id'] = property_obj.get('mlsId')
        property_data['mls_name'] = property_obj.get('mlsName')
        property_data['mls_number'] = property_obj.get('mlsNumber')
        
        # Listing agent and office
        attribution = property_obj.get('attributionInfo', {})
        property_data['listing_agent'] = attribution.get('agentName')
        property_data['listing_office'] = attribution.get('brokerName')
        property_data['listing_agent_phone'] = attribution.get('agentPhoneNumber')
        
        # Property status and type
        property_data['home_status'] = property_obj.get('homeStatus')
        property_data['contingent_type'] = property_obj.get('contingentListingType')
        property_data['listing_provider'] = property_obj.get('listingProvider')
        property_data['is_condo'] = property_obj.get('homeType') == 'CONDO'
        property_data['is_waterfront'] = bool(property_obj.get('waterfrontFeatures'))
        property_data['water_type'] = property_obj.get('waterBodyName')
        
        # Coordinates
        property_data['latitude'] = property_obj.get('latitude')
        property_data['longitude'] = property_obj.get('longitude')
        
        # Zestimate and financial info
        property_data['zestimate'] = property_obj.get('zestimate')
        rent_zest_raw = property_obj.get('rentZestimate')
        logger.info(f"🔍 Raw rentZestimate for {property_data.get('zpid')}: {rent_zest_raw} (type: {type(rent_zest_raw)})")
        property_data['rent_zestimate'] = rent_zest_raw
        
        # HOA fee - use monthlyHoaFee and handle boolean cases
        monthly_hoa = property_obj.get('monthlyHoaFee')
        if monthly_hoa is not None and monthly_hoa is not False and isinstance(monthly_hoa, (int, float)):
            property_data['monthly_hoa_fee'] = int(monthly_hoa)
        else:
            property_data['monthly_hoa_fee'] = None
        
        # Market information
        property_data['days_on_zillow'] = property_obj.get('daysOnZillow')
        property_data['page_view_count'] = property_obj.get('pageViewCount')
        property_data['favorite_count'] = property_obj.get('favoriteCount')
        
        # Enhanced extracted fields - prioritize resoFacts extraction
        reso_facts = property_obj.get('resoFacts', {})
        if isinstance(reso_facts, dict):
            # Extract all available fields from resoFacts first
            property_data['extracted_waterfront_features'] = reso_facts.get('waterfrontFeatures')
            property_data['extracted_water_view'] = reso_facts.get('waterView')
            property_data['extracted_on_market_date'] = reso_facts.get('onMarketDate')
            property_data['extracted_ownership_type'] = reso_facts.get('ownershipType')
            property_data['extracted_parcel_number'] = reso_facts.get('parcelNumber')
            property_data['extracted_living_area'] = reso_facts.get('livingArea')
            property_data['extracted_rooms'] = reso_facts.get('rooms')
            property_data['extracted_view'] = reso_facts.get('view')
            property_data['extracted_price_per_sqft'] = reso_facts.get('pricePerSquareFoot')
            property_data['extracted_year_built'] = reso_facts.get('yearBuilt')
            property_data['extracted_property_subtype'] = reso_facts.get('propertySubType')
            property_data['extracted_lot_size'] = reso_facts.get('lotSize')
            property_data['extracted_lot_size_acres'] = reso_facts.get('lotSizeAcres')
            property_data['extracted_mls_id'] = reso_facts.get('mlsId')
            property_data['extracted_mls_name'] = reso_facts.get('mlsName')
            property_data['extracted_mls_number'] = reso_facts.get('mlsNumber')
            property_data['extracted_contingent_type'] = reso_facts.get('contingentListingType')
            property_data['extracted_listing_provider'] = reso_facts.get('listingProvider')
            property_data['extracted_water_body_name'] = reso_facts.get('waterBodyName')
            property_data['extracted_hoa_fee'] = reso_facts.get('hoaFee')
            property_data['extracted_tax_annual_amount'] = reso_facts.get('taxAnnualAmount')
            property_data['extracted_tax_assessed_value'] = reso_facts.get('taxAssessedValue')
            
            # Additional resoFacts fields
            property_data['extracted_lot_features'] = reso_facts.get('lotFeatures')
            property_data['extracted_exterior_features'] = reso_facts.get('exteriorFeatures')
            property_data['extracted_interior_features'] = reso_facts.get('interiorFeatures')
            property_data['extracted_appliances'] = reso_facts.get('appliances')
            property_data['extracted_heating'] = reso_facts.get('heating')
            property_data['extracted_cooling'] = reso_facts.get('cooling')
            property_data['extracted_parking_features'] = reso_facts.get('parkingFeatures')
            property_data['extracted_security_features'] = reso_facts.get('securityFeatures')
            property_data['extracted_community_features'] = reso_facts.get('communityFeatures')
            
            # Debug logging for resoFacts extraction
            logger.info(f"🔍 resoFacts extraction for {property_data.get('zpid')}:")
            logger.info(f"  ✅ yearBuilt: {property_data.get('extracted_year_built')}")
            logger.info(f"  ✅ propertySubType: {property_data.get('extracted_property_subtype')}")
            logger.info(f"  ✅ lotSize: {property_data.get('extracted_lot_size')}")
            logger.info(f"  ✅ pricePerSquareFoot: {property_data.get('extracted_price_per_sqft')}")
            logger.info(f"  ✅ rooms: {property_data.get('extracted_rooms')}")
            logger.info(f"  ✅ waterfrontFeatures: {property_data.get('extracted_waterfront_features')}")
            logger.info(f"  ✅ waterView: {property_data.get('extracted_water_view')}")
            logger.info(f"  ✅ onMarketDate: {property_data.get('extracted_on_market_date')}")
            logger.info(f"  ✅ ownershipType: {property_data.get('extracted_ownership_type')}")
            logger.info(f"  ✅ parcelNumber: {property_data.get('extracted_parcel_number')}")
            logger.info(f"  ✅ mlsId: {property_data.get('extracted_mls_id')}")
            logger.info(f"  ✅ mlsName: {property_data.get('extracted_mls_name')}")
            logger.info(f"  ✅ mlsNumber: {property_data.get('extracted_mls_number')}")
            logger.info(f"  ✅ contingentListingType: {property_data.get('extracted_contingent_type')}")
            logger.info(f"  ✅ listingProvider: {property_data.get('extracted_listing_provider')}")
            logger.info(f"  ✅ waterBodyName: {property_data.get('extracted_water_body_name')}")
            logger.info(f"  ✅ hoaFee: {property_data.get('extracted_hoa_fee')}")
            logger.info(f"  ✅ taxAnnualAmount: {property_data.get('extracted_tax_annual_amount')}")
            logger.info(f"  ✅ taxAssessedValue: {property_data.get('extracted_tax_assessed_value')}")
            
        elif isinstance(reso_facts, list):
            # Extract from resoFacts list format
            for fact in reso_facts:
                if isinstance(fact, dict):
                    label = fact.get('factLabel', '').lower()
                    value = fact.get('factValue')
                    if 'waterfront' in label:
                        property_data['extracted_waterfront_features'] = value
                    elif 'water view' in label:
                        property_data['extracted_water_view'] = value
                    elif 'on market' in label:
                        property_data['extracted_on_market_date'] = value
                    elif 'ownership' in label:
                        property_data['extracted_ownership_type'] = value
                    elif 'parcel' in label:
                        property_data['extracted_parcel_number'] = value
                    elif 'living area' in label:
                        property_data['extracted_living_area'] = value
                    elif 'rooms' in label:
                        property_data['extracted_rooms'] = value
                    elif 'view' in label:
                        property_data['extracted_view'] = value
                    elif 'price/sqft' in label:
                        property_data['extracted_price_per_sqft'] = value
                    elif 'year built' in label:
                        property_data['extracted_year_built'] = value
                    elif 'property type' in label:
                        property_data['extracted_property_subtype'] = value
                    elif 'lot size' in label:
                        property_data['extracted_lot_size'] = value
                    elif 'mls' in label:
                        if 'id' in label:
                            property_data['extracted_mls_id'] = value
                        elif 'name' in label:
                            property_data['extracted_mls_name'] = value
                        elif 'number' in label:
                            property_data['extracted_mls_number'] = value
                    elif 'contingent' in label:
                        property_data['extracted_contingent_type'] = value
                    elif 'listing provider' in label:
                        property_data['extracted_listing_provider'] = value
                    elif 'water body' in label:
                        property_data['extracted_water_body_name'] = value
                    elif 'hoa' in label:
                        property_data['extracted_hoa_fee'] = value
                    elif 'tax' in label:
                        if 'annual' in label:
                            property_data['extracted_tax_annual_amount'] = value
                        elif 'assessed' in label:
                            property_data['extracted_tax_assessed_value'] = value
        
        # Apply fallback logic for fields not found in resoFacts
        # Basic property details with fallbacks
        property_data['year_built'] = (
            property_data.get('extracted_year_built') if property_data.get('extracted_year_built') is not None else
            property_obj.get('yearBuilt') or 
            property_data.get('year_built')
        )
        
        property_data['property_subtype'] = (
            property_data.get('extracted_property_subtype') if property_data.get('extracted_property_subtype') is not None else
            property_obj.get('propertySubType') or 
            property_data.get('property_subtype')
        )
        
        property_data['lot_size'] = (
            property_data.get('extracted_lot_size') if property_data.get('extracted_lot_size') is not None else
            property_obj.get('lotSize') or 
            property_data.get('lot_size')
        )
        
        property_data['lot_size_acres'] = (
            property_data.get('extracted_lot_size_acres') if property_data.get('extracted_lot_size_acres') is not None else
            property_obj.get('lotSizeAcres') or 
            property_data.get('lot_size_acres')
        )
        
        # MLS information with fallbacks
        property_data['mls_id'] = (
            property_data.get('extracted_mls_id') if property_data.get('extracted_mls_id') is not None else
            property_obj.get('mlsId') or 
            property_data.get('mls_id')
        )
        
        property_data['mls_name'] = (
            property_data.get('extracted_mls_name') if property_data.get('extracted_mls_name') is not None else
            property_obj.get('mlsName') or 
            property_data.get('mls_name')
        )
        
        property_data['mls_number'] = (
            property_data.get('extracted_mls_number') if property_data.get('extracted_mls_number') is not None else
            property_obj.get('mlsNumber') or 
            property_data.get('mls_number')
        )
        
        # Property status with fallbacks
        property_data['contingent_type'] = (
            property_data.get('extracted_contingent_type') if property_data.get('extracted_contingent_type') is not None else
            property_obj.get('contingentListingType') or 
            property_data.get('contingent_type')
        )
        
        property_data['listing_provider'] = (
            property_data.get('extracted_listing_provider') if property_data.get('extracted_listing_provider') is not None else
            property_obj.get('listingProvider') or 
            property_data.get('listing_provider')
        )
        
        # Waterfront features with fallbacks
        property_data['water_body_name'] = (
            property_data.get('extracted_water_body_name') if property_data.get('extracted_water_body_name') is not None else
            property_obj.get('waterBodyName') or 
            property_data.get('water_body_name')
        )
        
        # Financial data with fallbacks
        property_data['hoa_fee'] = (
            property_data.get('extracted_hoa_fee') if property_data.get('extracted_hoa_fee') is not None else
            property_obj.get('hoaFee') or 
            property_data.get('hoa_fee')
        )
        
        property_data['tax_annual_amount'] = (
            property_data.get('extracted_tax_annual_amount') if property_data.get('extracted_tax_annual_amount') is not None else
            property_obj.get('taxAnnualAmount') or 
            property_data.get('tax_annual_amount')
        )
        
        property_data['tax_assessed_value'] = (
            property_data.get('extracted_tax_assessed_value') if property_data.get('extracted_tax_assessed_value') is not None else
            property_obj.get('taxAssessedValue') or 
            property_data.get('tax_assessed_value')
        )
        
        # Enhanced waterfront features extraction
        property_data['waterfront_features'] = (
            property_data.get('extracted_waterfront_features') if property_data.get('extracted_waterfront_features') is not None else
            property_obj.get('waterfrontFeatures') or 
            property_data.get('waterfront_features')
        )
        
        property_data['water_view'] = (
            property_data.get('extracted_water_view') if property_data.get('extracted_water_view') is not None else
            property_obj.get('waterView') or 
            property_data.get('water_view')
        )
        
        property_data['view'] = (
            property_data.get('extracted_view') if property_data.get('extracted_view') is not None else
            property_obj.get('view') or 
            property_data.get('view')
        )
        
        property_data['rooms'] = (
            property_data.get('extracted_rooms') if property_data.get('extracted_rooms') is not None else
            property_obj.get('rooms') or 
            property_data.get('rooms')
        )
        
        property_data['price_per_sqft'] = (
            property_data.get('extracted_price_per_sqft') if property_data.get('extracted_price_per_sqft') is not None else
            property_obj.get('pricePerSquareFoot') or 
            property_data.get('price_per_sqft')
        )
        
        property_data['on_market_date'] = (
            property_data.get('extracted_on_market_date') if property_data.get('extracted_on_market_date') is not None else
            property_obj.get('onMarketDate') or 
            property_obj.get('comingSoonOnMarketDate') or 
            property_data.get('on_market_date')
        )
        
        property_data['ownership_type'] = (
            property_data.get('extracted_ownership_type') if property_data.get('extracted_ownership_type') is not None else
            property_obj.get('ownershipType') or 
            property_data.get('ownership_type')
        )
        
        property_data['parcel_number'] = (
            property_data.get('extracted_parcel_number') if property_data.get('extracted_parcel_number') is not None else
            property_obj.get('parcelNumber') or 
            property_data.get('parcel_number')
        )
        
        # Debug logging for final field values
        logger.info(f"🔍 Final field values for {property_data.get('zpid')}:")
        logger.info(f"  ✅ year_built: {property_data.get('year_built')}")
        logger.info(f"  ✅ property_subtype: {property_data.get('property_subtype')}")
        logger.info(f"  ✅ lot_size: {property_data.get('lot_size')}")
        logger.info(f"  ✅ lot_size_acres: {property_data.get('lot_size_acres')}")
        logger.info(f"  ✅ mls_id: {property_data.get('mlsID')}")
        logger.info(f"  ✅ mls_name: {property_data.get('mlsName')}")
        logger.info(f"  ✅ mls_number: {property_data.get('mls_number')}")
        logger.info(f"  ✅ contingent_type: {property_data.get('contingent_type')}")
        logger.info(f"  ✅ listing_provider: {property_data.get('listing_provider')}")
        logger.info(f"  ✅ water_body_name: {property_data.get('water_body_name')}")
        logger.info(f"  ✅ hoa_fee: {property_data.get('hoa_fee')}")
        logger.info(f"  ✅ tax_annual_amount: {property_data.get('tax_annual_amount')}")
        logger.info(f"  ✅ tax_assessed_value: {property_data.get('tax_assessed_value')}")
        logger.info(f"  ✅ waterfront_features: {property_data.get('waterfront_features')}")
        logger.info(f"  ✅ water_view: {property_data.get('water_view')}")
        logger.info(f"  ✅ view: {property_data.get('view')}")
        logger.info(f"  ✅ rooms: {property_data.get('rooms')}")
        logger.info(f"  ✅ price_per_sqft: {property_data.get('price_per_sqft')}")
        logger.info(f"  ✅ on_market_date: {property_data.get('on_market_date')}")
        logger.info(f"  ✅ ownership_type: {property_data.get('ownership_type')}")
        logger.info(f"  ✅ parcel_number: {property_data.get('parcel_number')}")
        
        # Photos
        photos = property_obj.get('responsivePhotos', [])
        property_data['photos'] = photos
        property_data['photo_count'] = len(photos)
        
        # Description - look in multiple places
        description = property_obj.get('description')
        if not description:
            # Try to find description in resoFacts
            reso_facts = property_obj.get('resoFacts', {})
            if isinstance(reso_facts, dict):
                description = reso_facts.get('description') or reso_facts.get('propertyDescription')
            elif isinstance(reso_facts, list):
                for fact in reso_facts:
                    if isinstance(fact, dict) and fact.get('factLabel', '').lower() == 'description':
                        description = fact.get('factValue')
                        break
        
        # If still no description, try to extract from HTML content
        if not description and property_data.get('html_content'):
            description = self.extract_description_from_html(property_data['html_content'])
        
        # Store description in both places for compatibility
        property_data['description'] = description  # For the expected fields list
        property_data['description_preview'] = description  # For backward compatibility
        
        # Also store the HTML content for potential description extraction
        property_data['html_content'] = property_data.get('html_content', '')
        
        # Price history and tax history
        property_data['price_history'] = property_obj.get('priceHistory')
        property_data['tax_history'] = property_obj.get('taxHistory')
        property_data['tax_annual_amount'] = property_obj.get('taxAnnualAmount')
        property_data['tax_assessed_value'] = property_obj.get('taxAssessedValue')
        
        # Schools
        property_data['schools'] = {
            'elementary': property_obj.get('elementarySchool'),
            'middle': property_obj.get('middleOrJuniorSchool'),
            'high': property_obj.get('highSchool'),
            'elementary_district': property_obj.get('elementarySchoolDistrict'),
            'middle_district': property_obj.get('middleOrJuniorSchoolDistrict'),
            'high_district': property_obj.get('highSchoolDistrict')
        }
        
        # Parking information
        property_data['parking_info'] = {
            'features': property_obj.get('parkingFeatures'),
            'capacity': property_obj.get('parkingCapacity'),
            'open_capacity': property_obj.get('openParkingCapacity'),
            'covered_capacity': property_obj.get('coveredParkingCapacity'),
            'carport_capacity': property_obj.get('carportParkingCapacity')
        }
        
        # Additional property features
        property_data['additional_features'] = {
            'stories': property_obj.get('stories'),
            'stories_total': property_obj.get('storiesTotal'),
            'structure_type': property_obj.get('structureType'),
            'architectural_style': property_obj.get('architecturalStyle'),
            'construction_materials': property_obj.get('constructionMaterials'),
            'flooring': property_obj.get('flooring'),
            'roof_type': property_obj.get('roofType'),
            'foundation': property_obj.get('foundationDetails'),
            'exterior_walls': property_obj.get('exteriorWalls'),
            'window_features': property_obj.get('windowFeatures'),
            'door_features': property_obj.get('doorFeatures'),
            'fireplace_features': property_obj.get('fireplaceFeatures'),
            'fireplaces': property_obj.get('fireplaces'),
            'pool_features': property_obj.get('poolFeatures'),
            'spa_features': property_obj.get('spaFeatures'),
            'fencing': property_obj.get('fencing'),
            'irrigation': property_obj.get('irrigationWaterRightsAcres'),
            'utilities': property_obj.get('utilities'),
            'sewer': property_obj.get('sewer'),
            'water_source': property_obj.get('waterSource'),
            'electric': property_obj.get('electric'),
            'gas': property_obj.get('gas'),
            'zoning': property_obj.get('zoning'),
            'zoning_description': property_obj.get('zoningDescription')
        }
        
        # Community and neighborhood
        property_data['community_info'] = {
            'subdivision': property_obj.get('subdivisionName'),
            'neighborhood': address.get('neighborhood'),
            'community': address.get('community'),
            'city_region': property_obj.get('cityRegion'),
            'parent_region': property_obj.get('parentRegion', {}).get('name')
        }
        
        # Listing details
        property_data['listing_details'] = {
            'listing_id': property_obj.get('listingId'),
            'listing_terms': property_obj.get('listingTerms'),
            'marketing_type': property_obj.get('marketingType'),
            'special_conditions': property_obj.get('specialListingConditions'),
            'offer_review_date': property_obj.get('offerReviewDate'),
            'coming_soon_date': property_obj.get('comingSoonOnMarketDate'),
            'is_new_construction': property_obj.get('isNewConstruction'),
            'is_senior_community': property_obj.get('isSeniorCommunity'),
            'has_home_warranty': property_obj.get('hasHomeWarranty'),
            'has_land_lease': property_obj.get('hasLandLease'),
            'land_lease_amount': property_obj.get('landLeaseAmount'),
            'land_lease_expiration': property_obj.get('landLeaseExpirationDate')
        }
        
        # Search for waterfront keywords
        waterfront_keywords = self.search_for_waterfront_info(property_obj)
        property_data['waterfront_keywords'] = waterfront_keywords
        
        # Use flexible field extraction for better coverage
        # Get the raw data sources for flexible extraction
        next_data_raw = property_data.get('_next_data_raw', '')
        next_data_processed = property_data.get('_next_data_processed', '')
        html_content = property_data.get('_html_content', '')
        
        # Extract fields using flexible methods
        flexible_fields = [
            'year_built', 'mls_id', 'mls_name', 'price_per_sqft', 'hoa_fee',
            'monthly_hoa_fee', 'zestimate', 'rent_zestimate', 'days_on_zillow',
            'page_view_count', 'favorite_count', 'home_status', 'contingent_type',
            'listing_provider', 'home_type', 'listing_agent', 'listing_office',
            'listing_agent_phone', 'photo_urls', 'price_history', 'tax_history',
            'reso_facts', 'schools', 'parking_info', 'on_market_date',
            'ownership_type', 'parcel_number', 'living_area_units',
            'waterfront_features', 'water_view', 'rooms', 'view', 'boat_access'
        ]
        
        # Extract MLS and listing info from attributionInfo
        attribution = property_obj.get('attributionInfo', {})
        if attribution:
            property_data['mls_id'] = attribution.get('mlsId')
            property_data['mls_name'] = attribution.get('mlsName')
            property_data['listing_agent'] = attribution.get('agentName')
            property_data['listing_agent_phone'] = attribution.get('agentPhoneNumber')
            property_data['listing_office'] = attribution.get('brokerName')
            logger.info(f"🔍 MLS/Agent data extracted: MLS={property_data['mls_id']}, Agent={property_data['listing_agent']}")
        
        # Extract year built from resoFacts or direct field
        year_built = property_obj.get('yearBuilt') or (property_obj.get('resoFacts', {}).get('yearBuilt') if property_obj.get('resoFacts') else None)
        if year_built:
            property_data['year_built'] = year_built
            logger.info(f"🔍 Year built extracted: {year_built}")
        
        # Extract price history and tax history
        price_history = property_obj.get('priceHistory')
        if price_history:
            property_data['price_history'] = json.dumps(price_history, separators=(',', ':'))
            property_data['price_history_preview'] = json.dumps(price_history, separators=(',', ':'))[:500]
            logger.info(f"🔍 Price history extracted: {len(property_data['price_history'])} characters")
        
        tax_history = property_obj.get('taxHistory')
        if tax_history:
            property_data['tax_history'] = json.dumps(tax_history, separators=(',', ':'))
            property_data['tax_history_preview'] = json.dumps(tax_history, separators=(',', ':'))[:500]
            logger.info(f"🔍 Tax history extracted: {len(property_data['tax_history'])} characters")
        
        # Extract lot size using the more reliable lotAreaValue + lotAreaUnits combination
        lot_area_value = property_obj.get('lotAreaValue')
        lot_area_units = property_obj.get('lotAreaUnits')
        if lot_area_value and lot_area_units:
            property_data['lot_area_value'] = lot_area_value
            property_data['lot_area_units'] = lot_area_units
            property_data['lot_size_combined'] = f"{lot_area_value} {lot_area_units}"
            logger.info(f"🔍 Lot size extracted: {lot_area_value} {lot_area_units}")
        else:
            # Fallback to lotSize if available
            lot_size = property_obj.get('lotSize')
            if lot_size:
                property_data['lot_size_combined'] = lot_size
                logger.info(f"🔍 Lot size fallback: {lot_size}")
            else:
                property_data['lot_size_combined'] = None
        
        # Extract HOA fee
        hoa_fee = property_obj.get('hoaFee') or property_obj.get('monthlyHoaFee')
        if hoa_fee:
            property_data['hoa_fee'] = hoa_fee
            logger.info(f"🔍 HOA fee extracted: {hoa_fee}")
        else:
            property_data['hoa_fee'] = None
        
        # Extract parking information
        parking_capacity = property_obj.get('parkingCapacity')
        if parking_capacity:
            property_data['parking_info'] = f"Capacity: {parking_capacity}"
            logger.info(f"🔍 Parking info extracted: {parking_capacity}")
        else:
            property_data['parking_info'] = None
        
        # Extract county (often under 'cnty' or in adTargets)
        county = property_obj.get('county') or property_obj.get('cnty')
        if not county:
            # Check if county is in adTargets
            ad_targets = property_obj.get('adTargets', {})
            if isinstance(ad_targets, dict):
                county = ad_targets.get('cnty')
        
        if county:
            property_data['county'] = county
            logger.info(f"🔍 County extracted: {county}")
        else:
            property_data['county'] = None
        
        # Extract property type from propertyTypeDimension
        property_type = property_obj.get('propertyTypeDimension')
        if property_type:
            property_data['property_type'] = property_type
            logger.info(f"🔍 Property type extracted: {property_type}")
        else:
            property_data['property_type'] = None
        
        for field_name in flexible_fields:
            if field_name not in property_data or property_data[field_name] is None:
                extracted_value = self.extract_field_flexible(
                    field_name, cache_data, next_data_raw, next_data_processed, html_content
                )
                if extracted_value is not None:
                    property_data[field_name] = extracted_value
                            # Don't log large data structures like photos
                    if field_name == 'photos' and isinstance(extracted_value, list) and len(extracted_value) > 5:
                        logger.info(f"🔍 Flexible extraction found {field_name}: {len(extracted_value)} photos")
                    elif isinstance(extracted_value, (dict, list)) and len(str(extracted_value)) > 200:
                        logger.info(f"🔍 Flexible extraction found {field_name}: {type(extracted_value).__name__} with {len(extracted_value) if isinstance(extracted_value, (list, dict)) else 'complex'} data")
                    else:
                        logger.info(f"🔍 Flexible extraction found {field_name}: {extracted_value}")
        
        # Apply enhanced regex patterns to multiple data sources
        description = property_data.get('description', '')
        next_data_raw = property_data.get('_next_data_raw', '')  # Raw Next.js data string
        next_data_processed = property_data.get('_next_data_processed', '')  # Processed Next.js data
        
        # Enhanced dock information extraction - DESCRIPTION FIELD ONLY
        if description:
            dock_patterns = [
                r'dock[^.]*(?:height|length|width|size)[^.]*',
                r'(?:private|shared|community)\s+dock[^.]*',
                r'dock\s+(?:access|available|included)[^.]*',
                r'(?:boat|yacht)\s+dock[^.]*',
                r'dock\s+(?:slip|berth|mooring)[^.]*'
            ]
            property_data['dock_info'] = self.apply_enhanced_regex_patterns(description, dock_patterns)
            logger.info(f"🔍 Dock info extracted from description: {property_data['dock_info']}")
        else:
            property_data['dock_info'] = None
            
        # Extract entire resoFacts category using regex - this contains rich nested property data
        reso_facts_raw = self._extract_reso_facts_via_regex(html_content, next_data_raw, next_data_processed)
        if reso_facts_raw:
            # Clean up newlines and store as-is
            property_data['reso_facts'] = reso_facts_raw.replace('\n', ' ').replace('\r', ' ')
            # Also create a preview version (first 500 chars)
            property_data['reso_facts_preview'] = reso_facts_raw[:500].replace('\n', ' ').replace('\r', ' ')
            logger.info(f"🔍 ResoFacts extracted via regex: {len(property_data['reso_facts'])} characters")
        else:
            property_data['reso_facts'] = None
            property_data['reso_facts_preview'] = None
        
        # Enhanced bridge height extraction
        bridge_patterns = [
            r'bridge\s+height[^.]*',
            r'(?:no\s+)?fixed\s+bridge[^.]*',
            r'(?:bridge|overpass)\s+(?:clearance|height)[^.]*',
            r'(?:under|below)\s+bridge[^.]*'
        ]
        bridge_results = self.apply_multi_source_regex('bridge_height', bridge_patterns,
                                                     description, next_data_raw, next_data_processed)
        property_data['regex_bridge_height'] = bridge_results
        
        # Enhanced water depth extraction
        depth_patterns = [
            r'water\s+depth[^.]*',
            r'(?:deep|shallow)\s+water[^.]*',
            r'(?:draft|drafting)[^.]*',
            r'(?:low|high)\s+tide[^.]*',
            r'(?:mean|average)\s+water\s+level[^.]*'
        ]
        depth_results = self.apply_multi_source_regex('water_depth', depth_patterns,
                                                    description, next_data_raw, next_data_processed)
        property_data['regex_water_depth'] = depth_results
        
        # Additional waterfront features
        canal_patterns = [
            r'canal\s+(?:front|access|view)[^.]*',
            r'(?:intracoastal|icw)\s+(?:waterway|canal)[^.]*',
            r'canal\s+(?:width|depth|length)[^.]*'
        ]
        canal_results = self.apply_multi_source_regex('canal_info', canal_patterns,
                                                    description, next_data_raw, next_data_processed)
        property_data['regex_canal_info'] = canal_results
        
        # Ocean access patterns
        ocean_patterns = [
            r'ocean\s+(?:front|access|view)[^.]*',
            r'(?:beach|shoreline)\s+access[^.]*',
            r'(?:gulf|atlantic|pacific)\s+access[^.]*'
        ]
        ocean_results = self.apply_multi_source_regex('ocean_access', ocean_patterns,
                                                    description, next_data_raw, next_data_processed)
        property_data['regex_ocean_access'] = ocean_results
        
        # Also search in other text fields for waterfront information
        if property_data.get('additional_features'):
            additional_text = str(property_data['additional_features'])
            if additional_text:
                # Look for waterfront features in additional features
                waterfront_in_features = self.search_for_waterfront_info(property_data['additional_features'])
                if waterfront_in_features:
                    property_data['waterfront_keywords'].extend(waterfront_in_features)
        
        # Enhanced waterfront classification
        property_data['is_waterfront'] = bool(
            property_data.get('waterfront_features') or 
            property_data.get('water_view') or 
            property_data.get('water_body_name') or
            property_data.get('waterfront_keywords') or
            any(keyword in str(property_data.get('description', '')).lower() 
                for keyword in ['waterfront', 'ocean', 'canal', 'river', 'lake', 'bay', 'dock'])
        )
        
        # Waterfront type classification
        waterfront_type = []
        if property_data.get('waterfront_features'):
            waterfront_type.append('waterfront')
        if property_data.get('water_view'):
            waterfront_type.append('water_view')
        if property_data.get('water_body_name'):
            waterfront_type.append('water_body')
        
        # Check multi-source regex results for waterfront features
        if property_data.get('regex_ocean_access'):
            ocean_results = property_data['regex_ocean_access']
            if any(matches for matches in ocean_results.values()):
                waterfront_type.append('ocean_access')
        
        if property_data.get('regex_canal_info'):
            canal_results = property_data['regex_canal_info']
            if any(matches for matches in canal_results.values()):
                waterfront_type.append('canal_access')
        
        if property_data.get('regex_dock_info'):
            dock_results = property_data['regex_dock_info']
            if any(matches for matches in dock_results.values()):
                waterfront_type.append('dock_access')
        
        property_data['waterfront_type'] = waterfront_type if waterfront_type else None
        
        return property_data
    
    def save_json_snippets(self, url: str, html_content: str, payload: Dict[str, Any], cache_data: Dict[str, Any], 
                           property_data: Dict[str, Any]) -> None:
        """Save JSON snippets for comparison across sessions"""
        try:
            zpid = property_data.get('zpid', 'unknown')
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Save HTML and a static (no-scripts) copy (only if enabled)
            if self.save_html:
                html_file = self.html_dir / f"{zpid}_{ts}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                try:
                    no_scripts = re.sub(r'<script\b[^<]*(?:(?!<\/script>).)*<\/script>', '', html_content, flags=re.IGNORECASE|re.DOTALL)
                    static_file = self.html_dir / f"{zpid}_{ts}_static.html"
                    with open(static_file, 'w', encoding='utf-8') as sf:
                        sf.write(no_scripts)
                except Exception:
                    pass
            
            # Save full payload (__NEXT_DATA__) (only if enabled)
            if self.save_next_data:
                payload_file = self.next_dir / f"{zpid}_{ts}.json"
                with open(payload_file, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
            
            # Save cache data (only if enabled)
            if self.save_cache:
                cache_file = self.cache_dir / f"{zpid}_{ts}.json"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # Save extracted property data (only if enabled)
            if self.save_processed:
                data_file = self.processed_dir / f"{zpid}_{ts}.json"
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(property_data, f, indent=2, ensure_ascii=False)
            
            # Create a summary snippet for quick comparison (only if enabled)
            if self.save_summary:
                summary = {
                    'zpid': zpid,
                    'url': url,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'waterfront_features_found': len([k for k in property_data.keys() if 'waterfront' in k.lower()]),
                    'waterfront_keywords_found': property_data.get('waterfront_keywords', []),
                    'regex_matches': {k: v for k, v in property_data.items() if k.startswith('regex_')},
                    'extracted_fields': {k: v for k, v in property_data.items() if k.startswith('extracted_')},
                    'key_waterfront_info': {k: v for k, v in property_data.items() if k.startswith('key_waterfront')},
                    'value_waterfront_info': {k: v for k, v in property_data.items() if k.startswith('value_waterfront')}
                }
                
                summary_file = self.summary_dir / f"{zpid}_{ts}.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Only log if any files were saved
            files_saved = []
            if self.save_html: files_saved.append('HTML')
            if self.save_next_data: files_saved.append('payload')
            if self.save_cache: files_saved.append('cache')
            if self.save_processed: files_saved.append('processed')
            if self.save_summary: files_saved.append('summary')
            
            if files_saved:
                logger.info(f"✅ Saved {', '.join(files_saved)} files for property {zpid}")
            
        except Exception as e:
            logger.error(f"Error saving JSON snippets: {e}")
    
    async def extract_property(self, url: str) -> Dict[str, Any]:
        """Extract a single property with flexible waterfront detection"""
        logger.info(f"🔍 Extracting property: {url}")
        
        # Check if this is a search results page or individual property page
        if self._is_search_results_page(url):
            logger.info(f"🔍 Detected search results page: {url}")
            
            # Check if we should continue from a saved file
            if self.continue_from_file:
                logger.info(f"🔄 Continuing from saved URLs file: {self.continue_from_file}")
                property_urls = self._load_urls_from_file(self.continue_from_file)
                if not property_urls:
                    logger.error(f"❌ No URLs found in {self.continue_from_file}")
                    property_urls = []
            else:
                # Extract property URLs from multiple pages of search results
                # Note: max_pages and max_properties_per_search are set via command line args
                property_urls = await self._extract_all_property_urls_from_search(url, max_pages=self.max_search_pages)  # Use configured page limit
                
                # Save URLs list if requested
                if property_urls and self.save_urls_list:
                    self._save_urls_list(property_urls, url)
            
            if property_urls:
                logger.info(f"🔍 Found {len(property_urls)} property URLs across search results pages")
                if self.simple_logging:
                    self._update_counter('search_results_found', len(property_urls))
                
                # Process each property URL (limit to max_properties_per_search)
                urls_to_process = property_urls[:self.max_properties_per_search]
                logger.info(f"🔍 Starting pre-filtering of {len(urls_to_process)} URLs")
                
                # Pre-filter URLs to remove already scraped properties
                filtered_urls = []
                for prop_url in urls_to_process:
                    logger.info(f"🔍 Checking URL: {prop_url}")
                    zpid_match = re.search(r'/([^/]+)_zpid/$', prop_url)
                    if zpid_match:
                        zpid = zpid_match.group(1)
                        logger.info(f"🔍 Extracted ZPID: {zpid}")
                        
                        # Check database BEFORE we start processing
                        logger.info(f"🔍 About to check database for ZPID: {zpid}")
                        if await self._is_property_already_scraped_db(zpid):
                            logger.info(f"⏭️ Skipping {zpid} - already in database, no need to scrape")
                            continue
                        
                        filtered_urls.append(prop_url)
                        logger.info(f"🆕 Will process new property: {zpid}")
                    else:
                        # If we can't extract ZPID, include it anyway
                        logger.info(f"🔍 Could not extract ZPID from URL: {prop_url}")
                        filtered_urls.append(prop_url)
                
                logger.info(f"🔍 Pre-filtering complete. Original: {len(urls_to_process)}, Filtered: {len(filtered_urls)}")
                logger.info(f"🔍 Processing {len(filtered_urls)} new properties (limited to {self.max_properties_per_search})")
                
                # Use concurrent extraction for better performance
                if self.max_concurrent_properties > 1:
                    logger.info(f"🚀 Using concurrent extraction with {self.max_concurrent_properties} threads")
                    results = await self._extract_properties_concurrent(filtered_urls)
                else:
                    # Sequential processing for single-threaded mode
                    logger.info("🐌 Using sequential processing (single thread)")
                    results = []
                    processed_count = 0
                    for i, prop_url in enumerate(filtered_urls, 1):
                        try:
                            logger.info(f"🔍 Processing property {i}/{len(filtered_urls)}: {prop_url}")
                            
                            result = await self._extract_single_property(prop_url)
                            if result:
                                results.append(result)
                                processed_count += 1
                                logger.info(f"✅ Successfully extracted property {i}/{len(filtered_urls)} - ZPID: {result.get('zpid', 'Unknown')}")
                                
                                # Stop if we've reached the limit
                                if processed_count >= self.max_properties_per_search:
                                    logger.info(f"🛑 Reached property limit ({self.max_properties_per_search}), stopping extraction")
                                    break
                            else:
                                logger.warning(f"⚠️ No result for property {i}/{len(filtered_urls)}")
                        except Exception as e:
                            logger.error(f"❌ Error extracting property {i}/{len(filtered_urls)} from {prop_url}: {e}")
                            self._update_counter('errors')
                
                # Return combined results
                if results:
                    combined_result = {
                        'search_page_url': url,
                        'properties_found': len(property_urls),
                        'properties_processed': len(urls_to_process),
                        'properties_extracted': len(results),
                        'property_results': results,
                        'zpid': f"search_results_{hashlib.md5(url.encode()).hexdigest()[:8]}"
                    }
                    logger.info(f"🎉 Successfully extracted {len(results)} properties from search results")
                    
                    # Show simple logging summary if enabled
                    if self.simple_logging:
                        self._show_simple_summary()
                    
                    return combined_result
                else:
                    logger.error("❌ Failed to extract any properties from search results page")
                    # Show simple logging summary even if no results
                    if self.simple_logging:
                        self._show_simple_summary()
                    return {}
            else:
                logger.error("❌ No property URLs found in search results page")
                return {}
        else:
            # This is an individual property page
            return await self._extract_single_property(url)
    
    def _is_search_results_page(self, url: str) -> bool:
        """Detect if a URL is a search results page vs individual property page"""
        # Search results page indicators
        search_indicators = [
            '/homes/?',  # Main search results
            '/fort-lauderdale-fl/waterfront/',  # Specific area search
            'searchQueryState=',  # Search query parameters
            'pagination',  # Pagination in URL
            'mapBounds',  # Map bounds in URL
            'isMapVisible',  # Map visibility flag
            'filterState'  # Filter state
        ]
        
        # Individual property page indicators
        property_indicators = [
            '/homedetails/',  # Home details page
            '_zpid',  # ZPID in URL
            '/homes-for-sale/',  # Specific property page
        ]
        
        url_lower = url.lower()
        
        # Check for search indicators
        search_score = sum(1 for indicator in search_indicators if indicator.lower() in url_lower)
        
        # Check for property indicators
        property_score = sum(1 for indicator in property_indicators if indicator.lower() in url_lower)
        
        # If search score is higher, it's likely a search results page
        return search_score > property_score
    
    def _create_pagination_url(self, base_url: str, page: int) -> str:
        """Create paginated URL for Zillow search results"""
        import json
        from urllib.parse import urlparse, parse_qs, urlencode
        
        # Parse existing searchQueryState if present
        if 'searchQueryState=' in base_url:
            try:
                # Parse the URL properly
                parsed = urlparse(base_url)
                query_params = parse_qs(parsed.query)
                
                if 'searchQueryState' in query_params:
                    # Decode the searchQueryState
                    search_state_str = query_params['searchQueryState'][0]
                    search_state = json.loads(search_state_str)
                    
                    # Update pagination
                    if 'pagination' not in search_state:
                        search_state['pagination'] = {}
                    search_state['pagination']['currentPage'] = page
                    
                    # Rebuild the URL with updated state
                    new_query_params = parse_qs(parsed.query)
                    new_query_params['searchQueryState'] = [json.dumps(search_state)]
                    
                    # Reconstruct the URL
                    new_query_string = urlencode(new_query_params, doseq=True)
                    new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query_string}"
                    
                    logger.info(f"🔗 Created paginated URL for page {page}: {new_url}")
                    return new_url
                    
            except Exception as e:
                logger.warning(f"⚠️ Error parsing searchQueryState for pagination: {e}")
        
        # Fallback: create simple pagination
        if '?' in base_url:
            return f"{base_url}&page={page}"
        else:
            return f"{base_url}?page={page}"
    
    async def _extract_all_property_urls_from_search(self, search_url: str, max_pages: int = None) -> List[str]:
        """Extract property URLs from multiple pages of search results"""
        if max_pages:
            logger.info(f"🔍 Extracting property URLs from search with pagination (max {max_pages} pages)")
        else:
            logger.info(f"🔍 Extracting property URLs from search with unlimited pagination")
        logger.info(f"🔍 Search URL: {search_url}")
        
        all_urls = []
        seen_urls = set()
        page = 1
        consecutive_empty_pages = 0
        max_empty_pages = 5  # Stop after 5 consecutive empty pages (more lenient)
        
        # Track total results expected from first page
        total_results_expected = None
        
        while (max_pages is None or page <= max_pages) and consecutive_empty_pages < max_empty_pages:
            # Log pagination status
            if page > 1:
                logger.info(f"🔍 Pagination status: page {page}, max_pages: {max_pages}, consecutive_empty: {consecutive_empty_pages}/{max_empty_pages}")
            if max_pages:
                logger.info(f"📄 Processing search page {page}/{max_pages}...")
            else:
                logger.info(f"📄 Processing search page {page}...")
            
            # Create paginated URL
            if page == 1:
                current_url = search_url
            else:
                current_url = self._create_pagination_url(search_url, page)
                logger.info(f"🔗 Created paginated URL: {current_url}")
            
            # Extract URLs from this page
            logger.info(f"🔍 Fetching page {page} from: {current_url}")
            page_urls = await self._extract_property_urls_from_search_page(current_url)
            
            if not page_urls:
                logger.info(f"⚠️ No URLs found on page {page}")
                consecutive_empty_pages += 1
                page += 1
                continue
            
            # Reset empty page counter
            consecutive_empty_pages = 0
            
            # On first page, try to extract total results count
            if page == 1 and total_results_expected is None:
                total_results_expected = self._extract_total_results_count(current_url, page_urls)
                if total_results_expected:
                    logger.info(f"📊 Expected total results: {total_results_expected}")
                else:
                    logger.info(f"📊 Could not determine expected total results")
            
            # Process new URLs
            new_urls = 0
            for url in page_urls:
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_urls.append(url)
                    new_urls += 1
                    
                    # Check if we've reached the property limit
                    if len(all_urls) >= self.max_properties_per_search:
                        logger.info(f"🛑 Reached property limit ({self.max_properties_per_search}) during search results extraction")
                        if self.simple_logging:
                            self._update_counter('search_results_found', len(all_urls))
                        return all_urls
            
            logger.info(f"  ✅ Page {page}: {len(page_urls)} results, {new_urls} new URLs")
            logger.info(f"  📊 Total unique URLs collected: {len(all_urls)}")
            
            # Debug: Show some example URLs found on this page
            if page_urls and page <= 2:  # Only show for first 2 pages to avoid spam
                sample_urls = page_urls[:3]  # Show first 3 URLs
                logger.info(f"  🔍 Sample URLs from page {page}: {sample_urls}")
            
            # Check if we're getting duplicate results (indicating we've reached the end)
            # Only count as empty if we're past the first few pages and getting consistent duplicates
            if new_urls == 0 and page > 3:
                logger.info(f"⚠️ No new URLs on page {page} - may have reached end of results")
                logger.info(f"🔍 Page {page} had {len(page_urls)} total URLs but {new_urls} were new")
                consecutive_empty_pages += 1
                logger.info(f"🔍 Consecutive empty pages: {consecutive_empty_pages}/{max_empty_pages}")
            elif new_urls == 0:
                logger.info(f"ℹ️ No new URLs on page {page} (duplicates expected in early pages)")
                logger.info(f"🔍 Page {page} had {len(page_urls)} total URLs but {new_urls} were new")
                # Don't count early duplicate pages as "empty" - this is normal
            
            page += 1
            
            # Add delay between requests to be respectful
            await asyncio.sleep(1)
        
        logger.info(f"🔍 Pagination complete! Processed {page - 1} pages, found {len(all_urls)} unique URLs")
        
        # Validate that we can get all expected results (only if we're doing limited pagination)
        if total_results_expected and max_pages and max_pages > 1 and len(all_urls) < total_results_expected * 0.8:  # Allow 80% threshold
            logger.error(f"❌ CRITICAL: Only found {len(all_urls)} URLs out of {total_results_expected} expected results")
            logger.error(f"❌ Pagination is not working correctly - stopping extraction")
            return []
        elif max_pages == 1 and total_results_expected:
            logger.info(f"✅ Single page mode: Found {len(all_urls)} URLs (expected ~{total_results_expected} total available)")
        elif max_pages is None:
            logger.info(f"✅ Unlimited pagination mode: Found {len(all_urls)} URLs across all available pages")
        else:
            logger.info(f"✅ Limited pagination mode: Found {len(all_urls)} URLs across {page - 1} pages (max: {max_pages})")
        
        # Additional debug info for pagination analysis
        if max_pages and page - 1 < max_pages:
            logger.info(f"🔍 Pagination stopped early: processed {page - 1} pages out of {max_pages} maximum")
            logger.info(f"🔍 This could indicate: 1) Reached consecutive empty pages limit, 2) All results found, or 3) Zillow returned no more unique results")
        
        return all_urls
    
    def _extract_total_results_count(self, search_url: str, page_urls: List[str]) -> Optional[int]:
        """Extract the total number of results expected from search results page"""
        try:
            # For complex search URLs, we need to parse the actual page content
            # The total count is usually in the page title or breadcrumbs
            if 'searchQueryState' in search_url:
                # This is a complex search URL - we need to fetch and parse it
                # For now, return None to avoid blocking the process
                # TODO: Implement actual page parsing to get total count
                return None
            elif 'fort-lauderdale-fl/waterfront/' in search_url:
                # Simple URL - we know it should have more than 41 results
                # Return a reasonable estimate based on typical Zillow results
                return 100  # Conservative estimate
            else:
                return None
        except Exception as e:
            logger.warning(f"⚠️ Could not extract total results count: {e}")
            return None
    
    async def _extract_property_urls_from_search_page(self, search_url: str) -> List[str]:
        """Extract all property URLs from a search results page using proven logic from collect_urls_from_srp.py"""
        logger.info(f"🔍 Extracting property URLs from search page: {search_url}")
        
        # Fetch the search results page
        logger.info(f"🔍 Fetching search results page via Zyte...")
        html_content = await self.fetch_property_page_zyte(search_url)
        if not html_content:
            logger.error("❌ Failed to fetch search results page")
            return []
        
        logger.info(f"🔍 Successfully fetched search page ({len(html_content)} characters)")
        
        # Extract Next.js payload
        logger.info(f"🔍 Extracting __NEXT_DATA__ payload...")
        payload = self.extract_next_data_payload(html_content)
        if not payload:
            logger.error("❌ Failed to extract __NEXT_DATA__ payload from search page")
            return []
        
        logger.info(f"🔍 Successfully extracted payload with keys: {list(payload.keys())}")
        
        # Look for property URLs in the search results using proven approach
        property_urls = []
        
        try:
            # Method 1: Use proven logic from collect_urls_from_srp.py
            # Look for URLs in searchPageState.cat1.searchResults.listResults
            props = payload.get('props', {}).get('pageProps', {})
            logger.info(f"🔍 PageProps keys: {list(props.keys())}")
            
            # Check searchPageState structure
            search_state = props.get('searchPageState') or props.get('initialState', {}).get('searchPageState') or {}
            cat1 = search_state.get('cat1', {})
            list_results = (cat1.get('searchResults') or {}).get('listResults') or []
            
            # Debug logging to see what we're working with
            logger.info(f"🔍 Search state keys: {list(search_state.keys())}")
            logger.info(f"🔍 Cat1 keys: {list(cat1.keys())}")
            logger.info(f"🔍 List results count: {len(list_results)}")
            
            if list_results:
                logger.info(f"🔍 First result sample: {list_results[0] if len(list_results) > 0 else 'None'}")
            
            if not list_results:
                # Try alternative paths
                logger.info("🔍 Trying alternative search results paths...")
                # Look for search results in different locations
                for key in ['searchResults', 'listResults', 'results', 'properties']:
                    if key in cat1:
                        logger.info(f"🔍 Found {key} in cat1: {type(cat1[key])}")
                        if isinstance(cat1[key], list):
                            list_results = cat1[key]
                            break
                        elif isinstance(cat1[key], dict):
                            list_results = cat1[key].get('listResults', [])
                            if list_results:
                                break
            
            # Additional debug: Check if this is actually a search results page
            if not list_results and not property_urls:
                logger.warning("⚠️ This doesn't appear to be a search results page - no property listings found")
                logger.info(f"🔍 Payload keys: {list(payload.keys())}")
                logger.info(f"🔍 Props keys: {list(props.keys())}")
                logger.info(f"🔍 Page type detection may be incorrect")
            
            for item in list_results:
                detail = item.get('detailUrl') or item.get('hdpUrl') or item.get('hdpUrlNew')
                if detail:
                    full = detail if str(detail).startswith('http') else f"https://www.zillow.com{detail}"
                    
                    # Extract ZPID from URL to check if we already have this property
                    zpid_match = re.search(r'/homedetails/([^/]+)_zpid/', full)
                    if zpid_match:
                        zpid = zpid_match.group(1)
                        if self._is_property_already_scraped(zpid):
                            logger.info(f"⏭️ Skipping already scraped property: {zpid}")
                            continue
                        else:
                            logger.info(f"🆕 Found new property: {zpid}")
                    
                    property_urls.append(full)
                    logger.info(f"🔍 Found property URL: {full}")
            
            # Method 2: Fallback - look for property URLs in the HTML content using regex
            if not property_urls:
                logger.info("🔍 No URLs found in searchPageState, trying HTML regex fallback...")
                property_pattern = r'https://www\.zillow\.com/homedetails/([^/]+)_zpid/'
                matches = re.findall(property_pattern, html_content)
                for match in matches:
                    zpid = match
                    if self._is_property_already_scraped(zpid):
                        logger.info(f"⏭️ Skipping already scraped property via regex: {zpid}")
                        continue
                    
                    property_url = f"https://www.zillow.com/homedetails/{match}_zpid/"
                    if property_url not in property_urls:
                        property_urls.append(property_url)
                        logger.info(f"🔍 Found new property URL via regex: {zpid}")
            
            # Method 3: Additional fallback - look for other URL patterns
            if not property_urls:
                logger.info("🔍 No URLs found via regex, trying additional patterns...")
                # Look for any href that contains homedetails
                href_pattern = r'href="([^"]*homedetails[^"]*)"'
                href_matches = re.findall(href_pattern, html_content)
                for href in href_matches:
                    if href.startswith('/'):
                        full_url = f"https://www.zillow.com{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # Extract ZPID from href to check if we already have this property
                    zpid_match = re.search(r'/homedetails/([^/]+)_zpid', full_url)
                    if zpid_match:
                        zpid = zpid_match.group(1)
                        if self._is_property_already_scraped(zpid):
                            logger.info(f"⏭️ Skipping already scraped property via href: {zpid}")
                            continue
                        else:
                            logger.info(f"🆕 Found new property via href: {zpid}")
                    
                    if full_url not in property_urls:
                        property_urls.append(full_url)
                        logger.info(f"🔍 Found property URL via href: {full_url}")
            
        except Exception as e:
            logger.error(f"❌ Error extracting property URLs from search page: {e}")
        
        # Remove duplicates
        property_urls = list(set(property_urls))
        
        # Count new vs. existing properties
        new_count = len(property_urls)
        logger.info(f"🔍 Total new property URLs found: {new_count}")
        logger.info(f"📊 Summary: {new_count} new properties ready for scraping")
        
        return property_urls
    
    async def _extract_properties_concurrent(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Extract multiple properties concurrently with configurable concurrency limit"""
        if not urls:
            return []
        
        logger.info(f"🚀 Starting concurrent property extraction with {len(urls)} URLs (max {self.max_concurrent_properties} concurrent)")
        if self.simple_logging:
            self._simple_log(f"Starting extraction of {len(urls)} properties with {self.max_concurrent_properties} concurrent threads")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent_properties)
        
        async def extract_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    self._update_counter('properties_scraped')
                    result = await self._extract_single_property(url)
                    if result:
                        self._update_counter('properties_extracted')
                    return result
                except Exception as e:
                    self._update_counter('errors')
                    logger.error(f"❌ Error extracting property {url}: {e}")
                    return None
        
        # Create tasks for all URLs
        tasks = [extract_with_semaphore(url) for url in urls]
        
        # Execute all tasks concurrently
        results = []
        for i, completed_task in enumerate(asyncio.as_completed(tasks), 1):
            try:
                result = await completed_task
                if result:
                    results.append(result)
                    if self.simple_logging:
                        self._simple_log(f"Completed {i}/{len(urls)} properties")
                else:
                    if self.simple_logging:
                        self._simple_log(f"Failed {i}/{len(urls)} properties")
            except Exception as e:
                self._update_counter('errors')
                logger.error(f"❌ Task execution error: {e}")
        
        logger.info(f"✅ Concurrent extraction complete: {len(results)}/{len(urls)} properties successful")
        return results

    async def _extract_single_property(self, url: str) -> Dict[str, Any]:
        """Extract a single property from its URL (original extract_property logic)"""
        logger.info(f"🔍 Extracting single property: {url}")
        
        # Fetch the page
        html_content = await self.fetch_property_page_zyte(url)
        if not html_content:
            logger.error("Failed to fetch property page")
            return {}
        
        # Extract Next.js payload
        payload = self.extract_next_data_payload(html_content)
        if not payload:
            logger.error("Failed to extract __NEXT_DATA__ payload")
            return {}
        
        # Extract gdpClientCache
        cache_data = self.extract_gdp_client_cache(payload)
        if not cache_data:
            logger.error("Failed to extract gdpClientCache")
            return {}
        
        # Capture raw Next.js data for regex processing
        raw_next_data = self.extract_raw_next_data(html_content)
        processed_next_data = self.extract_processed_next_data(html_content)
        
        # Outer payload metadata (coords, original URL)
        try:
            page_props = payload.get('props', {}).get('pageProps', {})
            query = page_props.get('query', {})
            search_params = page_props.get('componentProps', {}).get('searchPageStateParams', {}) or page_props.get('searchPageStateParams', {})
            qcoords = (search_params.get('query') or {}).copy() if isinstance(search_params.get('query'), dict) else {}
        except Exception:
            query, qcoords = {}, {}

        # Extract property data using flexible strategies
        property_data = self.extract_property_data_flexible(cache_data)
        
        # Add raw Next.js data for multi-source regex
        property_data['_next_data_raw'] = raw_next_data
        property_data['_next_data_processed'] = processed_next_data
        property_data['_html_content'] = html_content
        # Add outer metadata fallbacks
        if query.get('originalReqUrlPath'):
            property_data['original_url_path'] = query.get('originalReqUrlPath')
        # Coordinates fallbacks
        for k in ['latitude','longitude','lat','lon','lng']:
            if k in qcoords and qcoords[k] is not None:
                property_data[f'coord_{k}'] = qcoords[k]

        # Save JSON snippets for comparison
        self.save_json_snippets(url, html_content, payload, cache_data, property_data)
        
        # Store to database if enabled
        if self.enable_db_storage:
            db_result = self.store_property_to_database(property_data)
            if db_result['success']:
                # Log the specific action taken
                if db_result['action'] == 'insert':
                    logger.info(f"✅ {db_result['details']}")
                elif db_result['action'] == 'update':
                    logger.info(f"🔄 {db_result['details']}")
                elif db_result['action'] == 'no_change':
                    logger.warning(f"⚠️ {db_result['details']}")
                
                # Mark database storage success for tracking
                property_data['_database_stored'] = True
                property_data['_db_action'] = db_result['action']
                property_data['_db_details'] = db_result['details']
            else:
                logger.error(f"❌ CRITICAL ERROR: Failed to store property {property_data.get('zpid')} to database")
                logger.error(f"❌ Error details: {db_result['details']}")
                logger.error(f"❌ Stopping extraction due to database storage failure")
                raise Exception(f"Database storage failed for property {property_data.get('zpid')}")
        
        # Track field completion AFTER database storage
        self._track_field_completion(property_data)
        
        return property_data
    
    async def extract_multiple_properties(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Extract multiple properties with timeout handling and progress indicators"""
        logger.info(f"🚀 Starting extraction of {len(urls)} properties")
        start_time = time.time()
        
        results = []
        failed_urls = []
        
        # Use tqdm for progress bar
        with tqdm(total=len(urls), desc="Extracting properties", unit="prop") as pbar:
            for i, url in enumerate(urls, 1):
                logger.info(f"📊 Processing property {i}/{len(urls)}")
                pbar.set_description(f"Processing {i}/{len(urls)}")
                
                try:
                    # Set timeout for each property extraction with recovery
                    extraction_task = asyncio.create_task(self.extract_property(url))
                    try:
                        result = await asyncio.wait_for(extraction_task, timeout=self.timeout_seconds)
                        if result:
                            results.append(result)
                            logger.info(f"✅ Successfully extracted property {i}")
                            pbar.set_postfix({"success": len(results), "failed": len(failed_urls)})
                        else:
                            logger.warning(f"⚠️ Failed to extract property {i} - no result")
                            failed_urls.append(url)
                            pbar.set_postfix({"success": len(results), "failed": len(failed_urls)})
                    except asyncio.TimeoutError:
                        logger.error(f"⏰ Timeout extracting property {i} after {self.timeout_seconds * 2}s")
                        failed_urls.append(url)
                        pbar.set_postfix({"success": len(results), "failed": len(failed_urls)})
                        # Cancel the hanging task
                        extraction_task.cancel()
                        try:
                            await extraction_task
                        except asyncio.CancelledError:
                            pass
                        
                except Exception as e:
                    logger.error(f"❌ Error extracting property {i}: {e}")
                    failed_urls.append(url)
                    pbar.set_postfix({"success": len(results), "failed": len(failed_urls)})
                        
                except Exception as e:
                    logger.error(f"❌ Error extracting property {i}: {e}")
                    failed_urls.append(url)
                    pbar.set_postfix({"success": len(results), "failed": len(failed_urls)})
                
                pbar.update(1)
                
                # Small delay between requests to be respectful
                if i < len(urls):  # Don't delay after the last one
                    await asyncio.sleep(1)
        
        # Calculate timing
        total_time = time.time() - start_time
        success_rate = (len(results) / len(urls)) * 100 if urls else 0
        
        logger.info(f"🎉 Extraction complete in {total_time:.1f}s!")
        logger.info(f"📊 Results: {len(results)}/{len(urls)} successful ({success_rate:.1f}%)")
        if failed_urls:
            logger.warning(f"⚠️ Failed URLs: {len(failed_urls)}")
            for url in failed_urls[:5]:  # Show first 5 failed URLs
                logger.warning(f"  - {url}")
        
        # Save combined results and comprehensive summary under summary dir
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        combined_file = self.summary_dir / f"combined_{ts}.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Saved combined results to {combined_file}")
        
        # Create comprehensive summary
        summary = {
            'extraction_timestamp': datetime.now().isoformat(),
            'total_properties': len(urls),
            'successful_extractions': len(results),
            'failed_extractions': len(failed_urls),
            'success_rate_percent': success_rate,
            'total_time_seconds': total_time,
            'average_time_per_property': total_time / len(urls) if urls else 0,
            'properties_with_waterfront_keywords': len([r for r in results if r.get('waterfront_keywords')]),
            'properties_with_regex_matches': len([r for r in results if any(k.startswith('regex_') for k in r.keys())]),
            'properties_with_extracted_fields': len([r for r in results if any(k.startswith('extracted_') for k in r.keys())]),
            'properties_with_key_waterfront_info': len([r for r in results if any(k.startswith('key_waterfront') for k in r.keys())]),
            'properties_with_value_waterfront_info': len([r for r in results if any(k.startswith('value_waterfront') for k in r.keys())]),
            'total_photos': sum(r.get('photo_count', 0) for r in results),
            'waterfront_features_summary': self._summarize_waterfront_features(results),
            'failed_urls': failed_urls[:10]  # Include first 10 failed URLs for debugging
        }
        
        summary_file = self.summary_dir / f"run_summary_{ts}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Saved summary to {summary_file}")
        
        # Generate and save field completion report
        completion_report = self._generate_completion_report()
        report_file = self.summary_dir / f"field_completion_report_{ts}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(completion_report)
        logger.info(f"✅ Saved field completion report to {report_file}")
        
        # Print the completion report to console
        print("\n" + completion_report)
        
        return results
    
    def _summarize_waterfront_features(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize all waterfront features found across properties"""
        summary = {
            'waterfront_keywords_found': set(),
            'regex_patterns_matched': set(),
            'extracted_fields_found': set(),
            'key_waterfront_info_found': set(),
            'value_waterfront_info_found': set()
        }
        
        for result in results:
            if result.get('waterfront_keywords'):
                summary['waterfront_keywords_found'].update(result['waterfront_keywords'])
            
            for key in result.keys():
                if key.startswith('regex_'):
                    summary['regex_patterns_matched'].add(key)
                elif key.startswith('extracted_'):
                    summary['extracted_fields_found'].add(key)
                elif key.startswith('key_waterfront'):
                    summary['key_waterfront_info_found'].add(key)
                elif key.startswith('value_waterfront'):
                    summary['value_waterfront_info_found'].add(key)
        
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in summary.items()}

    def extract_description_from_html(self, html_content: str) -> Optional[str]:
        """Extract description from HTML meta tags as a fallback"""
        if not html_content:
            return None
        
        try:
            # Look for meta description tags
            meta_patterns = [
                r'<meta\s+name="description"\s+content="([^"]*)"',
                r'<meta\s+property="og:description"\s+content="([^"]*)"',
                r'<meta\s+name="twitter:description"\s+content="([^"]*)"'
            ]
            
            for pattern in meta_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    if description and len(description) > 20:  # Ensure it's substantial
                        return description
            
            # Look for structured data descriptions
            structured_pattern = r'"description"\s*:\s*"([^"]*)"'
            match = re.search(structured_pattern, html_content, re.IGNORECASE)
            if match:
                description = match.group(1).strip()
                if description and len(description) > 20:
                    return description
                    
        except Exception as e:
            logger.warning(f"Error extracting description from HTML: {e}")
        
        return None

    def _safe_convert_for_db(self, value: Any) -> Any:
        """
        Safely convert values for database storage, handling complex types
        """
        if value is None:
            return None
        
        # Handle boolean values that might need to be integers
        if isinstance(value, bool):
            return 1 if value else 0
        
        # Handle numeric strings
        if isinstance(value, str):
            # Try to convert to appropriate numeric type
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value
        
        # Convert complex types to JSON strings (but handle rent_zestimate specially)
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError):
                return str(value)
        
        return value

    def _safe_convert_rent_zestimate(self, value: Any) -> Any:
        """
        Special handling for rent_zestimate field - extract numeric value if possible
        """
        if value is None or value is False:
            return None
        
        # If it's a dict with a numeric value, try to extract it
        if isinstance(value, dict):
            # Look for common numeric fields in rent_zestimate
            for key in ['value', 'amount', 'price', 'rent']:
                if key in value and isinstance(value[key], (int, float)):
                    return value[key]
            # If no numeric value found, return None since DB expects integer
            return None
        
        # If it's already a number, return it
        if isinstance(value, (int, float)):
            return value
        
        # If it's a string, try to convert to number
        if isinstance(value, str):
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return None
        
        return None

    def _prepare_data_for_db(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare property data for safe database insertion"""
        db_data = {}
        for key, value in property_data.items():
            db_data[key] = self._safe_convert_for_db(value)
        return db_data

    def _retry_failed_database_insertion(self, property_data: Dict[str, Any]) -> bool:
        """Retry failed database insertion with additional error handling"""
        try:
            # Try to store again with enhanced error handling
            success = self.store_property_to_database(property_data)
            if success:
                logger.info(f"✅ Successfully recovered database insertion for {property_data.get('zpid')}")
                return True
            else:
                logger.error(f"❌ Failed to recover database insertion for {property_data.get('zpid')}")
                return False
        except Exception as e:
            logger.error(f"❌ Error during database insertion recovery for {property_data.get('zpid')}: {e}")
            return False

    def _extract_and_store_with_recovery(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract property data with database storage recovery mechanism"""
        try:
            # Extract the property data
            result = self.extract_property_data_flexible_from_url(url)
            if not result:
                logger.warning(f"⚠️ No data extracted from {url}")
                return None
            
            # Try to store to database
            db_success = self.store_property_to_database(result)
            if db_success:
                logger.info(f"✅ Successfully stored {result.get('zpid')} to database")
                return result
            else:
                logger.warning(f"⚠️ Database storage failed for {result.get('zpid')}, attempting recovery...")
                # Try recovery
                recovery_success = self._retry_failed_database_insertion(result)
                if recovery_success:
                    logger.info(f"✅ Database recovery successful for {result.get('zpid')}")
                    return result
                else:
                    logger.error(f"❌ Database recovery failed for {result.get('zpid')}, data saved to files only")
                    # Data is still saved to files, so we return the result
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Error in extract_and_store_with_recovery for {url}: {e}")
            return None

    def _extract_reso_facts_via_regex(self, html_content: str, next_data_raw: str, next_data_processed: str) -> Optional[str]:
        """
        Extract the entire resoFacts category using regex patterns across multiple data sources
        Priority: HTML content > processed Next.js data > raw Next.js data
        """
        # Multiple patterns to find resoFacts in different formats
        reso_facts_patterns = [
            # Pattern 1: Look for "resoFacts": { ... } in JSON
            r'"resoFacts"\s*:\s*\{[^}]*\}',
            # Pattern 2: Look for resoFacts with nested content
            r'"resoFacts"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            # Pattern 3: Look for resoFacts in HTML content
            r'resoFacts[^>]*>([^<]*)',
            # Pattern 4: Look for resoFacts in processed data
            r'resoFacts[^}]*\}',
            # Pattern 5: Look for resoFacts in raw data (with escaping)
            r'resoFacts[^}]*\}'
        ]
        
        # Try HTML content first (cleanest)
        if html_content:
            for pattern in reso_facts_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    logger.info(f"✅ ResoFacts found in HTML content using pattern: {pattern[:50]}...")
                    return match.group(0)
        
        # Try processed Next.js data
        if next_data_processed:
            for pattern in reso_facts_patterns:
                match = re.search(pattern, next_data_processed, re.IGNORECASE | re.DOTALL)
                if match:
                    logger.info(f"✅ ResoFacts found in processed Next.js data using pattern: {pattern[:50]}...")
                    return match.group(0)
        
        # Try raw Next.js data (last resort)
        if next_data_raw:
            for pattern in reso_facts_patterns:
                match = re.search(pattern, next_data_raw, re.IGNORECASE | re.DOTALL)
                if match:
                    logger.info(f"✅ ResoFacts found in raw Next.js data using pattern: {pattern[:50]}...")
                    return match.group(0)
        
        logger.warning("⚠️ ResoFacts not found in any data source")
        return None

    def process_existing_cache_files(self, cache_dir: str = "data/cache", update_existing: bool = True) -> Dict[str, Any]:
        """
        Process existing cache files to extract data and update database records
        
        Args:
            cache_dir: Directory containing cache files
            update_existing: Whether to update existing database records
            
        Returns:
            Summary of processing results
        """
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            logger.error(f"❌ Cache directory not found: {cache_dir}")
            return {}
        
        # Find all cache files
        cache_files = list(cache_path.glob("*.json"))
        logger.info(f"🔍 Found {len(cache_files)} cache files in {cache_dir}")
        
        if not cache_files:
            logger.warning("⚠️ No cache files found")
            return {}
        
        results = {
            'total_files': len(cache_files),
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'details': []
        }
        
        # Process each cache file
        for cache_file in tqdm(cache_files, desc="Processing cache files"):
            try:
                file_result = self._process_single_cache_file(cache_file, update_existing)
                if file_result:
                    results['processed'] += 1
                    if file_result.get('updated'):
                        results['updated'] += 1
                    results['details'].append(file_result)
                else:
                    results['errors'] += 1
            except Exception as e:
                logger.error(f"❌ Error processing {cache_file.name}: {e}")
                results['errors'] += 1
        
        logger.info(f"🎉 Cache processing complete: {results['processed']} processed, {results['updated']} updated, {results['errors']} errors")
        return results

    def _process_single_cache_file(self, cache_file: Path, update_existing: bool) -> Optional[Dict[str, Any]]:
        """
        Process a single cache file and extract property data
        
        Args:
            cache_file: Path to cache file
            update_existing: Whether to update existing database records
            
        Returns:
            Processing result summary
        """
        try:
            # Extract ZPID from filename
            zpid = cache_file.stem.split('_')[0]
            logger.info(f"🔍 Processing cache file: {cache_file.name} (ZPID: {zpid})")
            
            # Read and parse cache file
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Extract property data from cache
            property_data = self.extract_property_data_flexible_from_cache(cache_data)
            if not property_data:
                logger.warning(f"⚠️ No property data extracted from {cache_file.name}")
                return None
            
            # Ensure ZPID is set
            property_data['zpid'] = zpid
            
            # Check if record exists in database
            existing_record = self._check_existing_record(zpid)
            
            if existing_record and update_existing:
                # Update existing record with missing fields
                update_result = self._update_existing_record(zpid, property_data)
                if update_result:
                    logger.info(f"✅ Updated existing record for ZPID {zpid}")
                    return {
                        'zpid': zpid,
                        'file': cache_file.name,
                        'updated': True,
                        'fields_updated': update_result
                    }
                else:
                    logger.warning(f"⚠️ Failed to update existing record for ZPID {zpid}")
                    return {
                        'zpid': zpid,
                        'file': cache_file.name,
                        'updated': False,
                        'error': 'Update failed'
                    }
            else:
                # Insert new record
                if self.enable_db_storage:
                    insert_success = self.store_property_to_database(property_data)
                    if insert_success:
                        logger.info(f"✅ Inserted new record for ZPID {zpid}")
                        return {
                            'zpid': zpid,
                            'file': cache_file.name,
                            'updated': False,
                            'inserted': True
                        }
                    else:
                        logger.warning(f"⚠️ Failed to insert new record for ZPID {zpid}")
                        return {
                            'zpid': zpid,
                            'file': cache_file.name,
                            'updated': False,
                            'inserted': False,
                            'error': 'Insert failed'
                        }
                else:
                    logger.info(f"📝 Database storage disabled, skipping insert for ZPID {zpid}")
                    return {
                        'zpid': zpid,
                        'file': cache_file.name,
                        'updated': False,
                        'inserted': False,
                        'note': 'Database storage disabled'
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error processing {cache_file.name}: {e}")
            return None

    def extract_property_data_flexible_from_cache(self, cache_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract property data from cache file using enhanced extraction logic
        
        Args:
            cache_data: Parsed cache data
            
        Returns:
            Extracted property data dictionary
        """
        try:
            # Initialize property data
            property_data = {}
            
            # Find the property object in the GraphQL structure
            property_obj = None
            for key, value in cache_data.items():
                if isinstance(value, dict) and 'property' in value:
                    property_obj = value['property']
                    break
            
            if not property_obj:
                logger.warning("⚠️ No property object found in cache data")
                return None
            
            # Extract core fields from property object
            property_data.update({
                'zpid': property_obj.get('zpid'),
                'address': self._extract_address(property_obj),
                'price': property_obj.get('price'),
                'bedrooms': property_obj.get('bedrooms'),
                'bathrooms': property_obj.get('bathrooms'),
                'livingArea': property_obj.get('livingArea'),
                'title': property_obj.get('title'),
                'property_subtype': property_obj.get('propertySubType', []),
                'home_type': property_obj.get('homeType'),
                'property_type_dimension': property_obj.get('propertyTypeDimension'),
                'lot_area_value': property_obj.get('lotAreaValue'),
                'lot_area_units': property_obj.get('lotAreaUnits'),
                'lot_size_acres': property_obj.get('lotSize'),
                'price_per_sqft': property_obj.get('pricePerSquareFoot'),
                'monthly_hoa_fee': int(property_obj.get('monthlyHoaFee')) if property_obj.get('monthlyHoaFee') and isinstance(property_obj.get('monthlyHoaFee'), (int, float)) else None,
                'hoa_fee': None,  # Will be set from resoFacts if available, otherwise from monthlyHoaFee
                'rent_zestimate': property_obj.get('rentZestimate'),
                'days_on_zillow': property_obj.get('daysOnZillow'),
                'page_view_count': property_obj.get('pageViewCount'),
                'favorite_count': property_obj.get('favoriteCount'),
                'home_status': property_obj.get('homeStatus'),
                'contingent_type': property_obj.get('contingentType'),
                'listing_provider': property_obj.get('listingProvider'),
                'on_market_date': property_obj.get('onMarketDate'),
                'ownership_type': property_obj.get('ownershipType'),
                'parcel_number': property_obj.get('parcelNumber'),
                'description': property_obj.get('description'),
                'what_i_love': property_obj.get('whatILove'),
                'time_on_zillow': property_obj.get('timeOnZillow'),
                'selling_soon': property_obj.get('sellingSoon'),
                'mlsid': property_obj.get('mlsid'),
                'ouid': property_obj.get('ouid'),
                'time_zone': property_obj.get('timeZone'),
                'is_premier_builder': property_obj.get('isPremierBuilder'),
                'hi_res_image_link': property_obj.get('hiResImageLink'),
                'currency': property_obj.get('currency'),
                'listing_feed_id': property_obj.get('listingFeedID'),
                'ssid': property_obj.get('ssid'),
                'listing_sub_type': property_obj.get('listing_sub_type'),
                'coming_soon_on_market_date': property_obj.get('comingSoonOnMarketDate'),
                'is_preforeclosure_auction': property_obj.get('isPreforeclosureAuction'),
                'city_id': property_obj.get('cityId'),
                'state_id': property_obj.get('stateId'),
                'borough_id': property_obj.get('boroughId'),
                'county_id': property_obj.get('countyId'),
                'property_tax_rate': property_obj.get('propertyTaxRate'),
                'city': property_obj.get('city'),
                'state': property_obj.get('state'),
                'zipcode': property_obj.get('zipcode'),
                'county': property_obj.get('county') or property_obj.get('cnty') or (property_obj.get('adTargets', {}).get('cnty') if property_obj.get('adTargets') else None),
                'latitude': property_obj.get('latitude'),
                'longitude': property_obj.get('longitude'),
                'url': property_obj.get('hdpUrl'),
            })
            
            # Extract resoFacts data (this is where the enhanced extraction happens)
            reso_facts = property_obj.get('resoFacts', {})
            if reso_facts:
                property_data.update({
                    'year_built': reso_facts.get('yearBuilt'),
                    'property_subtype': reso_facts.get('propertySubType', []),
                    'lot_size': reso_facts.get('lotSize'),
                    'price_per_sqft': reso_facts.get('pricePerSquareFoot'),
                    'home_type': reso_facts.get('homeType'),
                    'parking_capacity': reso_facts.get('parkingCapacity'),
                    'parking_info': f"Capacity: {reso_facts.get('parkingCapacity')}" if reso_facts.get('parkingCapacity') else None,
                    'parking_features': reso_facts.get('parkingFeatures'),
                    'has_garage': reso_facts.get('hasGarage'),
                    'has_carport': reso_facts.get('hasCarport'),
                    'has_attached_garage': reso_facts.get('hasAttachedGarage'),
                    'garage_parking_capacity': reso_facts.get('garageParkingCapacity'),
                    'carport_parking_capacity': reso_facts.get('carportParkingCapacity'),
                    'covered_parking_capacity': reso_facts.get('coveredParkingCapacity'),
                    'open_parking_capacity': reso_facts.get('openParkingCapacity'),
                    'hoa_fee': reso_facts.get('hoaFee') or reso_facts.get('associationFee'),
                })
                
                # Store the entire resoFacts object
                property_data['reso_facts'] = json.dumps(reso_facts, ensure_ascii=False)
                property_data['reso_facts_preview'] = str(reso_facts)[:500]
                
                logger.info(f"✅ Found resoFacts with yearBuilt: {reso_facts.get('yearBuilt')}")
            
            # Set HOA fee: prioritize text description from resoFacts, fallback to monthly amount
            if not property_data.get('hoa_fee') and property_data.get('monthly_hoa_fee'):
                property_data['hoa_fee'] = f"${property_data['monthly_hoa_fee']}/month"
                logger.info(f"🔍 Set HOA fee from monthly amount: {property_data['hoa_fee']}")
            
            # Extract attribution info (MLS, agent, etc.)
            attribution_info = property_obj.get('attributionInfo', {})
            if attribution_info:
                property_data.update({
                    'mls_id': attribution_info.get('mlsId'),
                    'mls_name': attribution_info.get('mlsName'),
                    'listing_agent': attribution_info.get('agentName'),
                    'listing_agent_phone': attribution_info.get('agentPhoneNumber'),
                    'listing_office': attribution_info.get('brokerName'),
                })
                
                logger.info(f"✅ Found attribution info: MLS {attribution_info.get('mlsId')} - Agent {attribution_info.get('agentName')}")
            
            # Extract photo information
            photos = property_obj.get('photos', [])
            if photos:
                property_data['photo_urls'] = len(photos)
                # Store detailed photo info if needed
                photo_details = []
                for photo in photos:
                    if isinstance(photo, dict):
                        photo_details.append({
                            'url': photo.get('url'),
                            'caption': photo.get('caption'),
                            'subject_type': photo.get('subjectType')
                        })
                property_data['photo_details'] = json.dumps(photo_details, ensure_ascii=False)
                
                logger.info(f"✅ Found {len(photos)} photos")
            
            # Extract price history
            price_history = property_obj.get('priceHistory', [])
            if price_history:
                property_data['price_history'] = json.dumps(price_history, ensure_ascii=False)
                logger.info(f"✅ Found price history with {len(price_history)} entries")
            
            # Extract tax history
            tax_history = property_obj.get('taxHistory', [])
            if tax_history:
                property_data['tax_history'] = json.dumps(tax_history, ensure_ascii=False)
                logger.info(f"✅ Found tax history with {len(tax_history)} entries")
            
            # Extract schools
            schools = property_obj.get('schools', [])
            if schools:
                property_data['schools'] = json.dumps(schools, ensure_ascii=False)
            
            # Extract parking info (use resoFacts.parkingCapacity if available, otherwise fallback to parkingInfo)
            if not property_data.get('parking_info'):
                parking_info = property_obj.get('parkingInfo', [])
                if parking_info:
                    property_data['parking_info'] = json.dumps(parking_info, ensure_ascii=False)
            
            # Extract waterfront-specific fields
            property_data.update({
                'dock_info': self._extract_dock_info(property_data.get('description', '')),
                'bridge_height': self._extract_bridge_height(property_data.get('description', '')),
                'water_depth': self._extract_water_depth(property_data.get('description', '')),
                'canal_info': self._extract_canal_info(property_data.get('description', '')),
                'ocean_access': self._extract_ocean_access(property_data.get('description', '')),
            })
            
            # Log successful extraction
            logger.info(f"✅ Extracted {len(property_data)} fields from cache file")
            
            return property_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting property data from cache: {e}")
            return None

    def _check_existing_record(self, zpid: str) -> bool:
        """
        Check if a record exists in the database
        
        Args:
            zpid: Property ZPID
            
        Returns:
            True if record exists, False otherwise
        """
        if not self.enable_db_storage:
            return False
        
        try:
            engine = create_engine(os.getenv('DATABASE_URL'))
            with engine.connect() as conn:
                # Check both tables
                result = conn.execute(text("SELECT zpid FROM listings_summary WHERE zpid = :zpid"), {"zpid": zpid})
                if result.fetchone():
                    return True
                
                result = conn.execute(text("SELECT zpid FROM listings_detail WHERE zpid = :zpid"), {"zpid": zpid})
                if result.fetchone():
                    return True
                
                return False
        except Exception as e:
            logger.error(f"❌ Error checking existing record for ZPID {zpid}: {e}")
            return False

    def _update_existing_record(self, zpid: str, property_data: Dict[str, Any]) -> bool:
        """
        Update existing database record with new data, handling errors gracefully
        """
        if not self.enable_db_storage:
            return False
        
        try:
            # Update summary table
            summary_updates = 0
            detail_updates = 0
            
            # Process summary fields
            for field_name, value in property_data.items():
                if field_name.startswith('_') or field_name in ['zpid', 'url']:
                    continue
                
                # Check if field exists in summary table
                if field_name in self.summary_fields:
                    try:
                        safe_value = self._safe_convert_for_db(value)
                        if safe_value is not None:
                            with self.db_engine.connect() as conn:
                                result = conn.execute(
                                    text(f"UPDATE listings_summary SET {field_name} = :value, updated_at = NOW() WHERE zpid = :zpid"),
                                    {"value": safe_value, "zpid": zpid}
                                )
                                conn.commit()  # Explicitly commit the transaction
                                if result.rowcount > 0:
                                    summary_updates += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to update {field_name} in summary: {e}")
                        continue
            
            # Process detail fields
            for field_name, value in property_data.items():
                if field_name.startswith('_') or field_name in ['zpid', 'url']:
                    continue
                
                # Check if field exists in detail table
                if field_name in self.detail_fields:
                    try:
                        safe_value = self._safe_convert_for_db(value)
                        if safe_value is not None:
                            with self.db_engine.connect() as conn:
                                result = conn.execute(
                                    text(f"UPDATE listings_detail SET {field_name} = :value, updated_at = NOW() WHERE zpid = :zpid"),
                                    {"value": safe_value, "zpid": zpid}
                                )
                                conn.commit()  # Explicitly commit the transaction
                                if result.rowcount > 0:
                                    detail_updates += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to update {field_name} in detail: {e}")
                        continue
            
            logger.info(f"✅ Updated {summary_updates} summary + {detail_updates} detail fields for ZPID {zpid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update existing record for ZPID {zpid}: {e}")
            return False

    def _get_summary_updates(self, zpid: str, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get fields that need to be updated in listings_summary table
        
        Args:
            zpid: Property ZPID
            property_data: New property data
            
        Returns:
            Dictionary of field: value pairs to update
        """
        try:
            engine = create_engine(os.getenv('DATABASE_URL'))
            updates = {}
            
            with engine.connect() as conn:
                # Get current values
                result = conn.execute(text("SELECT * FROM listings_summary WHERE zpid = :zpid"), {"zpid": zpid})
                current = result.fetchone()
                
                if not current:
                    return {}
                
                # Check which fields need updating
                summary_fields = [
                    'address', 'beds', 'baths', 'home_size_sqft', 'price', 'price_formatted',
                    'price_per_sqft', 'home_type', 'home_status', 'is_waterfront', 'is_condo',
                    'latitude', 'longitude', 'city', 'state', 'zip_code', 'county',
                    'days_on_zillow', 'favorite_count', 'page_view_count', 'zestimate',
                    'rent_zestimate', 'hoa_fee', 'monthly_hoa_fee', 'contingent_type',
                    'listing_provider', 'lot_area_value', 'lot_area_units', 'lot_area_unit',
                    'mls_id', 'mls_name', 'year_built', 'property_type_dimension'
                ]
                
                for field in summary_fields:
                    if field in property_data and property_data[field] is not None:
                        current_value = getattr(current, field, None)
                        new_value = property_data[field]
                        
                        # Only update if value is different and new value is not None
                        if current_value != new_value and new_value is not None:
                            updates[field] = new_value
            
            return updates
            
        except Exception as e:
            logger.error(f"❌ Error getting summary updates for ZPID {zpid}: {e}")
            return {}

    def _get_detail_updates(self, zpid: str, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get fields that need to be updated in listings_detail table
        
        Args:
            zpid: Property ZPID
            property_data: New property data
            
        Returns:
            Dictionary of field: value pairs to update
        """
        try:
            engine = create_engine(os.getenv('DATABASE_URL'))
            updates = {}
            
            with engine.connect() as conn:
                # Get current values
                result = conn.execute(text("SELECT * FROM listings_detail WHERE zpid = :zpid"), {"zpid": zpid})
                current = result.fetchone()
                
                if not current:
                    return {}
                
                # Check which fields need updating
                detail_fields = [
                    'description_raw', 'description_preview', 'dock_info', 'bridge_height',
                    'water_depth', 'canal_info', 'ocean_access', 'water_view',
                    'waterfront_features', 'view', 'rooms', 'schools', 'schools_preview',
                    'parking_info', 'parking_info_preview', 'living_area', 'living_area_units',
                    'living_area_value', 'lot_size_acres', 'mls_number', 'listing_agent',
                    'listing_agent_phone', 'listing_office', 'on_market_date',
                    'ownership_type', 'parcel_number', 'property_subtype', 'price_history',
                    'price_history_preview', 'tax_history', 'tax_history_preview',
                    'reso_facts', 'reso_facts_preview', 'boat_access'
                ]
                
                for field in detail_fields:
                    if field in property_data and property_data[field] is not None:
                        current_value = getattr(current, field, None)
                        new_value = property_data[field]
                        
                        # Only update if value is different and new value is not None
                        if current_value != new_value and new_value is not None:
                            updates[field] = new_value
            
            return updates
            
        except Exception as e:
            logger.error(f"❌ Error getting detail updates for ZPID {zpid}: {e}")
            return {}

    def _extract_address(self, property_obj: Dict[str, Any]) -> Optional[str]:
        """Extract formatted address from property object"""
        address = property_obj.get('address', {})
        if address:
            street = address.get('streetAddress', '')
            city = address.get('city', '')
            state = address.get('state', '')
            zipcode = address.get('zipcode', '')
            
            if street and city and state:
                return f"{street}, {city}, {state} {zipcode}".strip()
        return None
    
    def _extract_dock_info(self, description: str) -> Optional[str]:
        """Extract dock information from description"""
        dock_patterns = [
            r'dock[^.]*\.',
            r'boat\s+slip[^.]*\.',
            r'waterfront\s+access[^.]*\.',
            r'boat\s+ramp[^.]*\.',
            r'pier[^.]*\.',
            r'wharf[^.]*\.'
        ]
        
        for pattern in dock_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _extract_bridge_height(self, description: str) -> Optional[str]:
        """Extract bridge height information from description"""
        bridge_patterns = [
            r'bridge\s+height[^.]*\.',
            r'clearance[^.]*\.',
            r'bridge\s+clearance[^.]*\.'
        ]
        
        for pattern in bridge_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _extract_water_depth(self, description: str) -> Optional[str]:
        """Extract water depth information from description"""
        depth_patterns = [
            r'water\s+depth[^.]*\.',
            r'depth[^.]*\.',
            r'deep\s+water[^.]*\.',
            r'shallow\s+water[^.]*\.'
        ]
        
        for pattern in depth_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _extract_canal_info(self, description: str) -> Optional[str]:
        """Extract canal information from description"""
        canal_patterns = [
            r'canal[^.]*\.',
            r'intracoastal[^.]*\.',
            r'waterway[^.]*\.',
            r'channel[^.]*\.'
        ]
        
        for pattern in canal_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _extract_ocean_access(self, description: str) -> Optional[str]:
        """Extract ocean access information from description"""
        ocean_patterns = [
            r'ocean\s+access[^.]*\.',
            r'oceanfront[^.]*\.',
            r'beach\s+access[^.]*\.',
            r'coastal[^.]*\.'
        ]
        
        for pattern in ocean_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

async def main():
    """Main function to extract properties from URLs file or process existing cache files"""
    parser = argparse.ArgumentParser(description='Extract waterfront property data from Zillow URLs or process existing cache files')
    parser.add_argument('--mode', type=str, choices=['urls', 'cache'], required=True, 
                       help='Processing mode: urls (scrape URLs) or cache (process existing files)')
    parser.add_argument('--urls-file', type=str, help='File containing URLs to process (required for urls mode)')
    parser.add_argument('--cache-dir', type=str, default='data/cache',
                       help='Directory containing cache files (default: data/cache)')
    parser.add_argument('--limit', type=int, help='Limit number of properties to process (for testing)')
    parser.add_argument('--max-search-pages', type=int, default=20, 
                       help='Maximum number of search results pages to process (default: 20)')
    parser.add_argument('--max-properties-per-search', type=int, default=1000,
                       help='Maximum number of properties to process from search results (default: 1000)')
    parser.add_argument('--update-existing', action='store_true', default=True,
                       help='Update existing database records with missing fields (default: True)')
    parser.add_argument('--dry-run', action='store_true', default=False,
                       help='Process files without updating database (for testing)')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Timeout in seconds for HTTP requests (default: 300)')
    parser.add_argument('--save-html', action='store_true',
                       help='Save HTML files for each property (default: False)')
    parser.add_argument('--save-processed', action='store_true',
                       help='Save processed data files (default: False)')
    parser.add_argument('--save-next-data', action='store_true',
                       help='Save next-data files (default: False)')
    parser.add_argument('--save-summary', action='store_true',
                       help='Save summary files (default: False)')
    parser.add_argument('--save-cache', action='store_true', default=True,
                       help='Save cache files (default: True)')
    parser.add_argument('--simple', action='store_true', default=False,
                       help='Use simple logging mode with progress counters (default: False)')
    parser.add_argument('--max-concurrent-properties', type=int, default=5,
                       help='Maximum number of properties to process concurrently (default: 5)')
    parser.add_argument('--save-urls-list', action='store_true', default=False,
                       help='Save extracted URLs list to file for later continuation (default: False)')
    parser.add_argument('--continue', dest='continue_from_file', type=str,
                       help='Continue processing from a previously saved URLs file')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = FlexibleWaterfrontExtractor(
        enable_db_storage=not args.dry_run, 
        cache_mode=(args.mode == 'cache'), 
        timeout_seconds=args.timeout,
        max_search_pages=args.max_search_pages,
        max_properties_per_search=args.max_properties_per_search,
        save_html=args.save_html,
        save_processed=args.save_processed,
        save_next_data=args.save_next_data,
        save_summary=args.save_summary,
        save_cache=args.save_cache,
        simple_logging=args.simple,
        max_concurrent_properties=args.max_concurrent_properties,
        save_urls_list=args.save_urls_list,
        continue_from_file=args.continue_from_file
    )
    
    if args.mode == 'urls':
        await _process_urls_mode(extractor, args)
    elif args.mode == 'cache':
        await _process_cache_mode(extractor, args)
    else:
        logger.error(f"❌ Invalid mode: {args.mode}")

async def _process_urls_mode(extractor: FlexibleWaterfrontExtractor, args):
    """Process URLs mode - scrape properties from URLs"""
    if not args.urls_file and not args.continue_from_file:
        logger.error("❌ Either --urls-file or --continue is required for urls mode")
        return
    
    # Read URLs from file or continue from saved file
    if args.continue_from_file:
        # Continue from saved URLs file
        urls = extractor._load_urls_from_file(args.continue_from_file)
        if not urls:
            logger.error(f"❌ No URLs found in {args.continue_from_file}")
            return
        logger.info(f"🔄 Continuing from saved URLs file: {args.continue_from_file}")
    else:
        # Read URLs from specified file
        try:
            with open(args.urls_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"📖 Loaded {len(urls)} URLs from {args.urls_file}")
        except FileNotFoundError:
            logger.error(f"❌ URLs file not found: {args.urls_file}")
            return
        except Exception as e:
            logger.error(f"❌ Error reading URLs file: {e}")
            return
    
    # Apply limit if specified
    if args.limit:
        urls = urls[:args.limit]
        logger.info(f"🔢 Limited to {len(urls)} URLs for testing")
    
    if not urls:
        logger.error("❌ No URLs to process")
        return
    
    # Process URLs
    logger.info(f"🚀 Starting URL processing mode with {len(urls)} URLs")
    results = await extractor.extract_multiple_properties(urls)
    
    logger.info(f"🎉 URL processing complete! Processed {len(results)} properties")
    for i, result in enumerate(results, 1):
        zpid = result.get('zpid', 'Unknown')
        waterfront_keywords = result.get('waterfront_keywords', [])
        regex_matches = {k: v for k, v in result.items() if k.startswith('regex_')}
        logger.info(f"Property {i} (ZPID: {zpid}):")
        logger.info(f"  Waterfront Keywords: {waterfront_keywords}")
        logger.info(f"  Regex Matches: {regex_matches}")

async def _process_cache_mode(extractor: FlexibleWaterfrontExtractor, args: argparse.Namespace):
    """Process existing cache files in cache mode"""
    logger.info("🔄 Starting cache processing mode...")
    
    # Get cache directory
    cache_dir = args.cache_dir or 'data/cache'
    if not os.path.exists(cache_dir):
        logger.error(f"❌ Cache directory not found: {cache_dir}")
        return
    
    # Get list of cache files
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
    if not cache_files:
        logger.error(f"❌ No cache files found in {cache_dir}")
        return
    
    logger.info(f"📁 Found {len(cache_files)} cache files in {cache_dir}")
    
    # Apply limit if specified
    if args.limit:
        cache_files = cache_files[:args.limit]
        logger.info(f"📊 Processing limited to {len(cache_files)} files")
    
    # Process files
    processed_count = 0
    updated_count = 0
    error_count = 0
    
    with tqdm(total=len(cache_files), desc="Processing cache files") as pbar:
        for cache_file in cache_files:
            try:
                result = extractor._process_single_cache_file(
                    Path(os.path.join(cache_dir, cache_file)),
                    args.update_existing
                )
                
                if result:
                    processed_count += 1
                    if result.get('updated', False):
                        updated_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {cache_file}: {e}")
                error_count += 1
                
            pbar.update(1)
    
    logger.info("🎉 Cache processing complete!")
    logger.info(f"📊 Summary:")
    logger.info(f"  Total files: {len(cache_files)}")
    logger.info(f"  Processed: {processed_count}")
    logger.info(f"  Updated: {updated_count}")
    logger.info(f"  Errors: {error_count}")
    
    # Show sample results if any were processed
    if processed_count > 0:
        logger.info("📋 Sample results:")
        # Get a sample of processed results for display
        sample_results = []
        for cache_file in cache_files[:min(3, len(cache_files))]:
            try:
                with open(os.path.join(cache_dir, cache_file), 'r') as f:
                    data = json.load(f)
                    if data.get('zpid'):
                        sample_results.append({
                            'zpid': data.get('zpid'),
                            'address': data.get('address', 'N/A'),
                            'price': data.get('price', 'N/A')
                        })
            except Exception:
                continue
        
        for result in sample_results:
            logger.info(f"  ZPID {result['zpid']}: {result['address']} - ${result['price']}")

if __name__ == "__main__":
    asyncio.run(main())
