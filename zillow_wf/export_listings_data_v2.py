#!/usr/bin/env python3
"""
Export Listings Data Script V2
Export specific fields from listings_detail table to a pipe-delimited text file.
Updated to replace '¦' with ';' and handle newlines within fields.
"""

import psycopg
import csv
from typing import List, Dict, Any
from datetime import datetime

class ListingsDataExporterV2:
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
    
    def get_listings_data(self) -> List[Dict[str, Any]]:
        """Get all data from the specified fields in listings_detail table"""
        try:
            self.cur.execute("""
                SELECT 
                    zpid,
                    description_raw,
                    waterfront_features,
                    canal_info,
                    reso_facts
                FROM listings_detail
                ORDER BY zpid
            """)
            
            results = self.cur.fetchall()
            print(f"📊 Found {len(results)} records in listings_detail table")
            
            # Convert to list of dictionaries
            data = []
            for row in results:
                zpid, description_raw, waterfront_features, canal_info, reso_facts = row
                data.append({
                    'zpid': zpid,
                    'description_raw': description_raw or '',
                    'waterfront_features': waterfront_features or '',
                    'canal_info': canal_info or '',
                    'reso_facts': reso_facts or ''
                })
            
            return data
            
        except Exception as e:
            print(f"❌ Error getting listings data: {e}")
            return []
    
    def get_dock_info_from_summary(self, zpids: List[str]) -> Dict[str, str]:
        """Get dock_info from listings_summary table for the given ZPIDs"""
        try:
            if not zpids:
                return {}
            
            # Create placeholders for the IN clause
            placeholders = ','.join(['%s'] * len(zpids))
            
            self.cur.execute(f"""
                SELECT zpid, dock_info
                FROM listings_summary
                WHERE zpid IN ({placeholders})
            """, zpids)
            
            results = self.cur.fetchall()
            
            # Convert to dictionary
            dock_info_dict = {}
            for row in results:
                zpid, dock_info = row
                dock_info_dict[str(zpid)] = dock_info or ''
            
            return dock_info_dict
            
        except Exception as e:
            print(f"❌ Error getting dock_info: {e}")
            return {}
    
    def clean_field_value(self, value: str) -> str:
        """Clean field value by replacing problematic characters"""
        if not value:
            return ""
        
        # Convert to string and clean
        cleaned = str(value)
        
        # Replace problematic characters
        cleaned = cleaned.replace('¦', ';')  # Replace broken pipe with semicolon
        cleaned = cleaned.replace('|', ';')  # Replace pipe with semicolon to avoid delimiter confusion
        cleaned = cleaned.replace('\n', '\\n')  # Replace newlines with literal \n
        cleaned = cleaned.replace('\r', '\\r')  # Replace carriage returns with literal \r
        
        return cleaned.strip()
    
    def export_to_pipe_delimited(self, data: List[Dict[str, Any]], filename: str = None):
        """Export data to a pipe-delimited text file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"listings_data_export_v2_{timestamp}.txt"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                # Write header
                header = "zpid|description_raw|dock_info|waterfront_features|canal_info|reso_facts"
                file.write(header + '\n')
                
                # Write data rows
                for row in data:
                    # Clean and prepare each field
                    clean_row = []
                    
                    # zpid
                    clean_row.append(str(row.get('zpid', '')))
                    
                    # description_raw
                    clean_row.append(self.clean_field_value(row.get('description_raw', '')))
                    
                    # dock_info
                    clean_row.append(self.clean_field_value(row.get('dock_info', '')))
                    
                    # waterfront_features
                    clean_row.append(self.clean_field_value(row.get('waterfront_features', '')))
                    
                    # canal_info
                    clean_row.append(self.clean_field_value(row.get('canal_info', '')))
                    
                    # reso_facts
                    clean_row.append(self.clean_field_value(row.get('reso_facts', '')))
                    
                    # Join with pipe delimiter
                    line = '|'.join(clean_row)
                    file.write(line + '\n')
            
            print(f"✅ Data exported to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            return None
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str = None):
        """Export data to a CSV file as backup"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"listings_data_export_v2_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['zpid', 'description_raw', 'dock_info', 'waterfront_features', 'canal_info', 'reso_facts']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='|')
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                for row in data:
                    # Clean the data
                    clean_row = {
                        'zpid': str(row.get('zpid', '')),
                        'description_raw': self.clean_field_value(row.get('description_raw', '')),
                        'dock_info': self.clean_field_value(row.get('dock_info', '')),
                        'waterfront_features': self.clean_field_value(row.get('waterfront_features', '')),
                        'canal_info': self.clean_field_value(row.get('canal_info', '')),
                        'reso_facts': self.clean_field_value(row.get('reso_facts', ''))
                    }
                    writer.writerow(clean_row)
            
            print(f"✅ CSV backup exported to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error exporting CSV: {e}")
            return None
    
    def run_export(self):
        """Run the complete export process"""
        if not self.connect():
            return
        
        try:
            print("🚀 Starting Listings Data Export V2...")
            
            # Get listings data
            listings_data = self.get_listings_data()
            if not listings_data:
                print("❌ No data found to export")
                return
            
            # Get dock_info from listings_summary
            zpids = [str(row['zpid']) for row in listings_data]
            dock_info_dict = self.get_dock_info_from_summary(zpids)
            
            # Add dock_info to the data
            for row in listings_data:
                zpid_str = str(row['zpid'])
                row['dock_info'] = dock_info_dict.get(zpid_str, '')
            
            # Export to pipe-delimited text file
            text_file = self.export_to_pipe_delimited(listings_data)
            
            # Export to CSV as backup
            csv_file = self.export_to_csv(listings_data)
            
            # Show summary
            self.show_export_summary(listings_data, text_file, csv_file)
            
        except Exception as e:
            print(f"❌ Error during export: {e}")
        finally:
            self.disconnect()
    
    def show_export_summary(self, data: List[Dict[str, Any]], text_file: str, csv_file: str):
        """Display export summary"""
        print(f"\n📊 EXPORT SUMMARY V2")
        print("=" * 60)
        print(f"Total Records Exported: {len(data)}")
        print(f"Text File: {text_file}")
        print(f"CSV Backup: {csv_file}")
        
        # Show data quality stats
        fields = ['description_raw', 'dock_info', 'waterfront_features', 'canal_info', 'reso_facts']
        print(f"\n📈 Data Quality Statistics:")
        for field in fields:
            non_empty = sum(1 for row in data if row.get(field))
            percentage = (non_empty / len(data)) * 100 if data else 0
            print(f"  {field}: {non_empty}/{len(data)} ({percentage:.1f}%)")
        
        # Show sample data
        if data:
            print(f"\n🏠 Sample Data (first 3 records):")
            for i, row in enumerate(data[:3], 1):
                print(f"  {i}. ZPID: {row['zpid']}")
                print(f"     Description: {str(row['description_raw'])[:100]}...")
                print(f"     Dock Info: {row['dock_info']}")
                print(f"     Waterfront Features: {row['waterfront_features']}")
                print(f"     Canal Info: {row['canal_info']}")
                print(f"     RESO Facts: {row['reso_facts']}")
                print()

def main():
    """Main function"""
    exporter = ListingsDataExporterV2()
    exporter.run_export()

if __name__ == "__main__":
    main()
