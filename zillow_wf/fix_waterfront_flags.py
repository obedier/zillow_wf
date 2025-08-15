#!/usr/bin/env python3
"""
Fix Waterfront Flags Script
Update the is_waterfront field in listings_summary based on data already extracted to listings_detail.
"""

import psycopg
import json
from typing import List, Dict, Any

class WaterfrontFlagFixer:
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
    
    def find_waterfront_properties(self) -> List[Dict[str, Any]]:
        """Find properties that should be marked as waterfront based on detail data"""
        print("🔍 Finding properties with waterfront indicators...")
        
        self.cur.execute("""
            SELECT 
                s.zpid,
                s.address,
                s.city,
                s.state,
                s.price,
                d.waterfront_features,
                d.water_view,
                d.description_raw
            FROM listings_summary s
            JOIN listings_detail d ON s.zpid = d.zpid
            WHERE (d.waterfront_features IS NOT NULL AND d.waterfront_features != '[]' AND d.waterfront_features != 'null')
               OR (d.water_view IS NOT NULL AND d.water_view != 'null')
               OR (d.description_raw IS NOT NULL AND (
                   LOWER(d.description_raw) LIKE '%waterfront%'
                   OR LOWER(d.description_raw) LIKE '%ocean%'
                   OR LOWER(d.description_raw) LIKE '%canal%'
                   OR LOWER(d.description_raw) LIKE '%river%'
                   OR LOWER(d.description_raw) LIKE '%lake%'
                   OR LOWER(d.description_raw) LIKE '%bay%'
                   OR LOWER(d.description_raw) LIKE '%dock%'
                   OR LOWER(d.description_raw) LIKE '%boat%'
                   OR LOWER(d.description_raw) LIKE '%marina%'
               ))
            ORDER BY s.price DESC
        """)
        
        results = self.cur.fetchall()
        waterfront_properties = []
        
        for row in results:
            zpid, address, city, state, price, waterfront_features, water_view, description = row
            
            # Determine waterfront type
            waterfront_type = self._classify_waterfront_type(waterfront_features, water_view, description)
            
            waterfront_properties.append({
                'zpid': zpid,
                'address': address,
                'city': city,
                'state': state,
                'price': price,
                'waterfront_features': waterfront_features,
                'water_view': water_view,
                'waterfront_type': waterfront_type
            })
        
        return waterfront_properties
    
    def _classify_waterfront_type(self, waterfront_features: str, water_view: str, description: str) -> str:
        """Classify the type of waterfront property"""
        if not waterfront_features and not water_view and not description:
            return "Unknown"
        
        # Check for specific waterfront types
        if waterfront_features:
            features_str = str(waterfront_features).lower()
            if 'ocean' in features_str or 'oceanfront' in features_str:
                return "Oceanfront"
            elif 'canal' in features_str:
                return "Canal"
            elif 'river' in features_str:
                return "Riverfront"
            elif 'lake' in features_str:
                return "Lakefront"
            elif 'bay' in features_str:
                return "Bayfront"
            elif 'waterfront' in features_str:
                return "Waterfront"
        
        if water_view:
            view_str = str(water_view).lower()
            if 'ocean' in view_str:
                return "Ocean View"
            elif 'canal' in view_str:
                return "Canal View"
            elif 'water' in view_str:
                return "Water View"
        
        if description:
            desc_str = str(description).lower()
            if 'ocean' in desc_str or 'oceanfront' in desc_str:
                return "Ocean Access"
            elif 'canal' in desc_str:
                return "Canal Access"
            elif 'river' in desc_str:
                return "River Access"
            elif 'lake' in desc_str:
                return "Lake Access"
            elif 'bay' in desc_str:
                return "Bay Access"
            elif 'dock' in desc_str or 'boat' in desc_str:
                return "Boat Access"
        
        return "Waterfront"
    
    def update_waterfront_flags(self, waterfront_properties: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update the is_waterfront field in listings_summary"""
        print(f"🔄 Updating waterfront flags for {len(waterfront_properties)} properties...")
        
        updated_count = 0
        error_count = 0
        
        for prop in waterfront_properties:
            try:
                # Update the is_waterfront flag
                self.cur.execute("""
                    UPDATE listings_summary 
                    SET is_waterfront = true, updated_at = CURRENT_TIMESTAMP
                    WHERE zpid = %s
                """, (prop['zpid'],))
                
                updated_count += 1
                print(f"✅ Updated ZPID {prop['zpid']}: {prop['waterfront_type']} - {prop['address']}")
                
            except Exception as e:
                error_count += 1
                print(f"❌ Error updating ZPID {prop['zpid']}: {e}")
        
        # Commit the changes
        self.conn.commit()
        
        return {
            'updated': updated_count,
            'errors': error_count
        }
    
    def show_waterfront_summary(self, waterfront_properties: List[Dict[str, Any]]):
        """Show a summary of waterfront properties found"""
        print(f"\n🌊 WATERFRONT PROPERTIES SUMMARY")
        print("=" * 60)
        print(f"Total Properties Found: {len(waterfront_properties)}")
        
        # Group by waterfront type
        type_counts = {}
        for prop in waterfront_properties:
            prop_type = prop['waterfront_type']
            type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
        
        print(f"\nWaterfront Types:")
        for prop_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {prop_type}: {count} properties")
        
        # Show top properties by price
        print(f"\nTop 5 Waterfront Properties by Price:")
        sorted_props = sorted(waterfront_properties, key=lambda x: x['price'] or 0, reverse=True)
        for i, prop in enumerate(sorted_props[:5], 1):
            price_str = f"${prop['price']:,}" if prop['price'] else "Price not available"
            print(f"  {i}. ZPID {prop['zpid']}: {prop['address']}, {prop['city']}, {prop['state']}")
            print(f"     {prop['waterfront_type']} - {price_str}")
    
    def run_fix(self):
        """Run the complete waterfront flag fix process"""
        if not self.connect():
            return
        
        try:
            print("🚀 Starting Waterfront Flag Fix Process...")
            
            # Step 1: Find properties with waterfront indicators
            waterfront_properties = self.find_waterfront_properties()
            
            if not waterfront_properties:
                print("❌ No waterfront properties found in detail data")
                return
            
            # Step 2: Show summary
            self.show_waterfront_summary(waterfront_properties)
            
            # Step 3: Update waterfront flags
            results = self.update_waterfront_flags(waterfront_properties)
            
            print(f"\n✅ Waterfront flag fix completed!")
            print(f"📊 Results:")
            print(f"  Properties updated: {results['updated']}")
            print(f"  Errors: {results['errors']}")
            
            # Step 4: Verify the update
            self.cur.execute("SELECT COUNT(*) FROM listings_summary WHERE is_waterfront = true")
            waterfront_count = self.cur.fetchone()[0]
            print(f"  Total waterfront properties in database: {waterfront_count}")
            
        except Exception as e:
            print(f"❌ Error during waterfront flag fix: {e}")
        finally:
            self.disconnect()

def main():
    """Main function to run the waterfront flag fixer"""
    fixer = WaterfrontFlagFixer()
    fixer.run_fix()

if __name__ == "__main__":
    main()




