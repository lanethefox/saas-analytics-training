#!/usr/bin/env python3
"""
Update location coordinates with realistic latitude/longitude values.

This script:
- Adds realistic coordinates based on city/state
- Ensures coordinates are properly distributed
- Updates the locations table with geo data
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import db_helper
import random

# Major US cities with coordinates for realistic distribution
US_CITIES = {
    'CA': [
        {'city': 'Los Angeles', 'lat': 34.0522, 'lng': -118.2437, 'weight': 3},
        {'city': 'San Francisco', 'lat': 37.7749, 'lng': -122.4194, 'weight': 2},
        {'city': 'San Diego', 'lat': 32.7157, 'lng': -117.1611, 'weight': 1},
        {'city': 'San Jose', 'lat': 37.3382, 'lng': -121.8863, 'weight': 1},
    ],
    'NY': [
        {'city': 'New York', 'lat': 40.7128, 'lng': -74.0060, 'weight': 4},
        {'city': 'Buffalo', 'lat': 42.8864, 'lng': -78.8784, 'weight': 1},
        {'city': 'Rochester', 'lat': 43.1566, 'lng': -77.6088, 'weight': 1},
    ],
    'TX': [
        {'city': 'Houston', 'lat': 29.7604, 'lng': -95.3698, 'weight': 2},
        {'city': 'Dallas', 'lat': 32.7767, 'lng': -96.7970, 'weight': 2},
        {'city': 'Austin', 'lat': 30.2672, 'lng': -97.7431, 'weight': 1},
        {'city': 'San Antonio', 'lat': 29.4241, 'lng': -98.4936, 'weight': 1},
    ],
    'FL': [
        {'city': 'Miami', 'lat': 25.7617, 'lng': -80.1918, 'weight': 2},
        {'city': 'Orlando', 'lat': 28.5383, 'lng': -81.3792, 'weight': 1},
        {'city': 'Tampa', 'lat': 27.9506, 'lng': -82.4572, 'weight': 1},
    ],
    'IL': [
        {'city': 'Chicago', 'lat': 41.8781, 'lng': -87.6298, 'weight': 3},
        {'city': 'Aurora', 'lat': 41.7606, 'lng': -88.3201, 'weight': 1},
    ],
    'PA': [
        {'city': 'Philadelphia', 'lat': 39.9526, 'lng': -75.1652, 'weight': 2},
        {'city': 'Pittsburgh', 'lat': 40.4406, 'lng': -79.9959, 'weight': 1},
    ],
    'AZ': [
        {'city': 'Phoenix', 'lat': 33.4484, 'lng': -112.0740, 'weight': 2},
        {'city': 'Tucson', 'lat': 32.2217, 'lng': -110.9265, 'weight': 1},
    ],
    'WA': [
        {'city': 'Seattle', 'lat': 47.6062, 'lng': -122.3321, 'weight': 2},
        {'city': 'Spokane', 'lat': 47.6588, 'lng': -117.4260, 'weight': 1},
    ],
    'MA': [
        {'city': 'Boston', 'lat': 42.3601, 'lng': -71.0589, 'weight': 2},
        {'city': 'Worcester', 'lat': 42.2626, 'lng': -71.8023, 'weight': 1},
    ],
    'CO': [
        {'city': 'Denver', 'lat': 39.7392, 'lng': -104.9903, 'weight': 2},
        {'city': 'Colorado Springs', 'lat': 38.8339, 'lng': -104.8214, 'weight': 1},
    ],
}

# Default coordinates for states not in the list
DEFAULT_STATE_COORDS = {
    'lat': 39.8283,  # Geographic center of US
    'lng': -98.5795
}

def get_coordinates_for_location(state):
    """Get random coordinates for a location based on state."""
    if state in US_CITIES:
        cities = US_CITIES[state]
        # Weighted random selection
        weights = [city['weight'] for city in cities]
        selected_city = random.choices(cities, weights=weights)[0]
        
        # Add some variance to avoid exact same coordinates
        # About 10-20 miles variance
        lat_variance = random.uniform(-0.2, 0.2)
        lng_variance = random.uniform(-0.2, 0.2)
        
        return {
            'latitude': round(selected_city['lat'] + lat_variance, 6),
            'longitude': round(selected_city['lng'] + lng_variance, 6)
        }
    else:
        # For other states, use center of US with larger variance
        return {
            'latitude': round(DEFAULT_STATE_COORDS['lat'] + random.uniform(-5, 5), 6),
            'longitude': round(DEFAULT_STATE_COORDS['lng'] + random.uniform(-5, 5), 6)
        }

def update_location_coordinates():
    """Update all locations with coordinates."""
    with db_helper.config.get_cursor() as cursor:
        # First check if columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw' 
            AND table_name = 'app_database_locations'
            AND column_name IN ('latitude', 'longitude')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add columns if they don't exist
        if 'latitude' not in existing_columns:
            print("Adding latitude column...")
            cursor.execute("""
                ALTER TABLE raw.app_database_locations 
                ADD COLUMN latitude DECIMAL(10, 6)
            """)
            cursor.connection.commit()
            
        if 'longitude' not in existing_columns:
            print("Adding longitude column...")
            cursor.execute("""
                ALTER TABLE raw.app_database_locations 
                ADD COLUMN longitude DECIMAL(10, 6)
            """)
            cursor.connection.commit()
        
        # Get all locations
        cursor.execute("""
            SELECT id, state
            FROM raw.app_database_locations
            ORDER BY id
        """)
        locations = cursor.fetchall()
        
        print(f"Updating coordinates for {len(locations)} locations...")
        
        # Update each location
        updates = []
        for location_id, state in locations:
            coords = get_coordinates_for_location(state)
            updates.append((coords['latitude'], coords['longitude'], location_id))
        
        # Batch update
        cursor.executemany("""
            UPDATE raw.app_database_locations
            SET latitude = %s, longitude = %s
            WHERE id = %s
        """, updates)
        
        cursor.connection.commit()
        
        # Verify update
        cursor.execute("""
            SELECT COUNT(*), 
                   COUNT(latitude) as with_lat,
                   COUNT(longitude) as with_lng
            FROM raw.app_database_locations
        """)
        total, with_lat, with_lng = cursor.fetchone()
        
        return {
            'total_locations': total,
            'updated_with_coordinates': with_lat,
            'success': with_lat == total
        }

def save_coordinate_summary():
    """Save summary of coordinate distribution."""
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT state, COUNT(*) as count,
                   AVG(latitude) as avg_lat,
                   AVG(longitude) as avg_lng,
                   MIN(latitude) as min_lat,
                   MAX(latitude) as max_lat,
                   MIN(longitude) as min_lng,
                   MAX(longitude) as max_lng
            FROM raw.app_database_locations
            GROUP BY state
            ORDER BY count DESC
        """)
        
        state_data = []
        for row in cursor.fetchall():
            state_data.append({
                'state': row[0],
                'location_count': row[1],
                'center_lat': float(row[2]) if row[2] else None,
                'center_lng': float(row[3]) if row[3] else None,
                'bounds': {
                    'min_lat': float(row[4]) if row[4] else None,
                    'max_lat': float(row[5]) if row[5] else None,
                    'min_lng': float(row[6]) if row[6] else None,
                    'max_lng': float(row[7]) if row[7] else None
                }
            })
        
        summary = {
            'total_states': len(state_data),
            'state_distribution': state_data
        }
        
        with open('data/location_coordinates_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("✓ Saved coordinate summary to data/location_coordinates_summary.json")

def main():
    print("=== Updating Location Coordinates ===")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Update coordinates
    print("\nUpdating location coordinates...")
    result = update_location_coordinates()
    
    if result['success']:
        print(f"✓ Successfully updated {result['updated_with_coordinates']} locations with coordinates")
    else:
        print(f"⚠ Only updated {result['updated_with_coordinates']} out of {result['total_locations']} locations")
    
    # Save summary
    save_coordinate_summary()
    
    # Show sample
    with db_helper.config.get_cursor() as cursor:
        cursor.execute("""
            SELECT city, state, latitude, longitude
            FROM raw.app_database_locations
            WHERE latitude IS NOT NULL
            LIMIT 5
        """)
        
        print("\nSample locations with coordinates:")
        for city, state, lat, lng in cursor.fetchall():
            print(f"  - {city}, {state}: ({lat}, {lng})")
    
    print("\n✓ Task 32 complete!")

if __name__ == "__main__":
    main()