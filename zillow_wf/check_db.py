#!/usr/bin/env python3
import psycopg

# Connect to database
conn = psycopg.connect('postgresql://osamabedier@localhost:5432/zillow_wf')
cur = conn.cursor()

# Check if the extracted properties exist
zpids = ['43117208', '43111853', '43192880']
for zpid in zpids:
    cur.execute('SELECT COUNT(*) FROM listings_summary WHERE zpid = %s', (zpid,))
    count = cur.fetchone()[0]
    print(f'ZPID {zpid}: {"Found" if count > 0 else "Not found"} in database')

cur.close()
conn.close()
