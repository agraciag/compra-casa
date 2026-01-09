import sqlite3
import os
from datetime import datetime

class PropertyDatabase:
    def __init__(self, db_path="data/properties.db"):
        """Initialize the database connection and create tables if they don't exist."""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # This allows us to access columns by name
        self.create_tables()
    
    def create_tables(self):
        """Create all necessary tables based on the defined schema."""
        cursor = self.conn.cursor()
        
        # Properties table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT UNIQUE,              -- ID from the source website
                source TEXT NOT NULL,                 -- Source website (idealista, fotocasa, etc.)
                url TEXT,                             -- Original listing URL
                title TEXT,                           -- Property title
                description TEXT,                     -- Property description
                
                -- Location
                address TEXT,
                city TEXT DEFAULT 'Zaragoza',
                district TEXT,                        -- Neighborhood/district
                postal_code TEXT,
                latitude REAL,
                longitude REAL,
                
                -- Property details
                property_type TEXT,                   -- apartment, house, studio, etc.
                price REAL,
                currency TEXT DEFAULT 'EUR',
                surface_area REAL,                    -- Total area in sq meters
                rooms INTEGER,                        -- Number of rooms
                bedrooms INTEGER,
                bathrooms INTEGER,
                floor_number INTEGER,                 -- Floor level
                total_floors INTEGER,                 -- Building height
                construction_year INTEGER,
                
                -- Features
                has_elevator BOOLEAN,
                has_parking BOOLEAN,
                parking_price REAL,
                has_terrace BOOLEAN,
                has_balcony BOOLEAN,
                has_garden BOOLEAN,
                has_pool BOOLEAN,
                energy_certificate_rating TEXT,       -- Energy efficiency rating
                
                -- Status and metadata
                is_active BOOLEAN DEFAULT TRUE,       -- Is the listing still active?
                first_seen_date DATE,
                last_seen_date DATE,
                scraped_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Historical Prices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER,
                price REAL NOT NULL,
                date_recorded DATE NOT NULL,
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        ''')
        
        # Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,            -- idealista, fotocasa, etc.
                base_url TEXT,
                last_scraped DATETIME,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Scraping Logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                url TEXT,
                status_code INTEGER,
                response_time REAL,
                error_message TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Market Statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                district TEXT,
                avg_price_per_sqm REAL,
                median_price_per_sqm REAL,
                transaction_count INTEGER,
                period_start DATE,                    -- Start of reporting period
                period_end DATE,                      -- End of reporting period
                source TEXT,                          -- Official source (penotariado, tinsa, etc.)
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_properties_city ON properties(city)",
            "CREATE INDEX IF NOT EXISTS idx_properties_district ON properties(district)",
            "CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price)",
            "CREATE INDEX IF NOT EXISTS idx_properties_surface_area ON properties(surface_area)",
            "CREATE INDEX IF NOT EXISTS idx_properties_rooms ON properties(rooms)",
            "CREATE INDEX IF NOT EXISTS idx_properties_bedrooms ON properties(bedrooms)",
            "CREATE INDEX IF NOT EXISTS idx_properties_property_type ON properties(property_type)",
            "CREATE INDEX IF NOT EXISTS idx_properties_coordinates ON properties(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_properties_is_active ON properties(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_properties_source ON properties(source)",
            "CREATE INDEX IF NOT EXISTS idx_properties_location_price ON properties(city, district, price)",
            "CREATE INDEX IF NOT EXISTS idx_properties_type_price ON properties(property_type, price)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        self.conn.commit()
    
    def insert_property(self, property_data):
        """Insert a new property record or update if it already exists."""
        cursor = self.conn.cursor()
        
        # Prepare the SQL statement
        sql = '''
            INSERT OR REPLACE INTO properties (
                external_id, source, url, title, description, address, city, district, 
                postal_code, latitude, longitude, property_type, price, currency, 
                surface_area, rooms, bedrooms, bathrooms, floor_number, total_floors, 
                construction_year, has_elevator, has_parking, parking_price, 
                has_terrace, has_balcony, has_garden, has_pool, 
                energy_certificate_rating, is_active, first_seen_date, last_seen_date, 
                scraped_at
            ) VALUES (
                :external_id, :source, :url, :title, :description, :address, :city, :district, 
                :postal_code, :latitude, :longitude, :property_type, :price, :currency, 
                :surface_area, :rooms, :bedrooms, :bathrooms, :floor_number, :total_floors, 
                :construction_year, :has_elevator, :has_parking, :parking_price, 
                :has_terrace, :has_balcony, :has_garden, :has_pool, 
                :energy_certificate_rating, :is_active, :first_seen_date, :last_seen_date, 
                :scraped_at
            )
        '''
        
        # Set the current timestamp
        property_data['scraped_at'] = datetime.now().isoformat()
        
        # Set first_seen_date if it's a new property
        if 'first_seen_date' not in property_data or property_data['first_seen_date'] is None:
            property_data['first_seen_date'] = datetime.now().date().isoformat()
        
        # Update last_seen_date
        property_data['last_seen_date'] = datetime.now().date().isoformat()
        
        cursor.execute(sql, property_data)
        self.conn.commit()
        
        return cursor.lastrowid
    
    def get_property_by_external_id(self, external_id, source):
        """Retrieve a property by its external ID and source."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM properties WHERE external_id = ? AND source = ?", 
            (external_id, source)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_similar_properties(self, address=None, price_range=None, surface_area_range=None):
        """Find potentially similar/duplicate properties."""
        cursor = self.conn.cursor()
        
        conditions = []
        params = []
        
        if address:
            conditions.append("address LIKE ?")
            params.append(f"%{address}%")
        
        if price_range:
            min_price, max_price = price_range
            conditions.append("price BETWEEN ? AND ?")
            params.extend([min_price, max_price])
        
        if surface_area_range:
            min_area, max_area = surface_area_range
            conditions.append("surface_area BETWEEN ? AND ?")
            params.extend([min_area, max_area])
        
        if conditions:
            sql = f"SELECT * FROM properties WHERE {' AND '.join(conditions)}"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        
        return []
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

# Example usage
if __name__ == "__main__":
    db = PropertyDatabase()
    print("Database initialized successfully!")
    print(f"Database file created at: {db.db_path}")
    db.close()