from flask import Flask, render_template, jsonify, request, send_from_directory, g
import os
import sqlite3
from datetime import datetime

from src.utils.database import PropertyDatabase


def get_db(db_path):
    """Get a database connection for the current request."""
    if 'db_conn' not in g:
        g.db_conn = sqlite3.connect(db_path)
        g.db_conn.row_factory = sqlite3.Row
    return g.db_conn


def add_price_per_sqm(prop_dict):
    """Calculate and add price_per_sqm to a property dict."""
    if prop_dict.get('surface_area') and prop_dict['surface_area'] > 0 and prop_dict.get('price'):
        prop_dict['price_per_sqm'] = round(prop_dict['price'] / prop_dict['surface_area'], 2)
    else:
        prop_dict['price_per_sqm'] = 0
    return prop_dict


def get_district_averages(conn):
    """Calculate average price/m2 per district for opportunity scoring."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT district, AVG(price / surface_area) as avg_price_sqm, COUNT(*) as cnt
        FROM properties
        WHERE is_active = 1 AND price IS NOT NULL AND surface_area > 0 AND district IS NOT NULL
        GROUP BY district
        HAVING cnt >= 1
    """)
    return {row['district']: row['avg_price_sqm'] for row in cursor.fetchall()}


def get_global_average(conn):
    """Calculate global average price/m2."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT AVG(price / surface_area)
        FROM properties
        WHERE is_active = 1 AND price IS NOT NULL AND surface_area > 0
    """)
    result = cursor.fetchone()[0]
    return result or 0


