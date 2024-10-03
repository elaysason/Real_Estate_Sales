import sqlite3

# Create or connect to the database
conn = sqlite3.connect('sales_data.db')
cursor = conn.cursor()

# Define the schema for the real estate sales data
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    sale_date TEXT,
    address TEXT,
    block TEXT,
    parcel TEXT,
    property_type TEXT,
    rooms INTEGER,
    floor INTEGER,
    square_meters REAL,
    amount REAL,
    trend_change TEXT
)
''')

# Commit and close the connection for now
conn.commit()
conn.close()