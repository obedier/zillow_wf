#!/usr/bin/env python3
"""
Corrected Database Exploration Script for Zillow Waterfront Properties
Based on the actual database schema discovered.
"""

import psycopg
import json
from datetime import datetime
from typing import Dict, List, Any

class DatabaseExplorer:
    def __init__(self, connection_string: str = 'postgresql://osamabedier@localhost:5432/zillow_wf'):
        self.connection_string = connection_string
        self.conn = None
        self.cur = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg.connect(self.connection_string)
            self.cur = self.conn.cursor()
            print("✅ Connected to database successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        print("🔌 Database connection closed")
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get basic information about tables"""
        print("\n📊 TABLE INFORMATION")
        print("=" * 50)
        
        # Check listings_summary
        self.cur.execute("""
            SELECT COUNT(*) as total_records,
                   COUNT(CASE WHEN is_waterfront = true THEN 1 END) as waterfront_count,
                   COUNT(CASE WHEN is_waterfront = false THEN 1 END) as non_waterfront_count,
                   COUNT(CASE WHEN is_waterfront IS NULL THEN 1 END) as unknown_waterfront
            FROM listings_summary
        """)
        summary_stats = self.cur.fetchone()
        
        # Check listings_detail
        self.cur.execute("SELECT COUNT(*) FROM listings_detail")
        detail_count = self.cur.fetchone()[0]
        
        # Check data freshness
        self.cur.execute("""
            SELECT MIN(created_at) as oldest_record,
                   MAX(created_at) as newest_record,
                   MAX(updated_at) as last_updated
            FROM listings_summary
        """)
        time_stats = self.cur.fetchone()
        
        table_info = {
            'summary_total': summary_stats[0],
            'waterfront_count': summary_stats[1],
            'non_waterfront_count': summary_stats[2],
            'unknown_waterfront': summary_stats[3],
            'detail_total': detail_count,
            'oldest_record': time_stats[0],
            'newest_record': time_stats[1],
            'last_updated': time_stats[2]
        }
        
        print(f"📋 listings_summary: {table_info['summary_total']:,} records")
        print(f"   - Waterfront: {table_info['waterfront_count']:,}")
        print(f"   - Non-waterfront: {table_info['non_waterfront_count']:,}")
        print(f"   - Unknown: {table_info['unknown_waterfront']:,}")
        print(f"📋 listings_detail: {table_info['detail_total']:,} records")
        print(f"📅 Data range: {table_info['oldest_record']} to {table_info['newest_record']}")
        print(f"🔄 Last updated: {table_info['last_updated']}")
        
        return table_info
    
    def analyze_waterfront_properties(self):
        """Analyze waterfront properties in detail"""
        print("\n🌊 WATERFRONT PROPERTIES ANALYSIS")
        print("=" * 50)
        
        # Basic waterfront stats
        self.cur.execute("""
            SELECT 
                COUNT(*) as total_waterfront,
                COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as with_price,
                COUNT(CASE WHEN beds IS NOT NULL THEN 1 END) as with_beds,
                COUNT(CASE WHEN baths IS NOT NULL THEN 1 END) as with_baths
            FROM listings_summary 
            WHERE is_waterfront = true
        """)
        waterfront_stats = self.cur.fetchone()
        
        if waterfront_stats[0] > 0:
            print(f"💧 Waterfront Properties Found: {waterfront_stats[0]:,}")
            print(f"   - With Price: {waterfront_stats[1]:,}")
            print(f"   - With Bedrooms: {waterfront_stats[2]:,}")
            print(f"   - With Bathrooms: {waterfront_stats[3]:,}")
        else:
            print("💧 No waterfront properties found in the database")
        
        # Check if there are any properties marked as waterfront
        self.cur.execute("""
            SELECT COUNT(*) as waterfront_count
            FROM listings_summary 
            WHERE is_waterfront = true
        """)
        waterfront_count = self.cur.fetchone()[0]
        
        if waterfront_count == 0:
            print("\n⚠️  NOTE: No properties are currently marked as waterfront")
            print("   This could mean:")
            print("   - The waterfront extraction hasn't run yet")
            print("   - The waterfront detection logic needs adjustment")
            print("   - Properties need to be re-processed")
    
    def analyze_data_quality(self):
        """Analyze data quality and completeness"""
        print("\n🔍 DATA QUALITY ANALYSIS")
        print("=" * 50)
        
        # Field completion rates for key fields
        fields_to_check = [
            ('price', 'price IS NOT NULL'),
            ('beds', 'beds IS NOT NULL'),
            ('baths', 'baths IS NOT NULL'),
            ('home_size_sqft', 'home_size_sqft IS NOT NULL'),
            ('latitude', 'latitude IS NOT NULL'),
            ('longitude', 'longitude IS NOT NULL'),
            ('zestimate', 'zestimate IS NOT NULL'),
            ('rent_zestimate', 'rent_zestimate IS NOT NULL'),
            ('year_built', 'year_built IS NOT NULL'),
            ('is_waterfront', 'is_waterfront IS NOT NULL')
        ]
        
        total_records = self.cur.execute("SELECT COUNT(*) FROM listings_summary").fetchone()[0]
        
        print("📊 Field Completion Rates:")
        for field, condition in fields_to_check:
            self.cur.execute(f"SELECT COUNT(*) FROM listings_summary WHERE {condition}")
            completed = self.cur.fetchone()[0]
            completion_rate = (completed / total_records) * 100
            print(f"   {field}: {completion_rate:.1f}% ({completed:,}/{total_records:,})")
        
        # Check for data inconsistencies
        print(f"\n⚠️  Data Quality Issues:")
        
        # Properties with extreme prices
        self.cur.execute("""
            SELECT COUNT(*) FROM listings_summary 
            WHERE price > 10000000 OR price < 10000
        """)
        extreme_prices = self.cur.fetchone()[0]
        if extreme_prices > 0:
            print(f"   Properties with extreme prices (<$10k or >$10M): {extreme_prices:,}")
        
        # Properties with missing coordinates
        self.cur.execute("""
            SELECT COUNT(*) FROM listings_summary 
            WHERE latitude IS NULL OR longitude IS NULL
        """)
        missing_coords = self.cur.fetchone()[0]
        if missing_coords > 0:
            print(f"   Properties missing coordinates: {missing_coords:,}")
    
    def analyze_market_trends(self):
        """Analyze market trends and patterns"""
        print("\n📈 MARKET TRENDS ANALYSIS")
        print("=" * 50)
        
        # Price distribution by property type
        self.cur.execute("""
            SELECT home_type, COUNT(*) as count, AVG(price) as avg_price
            FROM listings_summary 
            WHERE home_type IS NOT NULL AND price IS NOT NULL
            GROUP BY home_type 
            ORDER BY avg_price DESC
        """)
        home_types = self.cur.fetchall()
        
        if home_types:
            print("🏠 Home Type Analysis:")
            for home_type, count, avg_price in home_types:
                print(f"   {home_type}: {count:,} properties (avg: ${avg_price:,.0f})")
        
        # Days on market analysis
        self.cur.execute("""
            SELECT 
                CASE 
                    WHEN days_on_zillow <= 30 THEN '0-30 days'
                    WHEN days_on_zillow <= 90 THEN '31-90 days'
                    WHEN days_on_zillow <= 180 THEN '91-180 days'
                    ELSE '180+ days'
                END as market_time,
                COUNT(*) as property_count,
                AVG(price) as avg_price
            FROM listings_summary 
            WHERE days_on_zillow IS NOT NULL AND price IS NOT NULL
            GROUP BY market_time
            ORDER BY 
                CASE market_time
                    WHEN '0-30 days' THEN 1
                    WHEN '31-90 days' THEN 2
                    WHEN '91-180 days' THEN 3
                    ELSE 4
                END
        """)
        market_timing = self.cur.fetchall()
        
        if market_timing:
            print(f"\n⏰ Days on Market Analysis:")
            for timing, count, avg_price in market_timing:
                print(f"   {timing}: {count:,} properties (avg: ${avg_price:,.0f})")
    
    def analyze_geographic_distribution(self):
        """Analyze geographic distribution of properties"""
        print("\n🗺️  GEOGRAPHIC DISTRIBUTION")
        print("=" * 50)
        
        # Properties by state
        self.cur.execute("""
            SELECT state, COUNT(*) as count, AVG(price) as avg_price
            FROM listings_summary 
            WHERE state IS NOT NULL
            GROUP BY state 
            ORDER BY count DESC 
            LIMIT 10
        """)
        state_stats = self.cur.fetchall()
        
        if state_stats:
            print("🏛️  Top States by Property Count:")
            for state, count, avg_price in state_stats:
                print(f"   {state}: {count:,} properties (avg: ${avg_price:,.0f})")
        
        # Properties by city
        self.cur.execute("""
            SELECT city, state, COUNT(*) as count, AVG(price) as avg_price
            FROM listings_summary 
            WHERE city IS NOT NULL AND state IS NOT NULL
            GROUP BY city, state 
            ORDER BY count DESC 
            LIMIT 10
        """)
        city_stats = self.cur.fetchall()
        
        if city_stats:
            print(f"\n🏙️  Top Cities by Property Count:")
            for city, state, count, avg_price in city_stats:
                print(f"   {city}, {state}: {count:,} properties (avg: ${avg_price:,.0f})")
    
    def show_sample_properties(self, limit: int = 5):
        """Show sample properties for inspection"""
        print(f"\n🔍 SAMPLE PROPERTIES (showing {limit})")
        print("=" * 50)
        
        self.cur.execute("""
            SELECT zpid, address, city, state, price, beds, baths, 
                   home_size_sqft, is_waterfront, created_at
            FROM listings_summary 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        
        properties = self.cur.fetchall()
        
        for i, prop in enumerate(properties, 1):
            print(f"\n{i}. ZPID: {prop[0]}")
            print(f"   Address: {prop[1]}, {prop[2]}, {prop[3]}")
            print(f"   Price: ${prop[4]:,.0f}" if prop[4] else "   Price: Not available")
            print(f"   Beds/Baths: {prop[5]}/{prop[6]}" if prop[5] and prop[6] else "   Beds/Baths: Not available")
            print(f"   Size: {prop[7]:,} sqft" if prop[7] else "   Size: Not available")
            print(f"   Waterfront: {'Yes' if prop[8] else 'No' if prop[8] is False else 'Unknown'}")
            print(f"   Added: {prop[9]}")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\n📋 COMPREHENSIVE SUMMARY REPORT")
        print("=" * 50)
        
        # Overall statistics
        self.cur.execute("""
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN is_waterfront = true THEN 1 END) as waterfront_properties,
                ROUND(AVG(price), 2) as avg_price_all,
                ROUND(AVG(CASE WHEN is_waterfront = true THEN price END), 2) as avg_price_waterfront,
                COUNT(DISTINCT state) as states_covered,
                COUNT(DISTINCT city) as cities_covered
            FROM listings_summary
        """)
        overall_stats = self.cur.fetchone()
        
        print(f"📊 Overall Statistics:")
        print(f"   Total Properties: {overall_stats[0]:,}")
        print(f"   Waterfront Properties: {overall_stats[1]:,}")
        if overall_stats[0] > 0:
            waterfront_percentage = (overall_stats[1]/overall_stats[0]*100)
            print(f"   Waterfront Percentage: {waterfront_percentage:.1f}%")
        print(f"   Average Price (All): ${overall_stats[2]:,.0f}" if overall_stats[2] else "   Average Price (All): Not available")
        print(f"   Average Price (Waterfront): ${overall_stats[3]:,.0f}" if overall_stats[3] else "   Average Price (Waterfront): Not available")
        print(f"   States Covered: {overall_stats[4]}")
        print(f"   Cities Covered: {overall_stats[5]}")
        
        # Data freshness
        self.cur.execute("""
            SELECT 
                MAX(created_at) as latest_data,
                COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_additions
            FROM listings_summary
        """)
        freshness = self.cur.fetchone()
        
        print(f"\n🕒 Data Freshness:")
        print(f"   Latest Data: {freshness[0]}")
        print(f"   Added in Last 7 Days: {freshness[1]:,}")
    
    def run_full_exploration(self):
        """Run the complete database exploration"""
        if not self.connect():
            return
        
        try:
            print("🚀 Starting Database Exploration...")
            print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run all analysis methods
            self.get_table_info()
            self.analyze_waterfront_properties()
            self.analyze_data_quality()
            self.analyze_market_trends()
            self.analyze_geographic_distribution()
            self.show_sample_properties()
            self.generate_summary_report()
            
            print("\n✅ Database exploration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during exploration: {e}")
        finally:
            self.disconnect()

def main():
    """Main function to run the database explorer"""
    explorer = DatabaseExplorer()
    explorer.run_full_exploration()

if __name__ == "__main__":
    main()




