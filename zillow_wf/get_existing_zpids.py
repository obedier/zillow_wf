#!/usr/bin/env python3
import psycopg
import json

def get_existing_zpids():
    """Get all existing ZPIDs from the database"""
    conn = psycopg.connect('postgresql://osamabedier@localhost:5432/zillow_wf')
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT zpid FROM listings_summary')
        zpids = [row[0] for row in cur.fetchall()]
        
        # Save to JSON file
        with open('zillow_wf/data/existing_zpids.json', 'w') as f:
            json.dump(zpids, f)
        
        print(f'Saved {len(zpids)} existing ZPIDs to existing_zpids.json')
        print(f'First 10 ZPIDs: {zpids[:10]}')
        print(f'Last 10 ZPIDs: {zpids[-10:]}')
        
        return zpids
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    get_existing_zpids()