def score_opportunity(prop, district_avgs, global_avg):
    """Score a property as an opportunity. Returns score 0-100 and label.
    Lower price/m2 relative to district average = better opportunity.
    """
    price_sqm = prop.get('price_per_sqm', 0)
    if not price_sqm or price_sqm <= 0:
        return {'score': 0, 'label': 'sin_datos', 'diff_pct': 0}

    district = prop.get('district')
    avg = district_avgs.get(district, global_avg) if district else global_avg
    if not avg or avg <= 0:
        return {'score': 50, 'label': 'normal', 'diff_pct': 0}

    diff_pct = ((avg - price_sqm) / avg) * 100  # positive = cheaper than avg

    if diff_pct >= 20:
        score, label = 95, 'oportunidad'
    elif diff_pct >= 10:
        score, label = 80, 'buen_precio'
    elif diff_pct >= 0:
        score, label = 60, 'precio_justo'
    elif diff_pct >= -10:
        score, label = 40, 'algo_caro'
    else:
        score, label = 20, 'caro'

    return {'score': score, 'label': label, 'diff_pct': round(diff_pct, 1)}


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())

    # Initialize database (creates tables if needed)
    db = PropertyDatabase()
    db_path = db.db_path
    db.close()

    @app.teardown_appcontext
    def close_db(exception):
        conn = g.pop('db_conn', None)
        if conn is not None:
            conn.close()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/properties')
    def get_properties():
        """Get all properties with optional filters"""
        conn = get_db(db_path)
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM properties WHERE is_active = 1"
        params = []

        if request.args.get('min_price'):
            query += " AND price >= ?"
            params.append(float(request.args.get('min_price')))
        if request.args.get('max_price'):
            query += " AND price <= ?"
            params.append(float(request.args.get('max_price')))
        if request.args.get('min_surface'):
            query += " AND surface_area >= ?"
            params.append(float(request.args.get('min_surface')))
        if request.args.get('max_surface'):
            query += " AND surface_area <= ?"
            params.append(float(request.args.get('max_surface')))
        if request.args.get('bedrooms'):
            query += " AND bedrooms = ?"
            params.append(int(request.args.get('bedrooms')))
        if request.args.get('district'):
            query += " AND district LIKE ?"
            params.append(f"%{request.args.get('district')}%")
        if request.args.get('property_type'):
            query += " AND property_type = ?"
            params.append(request.args.get('property_type'))
        if request.args.get('property_condition'):
            query += " AND property_condition = ?"
            params.append(request.args.get('property_condition'))

        # Feature filters (boolean)
        for feat in ('has_elevator', 'has_parking', 'has_terrace', 'has_balcony', 'has_garden', 'has_pool'):
            if request.args.get(feat) == '1':
                query += f" AND {feat} = 1"

        query += " ORDER BY CASE WHEN surface_area > 0 THEN price / surface_area ELSE price END ASC LIMIT 100"

        cursor.execute(query, params)
        properties = [add_price_per_sqm(dict(row)) for row in cursor.fetchall()]

        # Add opportunity scores
        district_avgs = get_district_averages(conn)
        global_avg = get_global_average(conn)
        for p in properties:
            p['opportunity'] = score_opportunity(p, district_avgs, global_avg)

        return jsonify(properties)

    @app.route('/api/property/<int:property_id>')
    def get_property(property_id):
        """Get a specific property by ID"""
        conn = get_db(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
        row = cursor.fetchone()

        if row:
            prop = add_price_per_sqm(dict(row))
            district_avgs = get_district_averages(conn)
            global_avg = get_global_average(conn)
            prop['opportunity'] = score_opportunity(prop, district_avgs, global_avg)
            return jsonify(prop)
        else:
            return jsonify({'error': 'Property not found'}), 404

    @app.route('/api/properties', methods=['POST'])
    def create_property():
        """Create a new property from manual entry."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required = ['title', 'price']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Campo requerido: {field}'}), 400

        conn = get_db(db_path)
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        today = datetime.now().strftime('%Y-%m-%d')

        # Generate an external_id for manual entries
        cursor.execute("SELECT COUNT(*) FROM properties WHERE source = 'manual'")
        manual_count = cursor.fetchone()[0]
        external_id = data.get('external_id') or f"MANUAL{manual_count + 1:04d}"

        cursor.execute("""
            INSERT INTO properties (
                external_id, source, url, title, description,
                address, district, postal_code,
                property_type, price, surface_area,
                rooms, bedrooms, bathrooms, floor_number, construction_year,
                has_elevator, has_parking, has_terrace, has_balcony, has_garden, has_pool,
                energy_certificate_rating, property_condition,
                is_active, first_seen_date, last_seen_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        """, (
            external_id,
            data.get('source', 'manual'),
            data.get('url', ''),
            data['title'],
            data.get('description', ''),
            data.get('address', ''),
            data.get('district', ''),
            data.get('postal_code', ''),
            data.get('property_type', ''),
            float(data['price']),
            float(data['surface_area']) if data.get('surface_area') else None,
            int(data['rooms']) if data.get('rooms') else None,
            int(data['bedrooms']) if data.get('bedrooms') else None,
            int(data['bathrooms']) if data.get('bathrooms') else None,
            int(data['floor_number']) if data.get('floor_number') else None,
            int(data['construction_year']) if data.get('construction_year') else None,
            bool(data.get('has_elevator')),
            bool(data.get('has_parking')),
            bool(data.get('has_terrace')),
            bool(data.get('has_balcony')),
            bool(data.get('has_garden')),
            bool(data.get('has_pool')),
            data.get('energy_certificate_rating', ''),
            data.get('property_condition', ''),
            today, today, now, now,
        ))
        conn.commit()
        new_id = cursor.lastrowid

        return jsonify({'id': new_id, 'message': 'Propiedad creada'}), 201

    @app.route('/api/property/<int:property_id>', methods=['DELETE'])
    def delete_property(property_id):
        """Soft-delete a property (mark as inactive)."""
        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE properties SET is_active = 0, updated_at = ? WHERE id = ?",
                        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), property_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Propiedad no encontrada'}), 404
        return jsonify({'message': 'Propiedad eliminada'})

    @app.route('/api/property/<int:property_id>', methods=['PUT'])
    def update_property(property_id):
        """Update an existing property."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conn = get_db(db_path)
        cursor = conn.cursor()

        # Build dynamic UPDATE
        allowed_fields = [
            'title', 'description', 'url', 'address', 'district', 'postal_code',
            'property_type', 'price', 'surface_area', 'rooms', 'bedrooms', 'bathrooms',
            'floor_number', 'construction_year', 'has_elevator', 'has_parking',
            'has_terrace', 'has_balcony', 'has_garden', 'has_pool',
            'energy_certificate_rating', 'property_condition', 'source',
        ]
        sets = []
        params = []
        for field in allowed_fields:
            if field in data:
                sets.append(f"{field} = ?")
                params.append(data[field])

        if not sets:
            return jsonify({'error': 'No fields to update'}), 400

        sets.append("updated_at = ?")
        params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        params.append(property_id)

        cursor.execute(f"UPDATE properties SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Propiedad no encontrada'}), 404
        return jsonify({'message': 'Propiedad actualizada'})

    @app.route('/api/stats')
    def get_stats():
        """Get property statistics"""
        conn = get_db(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
        total_properties = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(price) FROM properties WHERE is_active = 1 AND price IS NOT NULL")
        avg_price = cursor.fetchone()[0]

        cursor.execute("""
            SELECT AVG(price/surface_area)
            FROM properties
            WHERE is_active = 1 AND price IS NOT NULL AND surface_area IS NOT NULL AND surface_area > 0
        """)
        avg_price_per_sqm = cursor.fetchone()[0]

        cursor.execute("""
            SELECT district, COUNT(*) as count
            FROM properties
            WHERE is_active = 1 AND district IS NOT NULL
            GROUP BY district
            ORDER BY count DESC
            LIMIT 10
        """)
        district_counts = [{'district': row[0], 'count': row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT
                CASE
                    WHEN price < 100000 THEN 'Under 100k'
                    WHEN price < 200000 THEN '100k - 200k'
                    WHEN price < 300000 THEN '200k - 300k'
                    WHEN price < 400000 THEN '300k - 400k'
                    ELSE 'Over 400k'
                END as price_range,
                COUNT(*) as count
            FROM properties
            WHERE is_active = 1 AND price IS NOT NULL
            GROUP BY price_range
            ORDER BY MIN(price)
        """)
        price_ranges = [{'range': row[0], 'count': row[1]} for row in cursor.fetchall()]

        # District price averages for opportunity detection
        district_avgs = get_district_averages(conn)
        district_avg_list = [{'district': d, 'avg_price_sqm': round(v, 2)} for d, v in sorted(district_avgs.items())]

        stats = {
            'total_properties': total_properties,
            'avg_price': round(avg_price, 2) if avg_price else 0,
            'avg_price_per_sqm': round(avg_price_per_sqm, 2) if avg_price_per_sqm else 0,
            'district_counts': district_counts,
            'price_ranges': price_ranges,
            'district_averages': district_avg_list,
        }

        return jsonify(stats)

    @app.route('/api/search')
    def search_properties():
        """Search properties by keyword"""
        keyword = request.args.get('q', '').strip()
        if not keyword:
            return jsonify([])

        conn = get_db(db_path)
        cursor = conn.cursor()

        # Escape LIKE wildcards in user input
        escaped = keyword.replace('%', r'\%').replace('_', r'\_')
        search_term = f"%{escaped}%"

        query = """
            SELECT * FROM properties
            WHERE is_active = 1
            AND (title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\' OR address LIKE ? ESCAPE '\\' OR district LIKE ? ESCAPE '\\')
            LIMIT 50
        """
        cursor.execute(query, (search_term, search_term, search_term, search_term))
        properties = [add_price_per_sqm(dict(row)) for row in cursor.fetchall()]
        return jsonify(properties)

    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
