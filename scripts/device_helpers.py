            'Motion Detector': (2, 8),
            'Music System': (50, 200),
            'Digital Display': (100, 400),
            'TV Controller': (3, 12)
        }
        
        min_watts, max_watts = consumption_ranges.get(device_type, (5, 25))
        return random.randint(min_watts, max_watts)
        
    def _determine_data_frequency(self, category: str) -> str:
        """Determine how often device sends data"""
        frequency_mapping = {
            'POS': 'per_transaction',        # Data sent with each transaction
            'Inventory': 'every_15_minutes', # Regular inventory updates
            'Environmental': 'every_5_minutes', # Frequent environmental monitoring
            'Security': 'continuous',        # Continuous security monitoring
            'Entertainment': 'hourly'        # Usage statistics hourly
        }
        return frequency_mapping.get(category, 'hourly')
        
    def _calculate_daily_events(self, device: Dict, date: date) -> int:
        """Calculate number of events per day for a device"""
        usage_pattern = device['usage_pattern']
        category = device['category']
        
        # Base events per day by usage pattern
        base_events = {
            'continuous': 288,      # Every 5 minutes = 288 events/day
            'peak_hours': 180,      # More events during business hours
            'scheduled': 24,        # Hourly events
            'per_transaction': 150  # Variable based on transaction volume
        }
        
        daily_events = base_events.get(usage_pattern, 24)
        
        # Adjust for day of week (weekend vs weekday)
        if date.weekday() >= 5:  # Weekend
            daily_events = int(daily_events * random.uniform(0.6, 0.8))
        else:  # Weekday
            daily_events = int(daily_events * random.uniform(0.9, 1.1))
            
        # Add some randomness
        return max(1, int(daily_events * random.uniform(0.7, 1.3)))
        
    def _generate_event_timestamp(self, date: date, device: Dict) -> datetime:
        """Generate realistic event timestamp within a day"""
        usage_pattern = device['usage_pattern']
        
        if usage_pattern == 'peak_hours':
            # Concentrate events during business hours (11 AM - 11 PM)
            hour = random.choices(
                range(24),
                weights=[1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 5, 8, 10, 8, 6, 8, 10, 12, 10, 8, 6, 4, 2, 1]
            )[0]
        elif usage_pattern == 'scheduled':
            # Regular hourly intervals
            hour = random.randint(6, 23)  # During waking hours
        else:
            # Continuous or per_transaction - any time
            hour = random.randint(0, 23)
            
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute, second=second))
        
    def _generate_device_event_data(self, device: Dict, timestamp: datetime) -> Dict:
        """Generate event data based on device type and category"""
        category = device['category']
        device_type = device['device_type']
        
        if category == 'POS':
            return self._generate_pos_event_data(device_type, timestamp)
        elif category == 'Inventory':
            return self._generate_inventory_event_data(device_type, timestamp)
        elif category == 'Environmental':
            return self._generate_environmental_event_data(device_type, timestamp)
        elif category == 'Security':
            return self._generate_security_event_data(device_type, timestamp)
        elif category == 'Entertainment':
            return self._generate_entertainment_event_data(device_type, timestamp)
        else:
            return self._generate_generic_event_data(device_type, timestamp)
            
    def _generate_pos_event_data(self, device_type: str, timestamp: datetime) -> Dict:
        """Generate POS system event data"""
        event_types = ['transaction', 'heartbeat', 'error', 'maintenance']
        event_type = random.choices(event_types, weights=[70, 25, 3, 2])[0]
        
        base_data = {
            'event_type': event_type,
            'status': 'normal',
            'metrics': {
                'cpu_usage_percent': random.uniform(10, 80),
                'memory_usage_percent': random.uniform(20, 75),
                'disk_usage_percent': random.uniform(30, 85),
                'uptime_hours': random.uniform(0, 720),  # Up to 30 days
                'network_latency_ms': random.uniform(10, 100)
            }
        }
        
        if event_type == 'transaction':
            base_data['metrics'].update({
                'transaction_amount': round(random.uniform(5.0, 150.0), 2),
                'payment_method': random.choice(['credit', 'debit', 'cash', 'mobile']),
                'transaction_duration_seconds': random.uniform(15, 120),
                'items_count': random.randint(1, 15)
            })
        elif event_type == 'error':
            base_data['status'] = 'error'
            base_data['metrics']['error_code'] = random.choice(['E001', 'E002', 'E003', 'E004'])
            base_data['alerts'] = ['Payment processing error detected']
            
        return base_data
        
    def _generate_inventory_event_data(self, device_type: str, timestamp: datetime) -> Dict:
        """Generate inventory monitoring event data"""
        if 'Monitor' in device_type:
            # Bottle/Keg monitors
            return {
                'event_type': 'inventory_reading',
                'status': 'normal',
                'metrics': {
                    'fill_level_percent': random.uniform(0, 100),
                    'temperature_celsius': random.uniform(2, 8),  # Cold storage
                    'flow_rate_ml_per_minute': random.uniform(0, 500),
                    'consumption_rate_daily': random.uniform(50, 95),
                    'estimated_empty_hours': random.uniform(2, 48)
                }
            }
        else:
            # Scanners and scales
            return {
                'event_type': 'inventory_scan',
                'status': 'normal',
                'metrics': {
                    'items_scanned': random.randint(1, 50),
                    'scan_accuracy_percent': random.uniform(95, 100),
                    'processing_time_seconds': random.uniform(0.5, 5.0),
                    'battery_level_percent': random.uniform(20, 100),
                    'signal_strength_dbm': random.uniform(-80, -30)
                }
            }
            
    def _generate_environmental_event_data(self, device_type: str, timestamp: datetime) -> Dict:
        """Generate environmental monitoring event data"""
        alerts = []
        
        if 'Temperature' in device_type:
            temp = random.uniform(18, 26)  # 64-79°F
            if temp > 25:
                alerts.append('High temperature detected')
            elif temp < 19:
                alerts.append('Low temperature detected')
                
            return {
                'event_type': 'environmental_reading',
                'status': 'normal' if not alerts else 'warning',
                'metrics': {
                    'temperature_celsius': round(temp, 1),
                    'temperature_fahrenheit': round(temp * 9/5 + 32, 1),
                    'sensor_accuracy': random.uniform(0.98, 1.0),
                    'calibration_drift': random.uniform(-0.5, 0.5)
                },
                'alerts': alerts
            }
        elif 'Humidity' in device_type:
            humidity = random.uniform(30, 70)
            if humidity > 65:
                alerts.append('High humidity detected')
            elif humidity < 35:
                alerts.append('Low humidity detected')
                
            return {
                'event_type': 'environmental_reading',
                'status': 'normal' if not alerts else 'warning',
                'metrics': {
                    'humidity_percent': round(humidity, 1),
                    'dew_point_celsius': round(random.uniform(10, 20), 1),
                    'sensor_drift': random.uniform(-2, 2)
                },
                'alerts': alerts
            }
        else:  # Air Quality
            aqi = random.randint(25, 150)
            if aqi > 100:
                alerts.append('Poor air quality detected')
                
            return {
                'event_type': 'air_quality_reading',
                'status': 'normal' if not alerts else 'warning',
                'metrics': {
                    'air_quality_index': aqi,
                    'pm25_ugm3': random.uniform(5, 35),
                    'pm10_ugm3': random.uniform(10, 50),
                    'co2_ppm': random.uniform(400, 1200),
                    'voc_ppb': random.uniform(10, 300)
                },
                'alerts': alerts
            }
            
    def _generate_security_event_data(self, device_type: str, timestamp: datetime) -> Dict:
        """Generate security system event data"""
        if 'Camera' in device_type:
            motion_detected = random.random() < 0.15  # 15% chance of motion
            
            return {
                'event_type': 'motion_detection' if motion_detected else 'heartbeat',
                'status': 'normal',
                'metrics': {
                    'motion_detected': motion_detected,
                    'confidence_score': random.uniform(0.7, 0.95) if motion_detected else 0,
                    'recording_quality': random.choice(['HD', '4K', '1080p']),
                    'storage_usage_percent': random.uniform(40, 85),
                    'network_bandwidth_mbps': random.uniform(5, 25)
                }
            }
        elif 'Access' in device_type:
            access_attempt = random.random() < 0.05  # 5% chance of access attempt
            
            return {
                'event_type': 'access_attempt' if access_attempt else 'heartbeat',
                'status': 'normal',
                'metrics': {
                    'access_granted': random.choice([True, False]) if access_attempt else None,
                    'card_id': f"CARD{random.randint(1000, 9999)}" if access_attempt else None,
                    'door_status': random.choice(['locked', 'unlocked']),
                    'tamper_detected': random.random() < 0.01,  # 1% chance
                    'power_source': random.choice(['mains', 'battery'])
                }
            }
        else:  # Motion Detector
            motion = random.random() < 0.20  # 20% chance of motion
            
            return {
                'event_type': 'motion_detection' if motion else 'heartbeat',
                'status': 'normal',
                'metrics': {
                    'motion_detected': motion,
                    'sensitivity_level': random.randint(1, 10),
                    'detection_range_meters': random.uniform(5, 15),
                    'battery_voltage': random.uniform(3.0, 4.5),
                    'false_alarm_rate': random.uniform(0.01, 0.05)
                }
            }
            
    def _generate_entertainment_event_data(self, device_type: str, timestamp: datetime) -> Dict:
        """Generate entertainment system event data"""
        if 'Music' in device_type:
            return {
                'event_type': 'audio_status',
                'status': 'normal',
                'metrics': {
                    'volume_level': random.randint(20, 80),
                    'audio_quality': random.choice(['High', 'Medium', 'Low']),
                    'playlist_position': random.randint(1, 100),
                    'streaming_bitrate_kbps': random.randint(128, 320),
                    'speaker_zones_active': random.randint(1, 6)
                }
            }
        elif 'Display' in device_type:
            return {
                'event_type': 'display_status',
                'status': 'normal',
                'metrics': {
                    'brightness_percent': random.randint(60, 100),
                    'content_type': random.choice(['menu', 'promotions', 'sports', 'news']),
                    'display_hours_today': random.uniform(8, 16),
                    'pixel_errors': random.randint(0, 5),
                    'power_consumption_watts': random.uniform(100, 300)
                }
            }
        else:  # TV Controller
            return {
                'event_type': 'streaming_status',
                'status': 'normal',
                'metrics': {
                    'channel_number': random.randint(1, 500),
                    'streaming_service': random.choice(['Netflix', 'Hulu', 'ESPN', 'YouTube']),
                    'buffer_health_percent': random.uniform(80, 100),
                    'resolution': random.choice(['1080p', '4K', '720p']),
                    'data_usage_mb_hour': random.uniform(500, 3000)
                }
            }
            
    def _generate_generic_event_data(self, device_type: str, timestamp: datetime) -> Dict:
        """Generate generic event data for unknown device types"""
        return {
            'event_type': 'heartbeat',
            'status': 'normal',
            'metrics': {
                'uptime_hours': random.uniform(0, 720),
                'signal_strength': random.uniform(0.5, 1.0),
                'battery_level_percent': random.uniform(20, 100),
                'error_count_24h': random.randint(0, 3)
            }
        }
        
    def _generate_user_creation_date(self, company_created: datetime) -> str:
        """Generate user creation date relative to company creation"""
        # Users created within 180 days of company creation
        days_offset = random.randint(0, 180)
        user_created = company_created + timedelta(days=days_offset)
        return user_created.strftime('%Y-%m-%d')
        
    def _generate_last_login_date(self) -> str:
        """Generate realistic last login date"""
        # Most users logged in within last 30 days
        days_ago = random.choices(
            range(0, 90),
            weights=[20] + [15] * 7 + [10] * 7 + [5] * 14 + [2] * 30 + [1] * 31
        )[0]
        
        last_login = datetime.now().date() - timedelta(days=days_ago)
        return last_login.strftime('%Y-%m-%d')
        
    def _generate_user_permissions(self, role: str) -> List[str]:
        """Generate user permissions based on role"""
        all_permissions = [
            'view_dashboard', 'view_analytics', 'view_reports', 'export_data',
            'manage_inventory', 'manage_devices', 'manage_users', 'manage_locations',
            'view_financial', 'manage_billing', 'admin_settings', 'api_access'
        ]
        
        role_permissions = {
            'Owner': all_permissions,
            'Regional Manager': [
                'view_dashboard', 'view_analytics', 'view_reports', 'export_data',
                'manage_inventory', 'manage_devices', 'manage_locations', 'view_financial'
            ],
            'Manager': [
                'view_dashboard', 'view_analytics', 'view_reports',
                'manage_inventory', 'manage_devices'
            ],
            'Assistant Manager': [
                'view_dashboard', 'view_reports', 'manage_inventory'
            ],
            'Staff': [
                'view_dashboard'
            ],
            'Admin': [
                'view_dashboard', 'view_analytics', 'manage_users', 'admin_settings'
            ],
            'Viewer': [
                'view_dashboard', 'view_reports'
            ]
        }
        
        return role_permissions.get(role, ['view_dashboard'])