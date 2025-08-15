#!/usr/bin/env python3
"""
Create WF Data Table Script
Create a new table called wf_data in the zillow_wf database and populate it with waterfront features data.
"""

import psycopg
import csv
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

class WFDataTableCreator:
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
    
    def create_table(self):
        """Create the wf_data table"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS wf_data (
                id SERIAL PRIMARY KEY,
                zpid VARCHAR(20) NOT NULL,
                description_length INTEGER,
                waterfront_linear_ft INTEGER,
                dock_linear_ft INTEGER,
                no_fixed_bridges BOOLEAN DEFAULT FALSE,
                waterfront_type TEXT,
                any_length INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            self.cur.execute(create_table_sql)
            
            # Create index on zpid for efficient joins
            self.cur.execute("CREATE INDEX IF NOT EXISTS idx_wf_data_zpid ON wf_data(zpid);")
            
            self.conn.commit()
            print("✅ wf_data table created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            self.conn.rollback()
            return False
    
    def load_csv_data(self, csv_file: str):
        """Load data from CSV file"""
        try:
            print(f"📁 Loading data from: {csv_file}")
            
            # Read CSV with pandas for better handling
            df = pd.read_csv(csv_file)
            print(f"📊 Loaded {len(df)} rows from CSV")
            
            # Show data types and sample
            print(f"📋 CSV Columns: {list(df.columns)}")
            print(f"📋 Data Types: {df.dtypes.to_dict()}")
            print(f"📋 Sample Data:")
            print(df.head(3))
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return None
    
    def insert_data(self, df: pd.DataFrame):
        """Insert data into the wf_data table"""
        try:
            print("💾 Inserting data into wf_data table...")
            
            # Clear existing data if any
            self.cur.execute("DELETE FROM wf_data;")
            print("🗑️  Cleared existing data")
            
            # Prepare insert statement
            insert_sql = """
            INSERT INTO wf_data (
                zpid, description_length, waterfront_linear_ft, dock_linear_ft, 
                no_fixed_bridges, waterfront_type, any_length
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # Convert DataFrame to list of tuples for insertion
            records = []
            for _, row in df.iterrows():
                # Handle boolean conversion for no_fixed_bridges
                no_fixed_bridges = row['no_fixed_bridges'] if pd.notna(row['no_fixed_bridges']) else False
                if isinstance(no_fixed_bridges, str):
                    no_fixed_bridges = no_fixed_bridges.upper() == 'TRUE'
                
                # Handle description_length - extract number if it's text like "80 Feet"
                description_length = None
                if pd.notna(row['description_length']):
                    if isinstance(row['description_length'], str):
                        # Try to extract number from text like "80 Feet"
                        import re
                        num_match = re.search(r'(\d+)', str(row['description_length']))
                        if num_match:
                            description_length = int(num_match.group(1))
                    else:
                        try:
                            description_length = int(row['description_length'])
                        except (ValueError, TypeError):
                            description_length = None
                
                # Handle waterfront_linear_ft
                waterfront_linear_ft = None
                if pd.notna(row['waterfront_linear_ft']):
                    try:
                        waterfront_linear_ft = int(float(row['waterfront_linear_ft']))
                    except (ValueError, TypeError):
                        waterfront_linear_ft = None
                
                # Handle dock_linear_ft
                dock_linear_ft = None
                if pd.notna(row['dock_linear_ft']):
                    try:
                        dock_linear_ft = int(float(row['dock_linear_ft']))
                    except (ValueError, TypeError):
                        dock_linear_ft = None
                
                # Handle any_length
                any_length = None
                if pd.notna(row['any_length']):
                    try:
                        any_length = int(float(row['any_length']))
                    except (ValueError, TypeError):
                        any_length = None
                
                record = (
                    str(row['zpid']),
                    description_length,
                    waterfront_linear_ft,
                    dock_linear_ft,
                    no_fixed_bridges,
                    row['waterfront_type'] if pd.notna(row['waterfront_type']) else None,
                    any_length
                )
                records.append(record)
            
            # Insert in batches
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                self.cur.executemany(insert_sql, batch)
                print(f"✅ Inserted batch {i//batch_size + 1}/{(len(records) + batch_size - 1)//batch_size}")
            
            self.conn.commit()
            print(f"✅ Successfully inserted {len(records)} records")
            return True
            
        except Exception as e:
            print(f"❌ Error inserting data: {e}")
            self.conn.rollback()
            return False
    
    def verify_data(self):
        """Verify the data was inserted correctly"""
        try:
            print("🔍 Verifying data insertion...")
            
            # Check row count
            self.cur.execute("SELECT COUNT(*) FROM wf_data;")
            count = self.cur.fetchone()[0]
            print(f"📊 Total rows in wf_data table: {count}")
            
            # Check sample data
            self.cur.execute("SELECT * FROM wf_data LIMIT 5;")
            sample_rows = self.cur.fetchall()
            print(f"📋 Sample rows:")
            for row in sample_rows:
                print(f"  {row}")
            
            # Check data types
            self.cur.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'wf_data' 
                ORDER BY ordinal_position;
            """)
            columns = self.cur.fetchall()
            print(f"🏗️  Table structure:")
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
            return False
    
    def test_joins(self):
        """Test joining with existing tables"""
        try:
            print("🔗 Testing table joins...")
            
            # Test join with listings_summary
            self.cur.execute("""
                SELECT COUNT(*) 
                FROM wf_data w 
                JOIN listings_summary l ON w.zpid = l.zpid;
            """)
            join_count = self.cur.fetchone()[0]
            print(f"📊 Joinable records with listings_summary: {join_count}")
            
            # Test join with listings_detail
            self.cur.execute("""
                SELECT COUNT(*) 
                FROM wf_data w 
                JOIN listings_detail l ON w.zpid = l.zpid;
            """)
            detail_join_count = self.cur.fetchone()[0]
            print(f"📊 Joinable records with listings_detail: {detail_join_count}")
            
            # Show sample joined data
            self.cur.execute("""
                SELECT w.zpid, w.waterfront_type, w.waterfront_linear_ft, 
                       l.address, l.city, l.state
                FROM wf_data w 
                JOIN listings_summary l ON w.zpid = l.zpid 
                WHERE w.waterfront_linear_ft IS NOT NULL 
                LIMIT 5;
            """)
            joined_samples = self.cur.fetchall()
            print(f"📋 Sample joined data:")
            for row in joined_samples:
                print(f"  ZPID {row[0]}: {row[1]} | {row[2]} ft | {row[3]}, {row[4]}, {row[5]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing joins: {e}")
            return False
    
    def run_creation(self, csv_file: str):
        """Run the complete table creation process"""
        print("🚀 Starting WF Data Table Creation...")
        
        if not self.connect():
            return
        
        try:
            # Create table
            if not self.create_table():
                return
            
            # Load CSV data
            df = self.load_csv_data(csv_file)
            if df is None:
                return
            
            # Insert data
            if not self.insert_data(df):
                return
            
            # Verify data
            if not self.verify_data():
                return
            
            # Test joins
            if not self.test_joins():
                return
            
            print("\n✅ WF Data table creation completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during table creation: {e}")
        finally:
            self.disconnect()

def main():
    """Main function"""
    csv_file = "waterfront_features_v4_634_properties2.csv"
    
    # Check if CSV file exists
    import os
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Create table and populate with data
    creator = WFDataTableCreator()
    creator.run_creation(csv_file)

if __name__ == "__main__":
    main()
