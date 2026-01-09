from flask import Flask, render_template, jsonify, request
import os
import sqlite3
from datetime import datetime
import json

from src.utils.database import PropertyDatabase
from src.utils.models import PropertyModel
from src.utils.deduplication import PropertyDeduplicator

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
    
    # Initialize database
    db = PropertyDatabase()
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/properties')
    def get_properties():
        """Get all properties with optional filters"""
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get query parameters for filtering
        filters = {}
        if request.args.get('min_price'):
            filters['min_price'] = float(request.args.get('min_price'))
        if request.args.get('max_price'):
            filters['max_price'] = float(request.args.get('max_price'))
        if request.args.get('min_surface'):
            filters['min_surface'] = float(request.args.get('min_surface'))
        if request.args.get('max_surface'):
            filters['max_surface'] = float(request.args.get('max_surface'))
        if request.args.get('bedrooms'):
            filters['bedrooms'] = int(request.args.get('bedrooms'))
        if request.args.get('district'):
            filters['district'] = request.args.get('district')
        
        # Build query with filters
        query = "SELECT * FROM properties WHERE is_active = 1"
        params = []
        
        if 'min_price' in filters:
            query += " AND price >= ?"
            params.append(filters['min_price'])
        if 'max_price' in filters:
            query += " AND price <= ?"
            params.append(filters['max_price'])
        if 'min_surface' in filters:
            query += " AND surface_area >= ?"
            params.append(filters['min_surface'])
        if 'max_surface' in filters:
            query += " AND surface_area <= ?"
            params.append(filters['max_surface'])
        if 'bedrooms' in filters:
            query += " AND bedrooms = ?"
            params.append(filters['bedrooms'])
        if 'district' in filters:
            query += " AND district LIKE ?"
            params.append(f"%{filters['district']}%")
        
        query += " ORDER BY price_per_sqm ASC LIMIT 100"  # Limit results for performance
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Calculate price per sqm for each property
        properties = []
        for row in rows:
            prop_dict = dict(row)
            if prop_dict['surface_area'] and prop_dict['surface_area'] > 0:
                prop_dict['price_per_sqm'] = round(prop_dict['price'] / prop_dict['surface_area'], 2)
            else:
                prop_dict['price_per_sqm'] = 0
            properties.append(prop_dict)
        
        conn.close()
        return jsonify(properties)
    
    @app.route('/api/property/<int:property_id>')
    def get_property(property_id):
        """Get a specific property by ID"""
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            prop_dict = dict(row)
            if prop_dict['surface_area'] and prop_dict['surface_area'] > 0:
                prop_dict['price_per_sqm'] = round(prop_dict['price'] / prop_dict['surface_area'], 2)
            else:
                prop_dict['price_per_sqm'] = 0
            return jsonify(prop_dict)
        else:
            return jsonify({'error': 'Property not found'}), 404
    
    @app.route('/api/stats')
    def get_stats():
        """Get property statistics"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
        total_properties = cursor.fetchone()[0]
        
        # Get average price
        cursor.execute("SELECT AVG(price) FROM properties WHERE is_active = 1 AND price IS NOT NULL")
        avg_price = cursor.fetchone()[0]
        
        # Get average price per sqm
        cursor.execute("""
            SELECT AVG(price/surface_area) 
            FROM properties 
            WHERE is_active = 1 AND price IS NOT NULL AND surface_area IS NOT NULL AND surface_area > 0
        """)
        avg_price_per_sqm = cursor.fetchone()[0]
        
        # Get properties by district
        cursor.execute("""
            SELECT district, COUNT(*) as count 
            FROM properties 
            WHERE is_active = 1 AND district IS NOT NULL 
            GROUP BY district 
            ORDER BY count DESC
            LIMIT 10
        """)
        district_counts = [{'district': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get price range distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN price < 100000 THEN 'Under €100k'
                    WHEN price < 200000 THEN '€100k - €200k'
                    WHEN price < 300000 THEN '€200k - €300k'
                    WHEN price < 400000 THEN '€300k - €400k'
                    ELSE 'Over €400k'
                END as price_range,
                COUNT(*) as count
            FROM properties 
            WHERE is_active = 1 AND price IS NOT NULL
            GROUP BY price_range
            ORDER BY MIN(price)
        """)
        price_ranges = [{'range': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        stats = {
            'total_properties': total_properties,
            'avg_price': round(avg_price, 2) if avg_price else 0,
            'avg_price_per_sqm': round(avg_price_per_sqm, 2) if avg_price_per_sqm else 0,
            'district_counts': district_counts,
            'price_ranges': price_ranges
        }
        
        return jsonify(stats)
    
    @app.route('/api/search')
    def search_properties():
        """Search properties by keyword"""
        keyword = request.args.get('q', '').strip()
        if not keyword:
            return jsonify([])
        
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search in title, description, address, and district
        query = """
            SELECT * FROM properties 
            WHERE is_active = 1 
            AND (title LIKE ? OR description LIKE ? OR address LIKE ? OR district LIKE ?)
            LIMIT 50
        """
        search_term = f"%{keyword}%"
        cursor.execute(query, (search_term, search_term, search_term, search_term))
        rows = cursor.fetchall()
        
        properties = []
        for row in rows:
            prop_dict = dict(row)
            if prop_dict['surface_area'] and prop_dict['surface_area'] > 0:
                prop_dict['price_per_sqm'] = round(prop_dict['price'] / prop_dict['surface_area'], 2)
            else:
                prop_dict['price_per_sqm'] = 0
            properties.append(prop_dict)
        
        conn.close()
        return jsonify(properties)
    
    # Serve static files
    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)