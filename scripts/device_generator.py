import os
import os
import sys
import random
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
import logging

# Add parent directory to path to import base class
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    # Fallback without faker
    class FakeFaker:
        def street_address(self): return f"{random.randint(100, 9999)} Main St"
        def city(self): return random.choice(["New York", "Los Angeles", "Chicago"])
        def state_abbr(self): return random.choice(["NY", "CA", "IL"])
        def zipcode(self): return f"{random.randint(10000, 99999)}"
        def name(self): return f"User {random.randint(1000, 9999)}"
        def email(self): return f"user{random.randint(100, 999)}@example.com"
        def phone_number(self): return f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        def company(self): return f"Company {random.randint(100, 999)}"
        def first_name(self): return random.choice(["John", "Jane", "Mike", "Sarah"])
        def last_name(self): return random.choice(["Smith", "Johnson", "Wilson", "Brown"])
        def ipv4_private(self): return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
        def mac_address(self): return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
    fake = FakeFaker()

logger = logging.getLogger(__name__)

class DeviceDataGenerator:
    """Generate IoT device and location data for bar management platform"""
    
    def __init__(self, config):
        self.config = config
        self.business_types = [
            'Restaurant', 'Sports Bar', 'Brewery', 'Wine Bar', 'Cocktail Lounge',
            'Sports Grill', 'Pub', 'Nightclub', 'Rooftop Bar', 'Dive Bar'
        ]
        
        self.device_categories = {
            'POS': {
                'types': ['POS Terminal', 'Payment Terminal', 'Order Tablet', 'Cash Register'],
                'base_price': 800,
                'failure_rate': 0.02,  # 2% monthly failure rate
                'usage_pattern': 'peak_hours'  # High usage during meal times
            },
            'Inventory': {
                'types': ['Inventory Scanner', 'Smart Scale', 'Bottle Monitor', 'Keg Monitor'],
                'base_price': 300,
                'failure_rate': 0.01,
                'usage_pattern': 'continuous'  # Continuous monitoring
            },
            'Environmental': {
                'types': ['Temperature Monitor', 'Humidity Sensor', 'Air Quality Monitor'],
                'base_price': 150,
                'failure_rate': 0.005,
                'usage_pattern': 'continuous'
            },
            'Security': {
                'types': ['Security Camera', 'Access Control', 'Motion Detector'],
                'base_price': 400,
                'failure_rate': 0.01,
                'usage_pattern': 'continuous'
            },
            'Entertainment': {
                'types': ['Music System', 'Digital Display', 'TV Controller'],
                'base_price': 600,
                'failure_rate': 0.015,
                'usage_pattern': 'scheduled'  # Based on operating hours
            }
        }
        
        self.location_types = {
            'Main Bar': {'typical_devices': 3, 'revenue_factor': 1.0},  # Reduced from 15
            'Restaurant Area': {'typical_devices': 2, 'revenue_factor': 0.8},  # Reduced from 12
            'Kitchen': {'typical_devices': 2, 'revenue_factor': 0.3},  # Reduced from 8
            'Storage': {'typical_devices': 1, 'revenue_factor': 0.1},  # Reduced from 6
            'Office': {'typical_devices': 1, 'revenue_factor': 0.05},  # Reduced from 4
            'Outdoor Patio': {'typical_devices': 1, 'revenue_factor': 0.6}  # Reduced from 6
        }
        
    def _random_datetime_in_range(self, start_date, end_date):
        """Generate a random datetime between start and end dates"""
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Convert date to datetime if needed
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Convert to timestamps
        start_timestamp = start_date.timestamp()
        end_timestamp = end_date.timestamp()
        
        # Generate random timestamp
        random_timestamp = random.uniform(start_timestamp, end_timestamp)
        
        # Convert back to datetime
        return datetime.fromtimestamp(random_timestamp)
        
    def _random_date_in_range(self, start_date, end_date):
        """Generate a random date between start and end dates"""
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()
            
        # Calculate the difference in days
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        
        # Return the random date
        return start_date + timedelta(days=random_days)
        
    def generate_locations(self, companies: List[Dict]) -> List[Dict]:
        """Generate location data for each company"""
        locations = []
        location_id = 110000000
        
        for company in companies:
            company_id = company['id']
            # Handle different company data structures
            if 'location_count' in company:
                num_locations = company['location_count']
            elif 'properties' in company and 'location_count' in company['properties']:
                num_locations = int(company['properties']['location_count'])
            else:
                num_locations = random.randint(1, 3)
            
            for i in range(num_locations):
                # Get company name from different structures
                if 'name' in company:
                    company_name = company['name']
                elif 'properties' in company and 'name' in company['properties']:
                    company_name = company['properties']['name']
                else:
                    company_name = f"Company {company_id}"
                
                # Location characteristics
                if num_locations == 1:
                    location_name = company_name
                else:
                    location_identifiers = [
                        "Downtown", "Mall", "Airport", "Westside", "Eastside",
                        "North", "South", "Central", "Uptown", "Midtown"
                    ]
                    location_name = f"{company_name} - {random.choice(location_identifiers)}"
                    
                # Location address
                location_address = {
                    'street': fake.street_address(),
                    'city': fake.city(),
                    'state': fake.state_abbr(),
                    'zip_code': fake.zipcode(),
                    'country': 'United States'
                }
                
                # Determine location size and type
                location_size = random.choice(['Small', 'Medium', 'Large', 'XLarge'])
                primary_type = random.choice(list(self.location_types.keys()))
                
                # Calculate expected device count
                base_devices = self.location_types[primary_type]['typical_devices']
                size_multiplier = {'Small': 0.7, 'Medium': 1.0, 'Large': 1.5, 'XLarge': 2.0}[location_size]
                expected_devices = int(base_devices * size_multiplier)
                
                # XS scale override: Force minimal devices for fast testing
                if hasattr(self.config, 'scale') and self.config.scale.value == 'xs':
                    expected_devices = max(1, min(expected_devices, 2))  # Max 2 devices per location
                
                # Get company creation date
                if 'created_date' in company:
                    if isinstance(company['created_date'], str):
                        company_created = datetime.fromisoformat(company['created_date'].replace('Z', ''))
                    else:
                        company_created = datetime.combine(company['created_date'], datetime.min.time())
                elif 'properties' in company and 'createdate' in company['properties']:
                    company_created = datetime.fromisoformat(company['properties']['createdate'].replace('Z', ''))
                else:
                    company_created = datetime.now() - timedelta(days=random.randint(30, 365))
                
                # Get business type
                if 'business_type' in company:
                    business_type = company['business_type']
                elif 'properties' in company and 'business_type' in company['properties']:
                    business_type = company['properties']['business_type']
                else:
                    business_type = random.choice(self.business_types)
                
                location = {
                    'id': str(location_id),
                    'customer_id': company_id,
                    'name': location_name,
                    'address': location_address,
                    'location_type': primary_type,
                    'size_category': location_size,
                    'business_type': business_type,
                    'opening_date': (company_created + timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d'),
                    'expected_device_count': expected_devices,
                    'square_footage': random.randint(1500, 12000),
                    'seating_capacity': random.randint(50, 300),
                    'revenue_potential': random.randint(2000, 15000),
                    'location_status': 'Active',
                    'timezone': 'America/New_York'
                }
                
                locations.append(location)
                location_id += 1
                
        logger.info(f"Generated {len(locations)} locations")
        return locations
        
    def generate_devices(self, locations: List[Dict]) -> List[Dict]:
        """Generate IoT devices for each location"""
        devices = []
        device_id = 120000000
        
        for location in locations:
            location_id = location['id']
            expected_devices = location['expected_device_count']
            
            # Generate device mix based on location type and size
            device_mix = {
                'POS': max(1, int(expected_devices * 0.30)),
                'Inventory': max(1, int(expected_devices * 0.25)),
                'Environmental': max(1, int(expected_devices * 0.15)),
                'Security': max(1, int(expected_devices * 0.20)),
                'Entertainment': max(1, int(expected_devices * 0.10))
            }
            
            for category, device_count in device_mix.items():
                category_info = self.device_categories[category]
                
                for i in range(device_count):
                    device_type = random.choice(category_info['types'])
                    
                    # Device installation date (after location opening)
                    opening_date = datetime.strptime(location['opening_date'], '%Y-%m-%d')
                    install_date = opening_date + timedelta(days=random.randint(0, 30))
                    
                    device = {
                        'id': str(device_id),
                        'location_id': location_id,
                        'device_type': device_type,
                        'category': category,
                        'manufacturer': random.choice(['Generic Corp', 'TechCorp', 'DeviceMaker']),
                        'model': f"Model-{random.randint(100, 999)}",
                        'serial_number': f"SN{random.randint(100000, 999999)}",
                        'install_date': install_date.strftime('%Y-%m-%d'),
                        'warranty_expiry': (install_date + timedelta(days=365)).strftime('%Y-%m-%d'),
                        'purchase_price': category_info['base_price'] * random.uniform(0.8, 1.3),
                        'firmware_version': f"{random.randint(1, 5)}.{random.randint(0, 15)}.{random.randint(0, 99)}",
                        'ip_address': fake.ipv4_private(),
                        'mac_address': fake.mac_address(),
                        'status': random.choice(['Online', 'Online', 'Online', 'Offline']),  # 75% online
                        'usage_pattern': category_info['usage_pattern'],
                        'expected_lifespan_years': random.randint(3, 7),
                        'energy_consumption_watts': random.randint(10, 200),
                        'network_connectivity': random.choice(['WiFi', 'Ethernet', 'Cellular'])
                    }
                    
                    devices.append(device)
                    device_id += 1
                    
        logger.info(f"Generated {len(devices)} IoT devices")
        return devices
        
    def generate_device_events(self, devices: List[Dict]):
        """Generate device event streams with realistic patterns optimized for large-scale data"""
        events = []
        event_id = 130000000
        batch_size = 50000  # Larger batches for better performance
        
        # Calculate date range efficiently
        total_days = (self.config.end_date - self.config.start_date).days
        logger.info(f"Generating device events over {total_days} days for {len(devices)} devices")
        
        for device_idx, device in enumerate(devices):
            device_id = device['id']
            install_date = datetime.strptime(device['install_date'], '%Y-%m-%d').date()
            
            # Start generating events from install date
            current_date = max(install_date, self.config.start_date)
            
            # XS scale: ULTRA-MINIMAL events for very fast testing
            if hasattr(self.config, 'scale') and self.config.scale.value == 'xs':
                # Generate only 1-3 events total per device for entire time period
                num_events_total = random.randint(1, 3)
                for i in range(num_events_total):
                    # Random date in range
                    days_in_range = (self.config.end_date - current_date).days
                    if days_in_range > 0:
                        random_date = current_date + timedelta(days=random.randint(0, days_in_range))
                        event_time = datetime.combine(random_date, datetime.min.time().replace(
                            hour=random.randint(9, 17),
                            minute=random.randint(0, 59),
                            second=random.randint(0, 59)
                        ))
                        
                        event = {
                            'id': str(event_id),
                            'device_id': device_id,
                            'location_id': device['location_id'],
                            'timestamp': event_time.isoformat(),
                            'event_type': 'heartbeat',
                            'status': 'normal',
                            'metrics': {'cpu_usage': random.uniform(10, 50)},
                            'device_category': device.get('category', 'Generic')
                        }
                        
                        events.append(event)
                        event_id += 1
                
                # Skip the complex date loop for XS scale
                continue
            
            # Optimize event generation based on scale and total volume
            total_devices = len(devices)
            if hasattr(self.config, 'scale') and self.config.scale.value == 'xs':
                # XS scale: MINIMAL events for fast testing (100 customers)
                date_step = random.randint(7, 14)  # Weekly sampling only
                base_daily_events = random.randint(1, 3)  # Very few events
            elif hasattr(self.config, 'scale') and self.config.scale.value == 'small':
                # SMALL scale: Much more efficient for testing
                if total_days > 180:  # If more than 6 months, sample heavily
                    date_step = random.randint(7, 14)  # Weekly sampling
                    base_daily_events = random.randint(2, 8)  # Much fewer events
                else:
                    date_step = random.randint(3, 7)  # Every few days
                    base_daily_events = random.randint(5, 15)
            elif total_days > 1000 and total_devices > 20000:
                # ENTERPRISE scale + long timeframe: Optimize for volume
                date_step = random.randint(2, 5)  # Sample every 2-5 days
                base_daily_events = random.randint(3, 15)
            elif total_days > 1000:  # 3+ years, reduce event density
                # Sample every 3-7 days instead of daily for long timeframes
                date_step = random.randint(3, 7)
                base_daily_events = random.randint(5, 25)  # Fewer events per sampled day
            else:
                date_step = 1
                base_daily_events = random.randint(10, 100)
            
            while current_date <= self.config.end_date:
                # Get device usage pattern
                usage_pattern = device.get('usage_pattern', 'continuous')
                
                # Generate events for this date based on device status and patterns
                if device['status'] == 'Online':
                    # Vary events by device category and usage pattern
                    if usage_pattern == 'peak_hours':
                        daily_events = int(base_daily_events * 1.5)  # POS devices more active
                    elif usage_pattern == 'continuous':
                        daily_events = base_daily_events
                    else:  # scheduled
                        daily_events = int(base_daily_events * 0.7)
                else:
                    daily_events = random.randint(0, 3)  # Offline devices minimal events
                
                # Add seasonal variance (bars busier on weekends/holidays)
                if current_date.weekday() >= 5:  # Weekend
                    daily_events = int(daily_events * 1.3)
                
                for event_num in range(daily_events):
                    # Generate event timestamp within the day (business hours weighted)
                    if usage_pattern == 'peak_hours':
                        # Weight towards business hours (11 AM - 11 PM)
                        hour = random.choices(
                            range(24),
                            weights=[1,1,1,1,1,1,1,1,2,3,5,8,8,7,7,8,8,9,9,8,6,4,2,1]
                        )[0]
                    else:
                        hour = random.randint(0, 23)
                    
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    event_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute, second=second))
                    
                    # Event type based on device category
                    category = device.get('category', 'Generic')
                    if category == 'POS':
                        event_types = ['transaction', 'heartbeat', 'status_check', 'error']
                        weights = [60, 25, 10, 5]
                    elif category == 'Inventory':
                        event_types = ['reading', 'heartbeat', 'threshold_alert', 'calibration']
                        weights = [50, 30, 15, 5]
                    else:
                        event_types = ['heartbeat', 'data_reading', 'alert', 'status_change']
                        weights = [40, 40, 15, 5]
                    
                    event_type = random.choices(event_types, weights=weights)[0]
                    
                    # Generate realistic metrics based on device type
                    metrics = {}
                    if category == 'POS':
                        metrics = {
                            'transaction_amount': round(random.uniform(5.50, 125.75), 2) if event_type == 'transaction' else None,
                            'cpu_usage': random.uniform(15, 85),
                            'memory_usage': random.uniform(25, 80),
                            'temperature': random.uniform(22, 45),
                            'network_latency': random.uniform(10, 200)
                        }
                    elif category == 'Inventory':
                        metrics = {
                            'stock_level': random.uniform(0, 100),
                            'weight_reading': random.uniform(0.1, 50.0),
                            'temperature': random.uniform(2, 8) if 'temp' in device['device_type'].lower() else random.uniform(18, 25),
                            'battery_level': random.uniform(20, 100)
                        }
                    else:
                        metrics = {
                            'cpu_usage': random.uniform(10, 75),
                            'memory_usage': random.uniform(20, 70),
                            'temperature': random.uniform(20, 40),
                            'signal_strength': random.uniform(0.3, 1.0)
                        }
                    
                    event = {
                        'id': str(event_id),
                        'device_id': device_id,
                        'location_id': device['location_id'],
                        'timestamp': event_time.isoformat(),
                        'event_type': event_type,
                        'status': 'normal' if event_type != 'error' else random.choice(['normal', 'warning', 'error']),
                        'metrics': {k: v for k, v in metrics.items() if v is not None},
                        'device_category': category
                    }
                    
                    events.append(event)
                    event_id += 1
                    
                    # Yield batches to manage memory efficiently
                    if len(events) >= batch_size:
                        logger.info(f"Generated batch of {len(events)} events (device {device_idx+1}/{len(devices)})")
                        yield events
                        events = []
                        
                current_date += timedelta(days=date_step)
                
            # Progress logging for all scales - more frequent for XS
            if hasattr(self.config, 'scale') and self.config.scale.value == 'xs':
                if (device_idx + 1) % 10 == 0:  # Every 10 devices for XS
                    logger.info(f"XS Scale: Completed {device_idx + 1}/{len(devices)} devices")
            elif (device_idx + 1) % 1000 == 0:
                logger.info(f"Completed event generation for {device_idx + 1}/{len(devices)} devices")
                
        # Yield final batch
        if events:
            logger.info(f"Generated final batch of {len(events)} device events")
            yield events
            
    def generate_user_activity(self, companies: List[Dict], locations: List[Dict]) -> List[Dict]:
        """Generate user activity data for the platform"""
        users = []
        user_id = 140000000
        
        # Group locations by company
        company_locations = {}
        for location in locations:
            customer_id = location['customer_id']
            if customer_id not in company_locations:
                company_locations[customer_id] = []
            company_locations[customer_id].append(location)
            
        for company in companies:
            company_id = company['id']
            company_locations_list = company_locations.get(company_id, [])
            
            # Generate 2-5 users per company
            num_users = random.randint(2, 5)
            
            for i in range(num_users):
                user_role = random.choice([
                    'Owner', 'Manager', 'Assistant Manager', 'Staff', 'Admin'
                ])
                
                # Get company creation date
                if 'created_date' in company:
                    if isinstance(company['created_date'], str):
                        company_created = datetime.fromisoformat(company['created_date'].replace('Z', ''))
                    else:
                        company_created = datetime.combine(company['created_date'], datetime.min.time())
                elif 'properties' in company and 'createdate' in company['properties']:
                    company_created = datetime.fromisoformat(company['properties']['createdate'].replace('Z', ''))
                else:
                    company_created = datetime.now() - timedelta(days=random.randint(30, 365))
                
                user_created = company_created + timedelta(days=random.randint(0, 180))
                
                user = {
                    'id': str(user_id),
                    'customer_id': company_id,
                    'email': fake.email(),
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': user_role,
                    'created_date': user_created.strftime('%Y-%m-%d'),
                    'last_login': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                    'status': random.choice(['Active', 'Active', 'Active', 'Inactive']),  # 75% active
                    'assigned_locations': [loc['id'] for loc in company_locations_list[:2]]  # First 2 locations
                }
                
                users.append(user)
                user_id += 1
                
        logger.info(f"Generated {len(users)} platform users")
        return users

    def generate_feature_usage(self, users: List[Dict]) -> List[Dict]:
        """Generate app_database_feature_usage data with correct schema"""
        logger.info("Generating feature usage data...")
        
        features = [
            'inventory_tracking', 'pos_integration', 'analytics_dashboard',
            'customer_loyalty', 'staff_scheduling', 'menu_management',
            'payment_processing', 'reporting', 'mobile_app', 'api_access'
        ]
        
        usage_data = []
        usage_id = 50000000
        
        for user in users:
            # Scale usage based on role
            role = user.get('role', 'Staff')
            if role in ['Admin', 'Owner']:
                usage_count = random.randint(15, 40)
            elif role in ['Manager']:
                usage_count = random.randint(10, 25)
            else:
                usage_count = random.randint(5, 15)
            
            for _ in range(usage_count):
                usage_data.append({
                    'usage_id': f"usage_{usage_id}",
                    'user_id': int(user['id']),
                    'customer_id': int(user['customer_id']),
                    'feature_name': random.choice(features),
                    'usage_count': random.randint(1, 50),
                    'timestamp': self._random_datetime_in_range(
                        self.config.start_date,
                        self.config.end_date
                    ).isoformat()
                })
                usage_id += 1
        
        logger.info(f"Generated {len(usage_data)} feature usage records")
        return usage_data

    def generate_page_views(self, users: List[Dict]) -> List[Dict]:
        """Generate app_database_page_views data with correct schema"""
        logger.info("Generating page views data...")
        
        pages = [
            ('/dashboard', 'Dashboard'),
            ('/inventory', 'Inventory Management'), 
            ('/analytics', 'Analytics'),
            ('/customers', 'Customer Management'),
            ('/staff', 'Staff Management'),
            ('/reports', 'Reports'),
            ('/settings', 'Settings'),
            ('/billing', 'Billing'),
            ('/support', 'Support'),
            ('/menu', 'Menu Management'),
            ('/pos', 'Point of Sale'),
            ('/loyalty', 'Loyalty Programs')
        ]
        
        page_views = []
        view_id = 60000000
        
        for user in users:
            # Scale page views based on role and activity
            role = user.get('role', 'Staff')
            if role in ['Admin', 'Owner']:
                view_count = random.randint(50, 150)
            elif role in ['Manager']:
                view_count = random.randint(30, 100)
            else:
                view_count = random.randint(15, 60)
            
            for _ in range(view_count):
                page_url, page_title = random.choice(pages)
                
                page_views.append({
                    'page_view_id': f"pv_{view_id}",
                    'session_id': f"sess_{random.randint(1000000, 9999999)}",
                    'user_id': int(user['id']),
                    'customer_id': int(user['customer_id']),
                    'page_url': page_url,
                    'page_title': page_title,
                    'timestamp': self._random_datetime_in_range(
                        self.config.start_date,
                        self.config.end_date
                    ).isoformat(),
                    'time_on_page_seconds': random.randint(10, 600),
                    'referrer_url': random.choice(['/dashboard', '/menu', '/inventory', 'direct', 'search'])
                })
                view_id += 1
        
        logger.info(f"Generated {len(page_views)} page view records")
        return page_views

    def generate_user_sessions(self, users: List[Dict]) -> List[Dict]:
        """Generate app_database_user_sessions data with correct schema"""
        logger.info("Generating user sessions data...")
        
        sessions = []
        session_id = 70000000
        
        for user in users:
            # Scale sessions based on role and activity level
            role = user.get('role', 'Staff')
            if role in ['Admin', 'Owner']:
                session_count = random.randint(100, 300)
            elif role in ['Manager']:
                session_count = random.randint(60, 200)
            else:
                session_count = random.randint(30, 120)
            
            for _ in range(session_count):
                start_time = self._random_datetime_in_range(
                    self.config.start_date,
                    self.config.end_date
                )
                duration = random.randint(300, 7200)  # 5 minutes to 2 hours
                end_time = start_time + timedelta(seconds=duration)
                
                sessions.append({
                    'session_id': f"sess_{session_id}",
                    'user_id': int(user['id']),
                    'customer_id': int(user['customer_id']),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'page_views': random.randint(1, 50),
                    'actions_taken': random.randint(0, 100),
                    'device_type': random.choice(['desktop', 'mobile', 'tablet']),
                    'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge', 'Mobile Safari'])
                })
                session_id += 1
        
        logger.info(f"Generated {len(sessions)} user session records")
        return sessions

    def generate_app_subscriptions(self, companies: List[Dict]) -> List[Dict]:
        """Generate app_database_subscriptions data with correct schema"""
        logger.info("Generating app database subscriptions...")
        
        plans = ['starter', 'professional', 'enterprise']
        statuses = ['active', 'trial', 'past_due', 'canceled', 'paused']
        
        subscriptions = []
        sub_id = 80000000
        
        for company in companies:
            # Most companies have 1 subscription, some have multiple for different locations
            num_subs = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            
            for _ in range(num_subs):
                start_date = self._random_date_in_range(
                    self.config.start_date,
                    self.config.end_date - timedelta(days=30)
                )
                
                plan = random.choice(plans)
                status = random.choices(statuses, weights=[0.7, 0.1, 0.05, 0.1, 0.05])[0]
                
                # Price based on plan
                if plan == 'starter':
                    price = 49.99
                elif plan == 'professional':
                    price = 99.99
                else:  # enterprise
                    price = 199.99
                
                subscription = {
                    'id': sub_id,
                    'customer_id': int(company['id']),
                    'plan_name': plan,
                    'status': status,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': None if status in ['active', 'trial'] else self._random_date_in_range(
                        start_date + timedelta(days=30),
                        self.config.end_date
                    ).strftime('%Y-%m-%d'),
                    'monthly_price': price,
                    'billing_cycle': random.choice(['monthly', 'annual'])
                }
                
                subscriptions.append(subscription)
                sub_id += 1
        
        logger.info(f"Generated {len(subscriptions)} app database subscription records")
        return subscriptions
