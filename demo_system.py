#!/usr/bin/env python3
"""
Demo script to populate the database with sample properties for testing.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import PropertyDatabase
from src.utils.models import PropertyModel
from src.utils.deduplication import PropertyDeduplicator


SAMPLE_PROPERTIES = [
    {
        'external_id': 'DEMO001', 'source': 'idealista',
        'url': 'https://www.idealista.com/inmueble/DEMO001/',
        'title': 'Piso reformado en Casco Historico',
        'description': 'Precioso piso reformado con vistas al Pilar. Segunda mano en excelente estado.',
        'address': 'Calle Alfonso I, 10', 'district': 'Casco Historico', 'postal_code': '50001',
        'latitude': 41.6488, 'longitude': -0.8774,
        'property_type': 'apartment', 'price': 185000, 'surface_area': 85,
        'rooms': 3, 'bedrooms': 2, 'bathrooms': 1, 'floor_number': 3, 'total_floors': 5,
        'construction_year': 1980,
        'has_elevator': True, 'has_parking': False, 'has_terrace': False,
        'has_balcony': True, 'has_garden': False, 'has_pool': False,
        'energy_certificate_rating': 'D', 'property_condition': 'segunda_mano',
    },
    {
        'external_id': 'DEMO002', 'source': 'fotocasa',
        'url': 'https://www.fotocasa.es/inmueble/DEMO002/',
        'title': 'Obra nueva en Valdespartera con terraza',
        'description': 'Promocion nueva con zonas comunes, piscina y garaje incluido.',
        'address': 'Calle Parque del Agua, 5', 'district': 'Valdespartera', 'postal_code': '50019',
        'latitude': 41.6150, 'longitude': -0.9100,
        'property_type': 'apartment', 'price': 245000, 'surface_area': 92,
        'rooms': 4, 'bedrooms': 3, 'bathrooms': 2, 'floor_number': 2, 'total_floors': 6,
        'construction_year': 2025,
        'has_elevator': True, 'has_parking': True, 'has_terrace': True,
        'has_balcony': False, 'has_garden': False, 'has_pool': True,
        'energy_certificate_rating': 'A', 'property_condition': 'obra_nueva',
    },
    {
        'external_id': 'DEMO003', 'source': 'habitaclia',
        'url': 'https://www.habitaclia.com/inmueble/DEMO003/',
        'title': 'Edificio en construccion - Parque Venecia',
        'description': 'Entrega prevista para 2027. Pisos de 2 y 3 dormitorios con garaje.',
        'address': 'Avenida Parque Venecia, 22', 'district': 'Parque Venecia', 'postal_code': '50021',
        'latitude': 41.6200, 'longitude': -0.8950,
        'property_type': 'apartment', 'price': 220000, 'surface_area': 78,
        'rooms': 3, 'bedrooms': 2, 'bathrooms': 2, 'floor_number': 4, 'total_floors': 8,
        'construction_year': 2027,
        'has_elevator': True, 'has_parking': True, 'has_terrace': True,
        'has_balcony': False, 'has_garden': True, 'has_pool': True,
        'energy_certificate_rating': 'A', 'property_condition': 'en_construccion',
    },
    {
        'external_id': 'DEMO004', 'source': 'idealista',
        'url': 'https://www.idealista.com/inmueble/DEMO004/',
        'title': 'Atico duplex en Delicias',
        'description': 'Atico duplex con gran terraza y vistas despejadas.',
        'address': 'Calle Delicias, 45', 'district': 'Delicias', 'postal_code': '50017',
        'latitude': 41.6450, 'longitude': -0.9050,
        'property_type': 'duplex', 'price': 165000, 'surface_area': 110,
        'rooms': 4, 'bedrooms': 3, 'bathrooms': 2, 'floor_number': 5, 'total_floors': 5,
        'construction_year': 1995,
        'has_elevator': False, 'has_parking': False, 'has_terrace': True,
        'has_balcony': True, 'has_garden': False, 'has_pool': False,
        'energy_certificate_rating': 'E', 'property_condition': 'segunda_mano',
    },
    {
        'external_id': 'DEMO005', 'source': 'fotocasa',
        'url': 'https://www.fotocasa.es/inmueble/DEMO005/',
        'title': 'Chalet adosado en Montecanal',
        'description': 'Chalet con jardin privado, garaje doble y piscina comunitaria.',
        'address': 'Calle Montecanal, 12', 'district': 'Montecanal', 'postal_code': '50012',
        'latitude': 41.6250, 'longitude': -0.8650,
        'property_type': 'chalet', 'price': 385000, 'surface_area': 210,
        'rooms': 5, 'bedrooms': 4, 'bathrooms': 3, 'floor_number': 0, 'total_floors': 2,
        'construction_year': 2010,
        'has_elevator': False, 'has_parking': True, 'has_terrace': True,
        'has_balcony': False, 'has_garden': True, 'has_pool': True,
        'energy_certificate_rating': 'B', 'property_condition': 'segunda_mano',
    },
    {
        'external_id': 'DEMO006', 'source': 'idealista',
        'url': 'https://www.idealista.com/inmueble/DEMO006/',
        'title': 'Estudio en el centro',
        'description': 'Estudio ideal para inversion o primera vivienda.',
        'address': 'Calle San Vicente de Paul, 8', 'district': 'Casco Historico', 'postal_code': '50001',
        'latitude': 41.6510, 'longitude': -0.8790,
        'property_type': 'studio', 'price': 75000, 'surface_area': 38,
        'rooms': 1, 'bedrooms': 0, 'bathrooms': 1, 'floor_number': 1, 'total_floors': 4,
        'construction_year': 1970,
        'has_elevator': False, 'has_parking': False, 'has_terrace': False,
        'has_balcony': True, 'has_garden': False, 'has_pool': False,
        'energy_certificate_rating': 'F', 'property_condition': 'segunda_mano',
    },
    {
        'external_id': 'DEMO007', 'source': 'habitaclia',
        'url': 'https://www.habitaclia.com/inmueble/DEMO007/',
        'title': 'Obra nueva en Arcosur con garaje',
        'description': 'Pisos a estrenar con zonas verdes y excelentes comunicaciones.',
        'address': 'Calle Arcosur, 3', 'district': 'Arcosur', 'postal_code': '50020',
        'latitude': 41.6080, 'longitude': -0.9200,
        'property_type': 'apartment', 'price': 195000, 'surface_area': 75,
        'rooms': 3, 'bedrooms': 2, 'bathrooms': 1, 'floor_number': 1, 'total_floors': 5,
        'construction_year': 2025,
        'has_elevator': True, 'has_parking': True, 'has_terrace': False,
        'has_balcony': True, 'has_garden': False, 'has_pool': False,
        'energy_certificate_rating': 'A', 'property_condition': 'obra_nueva',
    },
    {
        'external_id': 'DEMO008', 'source': 'fotocasa',
        'url': 'https://www.fotocasa.es/inmueble/DEMO008/',
        'title': 'Piso grande en Las Fuentes',
        'description': 'Piso de 4 dormitorios cerca del tranvia. Necesita reforma.',
        'address': 'Calle Salvador Minguijon, 15', 'district': 'Las Fuentes', 'postal_code': '50002',
        'latitude': 41.6530, 'longitude': -0.8630,
        'property_type': 'apartment', 'price': 125000, 'surface_area': 105,
        'rooms': 5, 'bedrooms': 4, 'bathrooms': 1, 'floor_number': 4, 'total_floors': 7,
        'construction_year': 1975,
        'has_elevator': True, 'has_parking': False, 'has_terrace': False,
        'has_balcony': True, 'has_garden': False, 'has_pool': False,
        'energy_certificate_rating': 'G', 'property_condition': 'segunda_mano',
    },
    {
        'external_id': 'DEMO009', 'source': 'idealista',
        'url': 'https://www.idealista.com/inmueble/DEMO009/',
        'title': 'Promocion en construccion - Rosales del Canal',
        'description': 'Edificio en construccion con entrega prevista 2027. Calidades premium.',
        'address': 'Camino de Rosales, 18', 'district': 'Rosales del Canal', 'postal_code': '50012',
        'latitude': 41.6300, 'longitude': -0.8550,
        'property_type': 'apartment', 'price': 310000, 'surface_area': 105,
        'rooms': 4, 'bedrooms': 3, 'bathrooms': 2, 'floor_number': 3, 'total_floors': 6,
        'construction_year': 2027,
        'has_elevator': True, 'has_parking': True, 'has_terrace': True,
        'has_balcony': False, 'has_garden': True, 'has_pool': True,
        'energy_certificate_rating': 'A', 'property_condition': 'en_construccion',
    },
    {
        'external_id': 'DEMO010', 'source': 'habitaclia',
        'url': 'https://www.habitaclia.com/inmueble/DEMO010/',
        'title': 'Piso exterior en San Jose',
        'description': 'Piso luminoso con 3 dormitorios y ascensor.',
        'address': 'Avenida San Jose, 50', 'district': 'San Jose', 'postal_code': '50013',
        'latitude': 41.6420, 'longitude': -0.8700,
        'property_type': 'apartment', 'price': 145000, 'surface_area': 80,
        'rooms': 4, 'bedrooms': 3, 'bathrooms': 1, 'floor_number': 3, 'total_floors': 6,
        'construction_year': 1985,
        'has_elevator': True, 'has_parking': False, 'has_terrace': False,
        'has_balcony': True, 'has_garden': False, 'has_pool': False,
        'energy_certificate_rating': 'D', 'property_condition': 'segunda_mano',
    },
]


def demo_system():
    print("Property Purchase Analysis System - Demo")
    print("=" * 50)

    db = PropertyDatabase()

    print(f"\nInserting {len(SAMPLE_PROPERTIES)} sample properties...")
    for prop_data in SAMPLE_PROPERTIES:
        prop = PropertyModel(**prop_data)
        db.insert_property(prop.to_dict())
        print(f"  + {prop.title} | {prop.price:,.0f} EUR | {prop.property_condition or '?'}")

    stats = db.get_duplicate_stats()
    print(f"\nDatabase stats:")
    print(f"  Total: {stats['total_properties']}")
    print(f"  Active: {stats['active_properties']}")

    # Test deduplication
    print("\nTesting deduplication...")
    deduplicator = PropertyDeduplicator(db)
    test_prop = PropertyModel(**SAMPLE_PROPERTIES[0])
    dupes = deduplicator.find_potential_duplicates(test_prop)
    print(f"  Duplicates for '{test_prop.title}': {len(dupes)}")

    db.close()

    print("\nDone! Start the web app to see properties:")
    print("  python3 app.py")
    print("  Open http://localhost:5000")


if __name__ == "__main__":
    demo_system()
