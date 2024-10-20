import sqlite3

# Create or connect to the database
conn = sqlite3.connect('sales_data.db')
cursor = conn.cursor()

# Define the schema for the real estate sales data
cursor.execute('''
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,                   -- City
    sale_date TEXT,               -- יום מכירה (Sale Date)
    address TEXT,                 -- כתובת (Address)
    block_parcel TEXT,            -- גוש חלקה (Block - Parcel combined into one)
    property_type TEXT,           -- סוג נכס (Property Type)
    rooms INTEGER,                -- חדרים (Rooms)
    floor INTEGER,                -- קומה (Floor)
    square_meters REAL,           -- מ"ר (Square Meters)
    amount REAL,                  -- סכום (Amount)
    trend_change TEXT,            -- מגמת שינוי (Trend Change)
    UNIQUE(city, sale_date, address, amount) -- Prevent duplicates
);  
''')

# Commit and close the connection for now
conn.commit()
conn.close()