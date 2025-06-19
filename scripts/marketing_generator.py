import os
import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker
from typing import Dict, List, Tuple, Optional
import logging

# Add parent directory to path to import base class
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

fake = Faker()
logger = logging.getLogger(__name__)

class BusinessEntityGenerator:
    """Base class for generating business entities with realistic patterns"""
    
    def __init__(self, config):
        self.config = config
        self.business_types = [
            'Restaurant', 'Sports Bar', 'Brewery', 'Wine Bar', 'Cocktail Lounge',
            'Sports Grill', 'Pub', 'Nightclub', 'Rooftop Bar', 'Dive Bar'
        ]
        
    def generate_business_name(self, business_type: str) -> str:
        """Generate realistic business names"""
        prefixes = {
            'Restaurant': ['The', 'Villa', 'Casa', 'Chez'],
            'Sports Bar': ['Sports', 'Champions', 'MVP', 'Stadium'],
            'Brewery': ['Craft', 'Local', 'Artisan', 'Barrel'],
            'Wine Bar': ['Vintage', 'Cork', 'Grape', 'Cellar'],
            'Cocktail Lounge': ['Mixology', 'Craft', 'Premium', 'Elite'],
            'Sports Grill': ['Grill', 'BBQ', 'Fire', 'Smoke'],
            'Pub': ['Irish', 'Corner', 'Local', 'Traditional'],
            'Nightclub': ['Club', 'Neon', 'Electric', 'Pulse'],
            'Rooftop Bar': ['Sky', 'Rooftop', 'Heights', 'View'],
            'Dive Bar': ['Corner', 'Local', 'Neighborhood', 'Classic']
        }
        
        suffixes = {
            'Restaurant': ['Bistro', 'Kitchen', 'Table', 'House'],
            'Sports Bar': ['Sports Bar', 'Grill', 'Tavern'],
            'Brewery': ['Brewing', 'Brewery', 'Beer Co'],
            'Wine Bar': ['Wine Bar', 'Cellars', 'Vintners'],
            'Cocktail Lounge': ['Lounge', 'Bar', 'Cocktails'],
            'Sports Grill': ['Grill', 'BBQ', 'Kitchen'],
            'Pub': ['Pub', 'Tavern', 'Inn'],
            'Nightclub': ['Club', 'Lounge', 'Scene'],
            'Rooftop Bar': ['Rooftop', 'Sky Bar', 'Heights'],
            'Dive Bar': ['Bar', 'Tavern', 'Saloon']
        }
        
        prefix = random.choice(prefixes.get(business_type, ['The']))
        name = fake.company().replace('Group', '').replace('Inc', '').replace('LLC', '').strip()
        suffix = random.choice(suffixes.get(business_type, ['Bar']))
        
        return f"{prefix} {name} {suffix}"

import os
import sys
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker
from typing import Dict, List, Tuple, Optional
import uuid
import argparse
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Faker with consistent seed for reproducibility
fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

class DataScale(Enum):
    """Data generation scale options"""
    XS = "xs"               # 100 customers for quick testing
    SMALL = "small"         # 1,000 customers for testing
    ENTERPRISE = "enterprise" # 40,000 customers for full enterprise scale

@dataclass
class PlatformConfig:
    """Configuration for synthetic data generation"""
    scale: DataScale
    start_date: date
    end_date: date
    
    # Scale-based sizing
    customers: int
    locations_per_customer: Tuple[int, int]  # (min, max)
    devices_per_location: Tuple[int, int]    # (min, max)
    
    # Business parameters
    trial_conversion_rate: float = 0.65
    monthly_churn_rate: float = 0.08
    expansion_probability: float = 0.15
    support_ticket_rate: float = 0.12  # tickets per customer per month

    @classmethod
    def create(cls, scale: str, months_back: int = 24) -> 'PlatformConfig':
        """Create configuration based on scale"""
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)
        
        scale_enum = DataScale(scale)
        
        if scale_enum == DataScale.XS:
            return cls(
                scale=scale_enum,
                start_date=start_date,
                end_date=end_date,
                customers=100,
                locations_per_customer=(1, 4),
                devices_per_location=(2, 8)
            )
        elif scale_enum == DataScale.SMALL:
            return cls(
                scale=scale_enum,
                start_date=start_date,
                end_date=end_date,
                customers=1000,
                locations_per_customer=(1, 8),
                devices_per_location=(3, 15)
            )
        else:  # ENTERPRISE
            return cls(
                scale=scale_enum,
                start_date=start_date,
                end_date=end_date,
                customers=40000,
                locations_per_customer=(1, 20),
                devices_per_location=(3, 30)
            )

class BusinessEntityGenerator:
    """Base class for generating business entities with realistic patterns"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.business_types = [
            'Restaurant', 'Sports Bar', 'Brewery', 'Wine Bar', 'Cocktail Lounge',
            'Sports Grill', 'Pub', 'Nightclub', 'Rooftop Bar', 'Dive Bar'
        ]
        
        self.device_types = [
            'POS Terminal', 'Inventory Scanner', 'Temperature Monitor', 
            'Security Camera', 'Music System', 'Payment Terminal',
            'Kitchen Display', 'Order Tablet', 'Cash Register'
        ]
        
    def generate_business_name(self, business_type: str) -> str:
        """Generate realistic business names"""
        prefixes = {
            'Restaurant': ['The', 'Villa', 'Casa', 'Chez'],
            'Sports Bar': ['Sports', 'Champions', 'MVP', 'Stadium'],
            'Brewery': ['Craft', 'Local', 'Artisan', 'Barrel'],
            'Wine Bar': ['Vintage', 'Cork', 'Grape', 'Cellar'],
            'Cocktail Lounge': ['Mixology', 'Craft', 'Premium', 'Elite'],
            'Sports Grill': ['Grill', 'BBQ', 'Fire', 'Smoke'],
            'Pub': ['Irish', 'Corner', 'Local', 'Traditional'],
            'Nightclub': ['Club', 'Neon', 'Electric', 'Pulse'],
            'Rooftop Bar': ['Sky', 'Rooftop', 'Heights', 'View'],
            'Dive Bar': ['Corner', 'Local', 'Neighborhood', 'Classic']
        }
        
        suffixes = {
            'Restaurant': ['Bistro', 'Kitchen', 'Table', 'House'],
            'Sports Bar': ['Sports Bar', 'Grill', 'Tavern'],
            'Brewery': ['Brewing', 'Brewery', 'Beer Co'],
            'Wine Bar': ['Wine Bar', 'Cellars', 'Vintners'],
            'Cocktail Lounge': ['Lounge', 'Bar', 'Cocktails'],
            'Sports Grill': ['Grill', 'BBQ', 'Kitchen'],
            'Pub': ['Pub', 'Tavern', 'Inn'],
            'Nightclub': ['Club', 'Lounge', 'Scene'],
            'Rooftop Bar': ['Rooftop', 'Sky Bar', 'Heights'],
            'Dive Bar': ['Bar', 'Tavern', 'Saloon']
        }
        
        prefix = random.choice(prefixes.get(business_type, ['The']))
        name = fake.company().replace('Group', '').replace('Inc', '').replace('LLC', '').strip()
        suffix = random.choice(suffixes.get(business_type, ['Bar']))
        
        return f"{prefix} {name} {suffix}"

class MarketingDataGenerator(BusinessEntityGenerator):
    """Generate marketing attribution and campaign performance data"""
    
    def __init__(self, config):
        super().__init__(config)
        self.channels = {
            'google_ads': {
                'campaign_types': ['Search', 'Display', 'Video', 'Shopping'],
                'avg_cpc': {'Search': 3.50, 'Display': 1.20, 'Video': 0.15, 'Shopping': 0.80},
                'avg_ctr': {'Search': 0.035, 'Display': 0.008, 'Video': 0.025, 'Shopping': 0.012}
            },
            'facebook_ads': {
                'campaign_types': ['Traffic', 'Conversions', 'Brand Awareness', 'Lead Generation'],
                'avg_cpc': {'Traffic': 1.80, 'Conversions': 2.40, 'Brand Awareness': 0.90, 'Lead Generation': 2.80},
                'avg_ctr': {'Traffic': 0.015, 'Conversions': 0.022, 'Brand Awareness': 0.008, 'Lead Generation': 0.018}
            },
            'linkedin_ads': {
                'campaign_types': ['Single Image Ad', 'Carousel Ad', 'Video Ad', 'Lead Gen Form'],
                'avg_cpc': {'Single Image Ad': 5.20, 'Carousel Ad': 4.80, 'Video Ad': 3.90, 'Lead Gen Form': 6.50},
                'avg_ctr': {'Single Image Ad': 0.008, 'Carousel Ad': 0.012, 'Video Ad': 0.015, 'Lead Gen Form': 0.025}
            }
        }
        
        self.audience_segments = [
            'Restaurant Owners', 'Bar Managers', 'Hospitality Directors',
            'Multi-Location Operators', 'Franchise Owners', 'Food Service Directors'
        ]
        
        self.campaign_objectives = [
            'Lead Generation', 'Brand Awareness', 'Website Traffic', 
            'Demo Requests', 'Trial Signups', 'Customer Acquisition'
        ]
        
    def _safe_timestamp(self, dt_obj) -> int:
        """Safely convert date or datetime to timestamp"""
        if isinstance(dt_obj, datetime):
            return int(dt_obj.timestamp())
        else:  # date object
            return int(datetime.combine(dt_obj, datetime.min.time()).timestamp())
        
    def generate_google_ads_campaigns(self, companies: List[Dict]) -> List[Dict]:
        """Generate Google Ads campaign performance data"""
        campaigns = []
        campaign_id = 80000000
        
        # Calculate campaign duration based on config date range
        total_days = (self.config.end_date - self.config.start_date).days
        
        # Generate 15-25 campaigns for the period
        num_campaigns = random.randint(15, 25)
        
        for i in range(num_campaigns):
            campaign_type = random.choice(self.channels['google_ads']['campaign_types'])
            
            # Campaign timing
            start_offset = random.randint(0, max(1, total_days - 30))
            campaign_start = self.config.start_date + timedelta(days=start_offset)
            campaign_end = min(
                campaign_start + timedelta(days=random.randint(30, 90)),
                self.config.end_date
            )
            
            # Campaign performance metrics
            daily_budget = random.randint(100, 1000)
            total_spend = self._calculate_campaign_spend(daily_budget, campaign_start, campaign_end)
            
            avg_cpc = self.channels['google_ads']['avg_cpc'][campaign_type]
            actual_cpc = avg_cpc * random.uniform(0.7, 1.3)  # Add variance
            
            clicks = int(total_spend / actual_cpc)
            
            avg_ctr = self.channels['google_ads']['avg_ctr'][campaign_type]
            actual_ctr = avg_ctr * random.uniform(0.5, 1.5)
            
            impressions = int(clicks / actual_ctr) if actual_ctr > 0 else 0
            
            # Conversion tracking
            conversion_rate = random.uniform(0.02, 0.08)  # 2-8% conversion rate
            conversions = int(clicks * conversion_rate)
            
            campaign = {
                'id': str(campaign_id),
                'name': self._generate_campaign_name('Google Ads', campaign_type, i),
                'status': 'ENABLED' if campaign_end >= self.config.end_date else 'PAUSED',
                'type': campaign_type,
                'advertising_channel_type': self._map_google_channel_type(campaign_type),
                'start_date': campaign_start.strftime('%Y-%m-%d'),
                'end_date': campaign_end.strftime('%Y-%m-%d') if campaign_end < self.config.end_date else None,
                'budget': {
                    'amount': daily_budget * 1000000,  # Google Ads uses micros
                    'delivery_method': 'STANDARD'
                },
                'targeting_settings': {
                    'target_audience': random.choice(self.audience_segments),
                    'geographic_targeting': random.choice(['United States', 'North America', 'Major Cities'])
                },
                'performance_stats': {
                    'impressions': impressions,
                    'clicks': clicks,
                    'cost': int(total_spend * 1000000),  # Micros
                    'conversions': conversions,
                    'ctr': actual_ctr,
                    'average_cpc': int(actual_cpc * 1000000),
                    'conversion_rate': conversion_rate,
                    'cost_per_conversion': total_spend / conversions if conversions > 0 else 0
                },
                'campaign_objective': random.choice(self.campaign_objectives)
            }
            
            campaigns.append(campaign)
            campaign_id += 1
            
        logger.info(f"Generated {len(campaigns)} Google Ads campaigns")
        return campaigns

    def generate_facebook_ads_campaigns(self, companies: List[Dict]) -> List[Dict]:
        """Generate Facebook Ads campaign performance data"""
        campaigns = []
        campaign_id = 95000000
        
        total_days = (self.config.end_date - self.config.start_date).days
        num_campaigns = random.randint(10, 20)
        
        for i in range(num_campaigns):
            campaign_type = random.choice(self.channels['facebook_ads']['campaign_types'])
            
            # Campaign timing
            start_offset = random.randint(0, max(1, total_days - 30))
            campaign_start = self.config.start_date + timedelta(days=start_offset)
            campaign_end = min(
                campaign_start + timedelta(days=random.randint(30, 90)),
                self.config.end_date
            )
            
            # Campaign performance metrics
            daily_budget = random.randint(50, 500)
            total_spend = self._calculate_campaign_spend(daily_budget, campaign_start, campaign_end)
            
            avg_cpc = self.channels['facebook_ads']['avg_cpc'][campaign_type]
            actual_cpc = avg_cpc * random.uniform(0.7, 1.3)
            
            clicks = int(total_spend / actual_cpc)
            
            avg_ctr = self.channels['facebook_ads']['avg_ctr'][campaign_type]
            actual_ctr = avg_ctr * random.uniform(0.5, 1.5)
            
            impressions = int(clicks / actual_ctr) if actual_ctr > 0 else 0
            
            # Facebook-specific metrics
            reach = int(impressions * random.uniform(0.6, 0.9))  # Reach is typically lower than impressions
            frequency = impressions / reach if reach > 0 else 1
            
            conversion_rate = random.uniform(0.015, 0.06)  # 1.5-6% conversion rate
            conversions = int(clicks * conversion_rate)
            
            campaign = {
                'id': str(campaign_id),
                'name': self._generate_campaign_name('Facebook', campaign_type, i),
                'status': 'ACTIVE' if campaign_end >= self.config.end_date else 'PAUSED',
                'objective': self._map_facebook_objective(campaign_type),
                'start_time': campaign_start.strftime('%Y-%m-%d'),
                'stop_time': campaign_end.strftime('%Y-%m-%d') if campaign_end < self.config.end_date else None,
                'daily_budget': daily_budget * 100,  # Facebook uses cents
                'lifetime_budget': None,
                'bid_strategy': 'LOWEST_COST_WITHOUT_CAP',
                'targeting': {
                    'age_min': 25,
                    'age_max': 65,
                    'genders': [1, 2],  # All genders
                    'geo_locations': {
                        'countries': ['US'],
                        'location_types': ['home', 'recent']
                    },
                    'interests': self._generate_facebook_interests(),
                    'behaviors': ['Business decision makers', 'Restaurant industry']
                },
                'performance_stats': {
                    'impressions': impressions,
                    'clicks': clicks,
                    'spend': total_spend,
                    'reach': reach,
                    'frequency': round(frequency, 2),
                    'ctr': round(actual_ctr, 4),
                    'cpc': round(actual_cpc, 2),
                    'conversions': conversions,
                    'conversion_rate': round(conversion_rate, 4),
                    'cost_per_conversion': round(total_spend / conversions, 2) if conversions > 0 else 0,
                    'cpp': round(total_spend / reach, 2) if reach > 0 else 0  # Cost per person reached
                }
            }
            
            campaigns.append(campaign)
            campaign_id += 1
            
        logger.info(f"Generated {len(campaigns)} Facebook Ads campaigns")
        return campaigns
        
    def generate_facebook_ads_adsets(self, campaigns: List[Dict]) -> List[Dict]:
        """Generate Facebook ad sets for campaigns"""
        adsets = []
        adset_id = 96000000
        
        for campaign in campaigns:
            # 1-3 ad sets per campaign
            num_adsets = random.randint(1, 3)
            
            campaign_impressions = campaign['performance_stats']['impressions']
            campaign_clicks = campaign['performance_stats']['clicks']
            campaign_spend = campaign['performance_stats']['spend']
            campaign_conversions = campaign['performance_stats']['conversions']
            campaign_reach = campaign['performance_stats']['reach']
            
            for i in range(num_adsets):
                # Distribute campaign metrics across ad sets
                adset_share = random.uniform(0.2, 0.6)
                adset_impressions = int(campaign_impressions * adset_share)
                adset_clicks = int(campaign_clicks * adset_share)
                adset_spend = campaign_spend * adset_share
                adset_conversions = int(campaign_conversions * adset_share)
                adset_reach = int(campaign_reach * adset_share)
                
                adset = {
                    'id': str(adset_id),
                    'name': f"{campaign['name']} - AdSet {i+1}",
                    'campaign_id': campaign['id'],
                    'status': 'ACTIVE',
                    'optimization_goal': campaign['objective'],
                    'billing_event': 'IMPRESSIONS',
                    'bid_amount': int(campaign['performance_stats']['cpc'] * 100),  # cents
                    'daily_budget': int(campaign['daily_budget'] / num_adsets),
                    'targeting': {
                        'age_min': 25 + (i * 10),  # Vary age targeting by ad set
                        'age_max': 55 + (i * 10),
                        'genders': [1, 2],
                        'geo_locations': campaign['targeting']['geo_locations'],
                        'interests': random.sample(campaign['targeting']['interests'], 
                                                  min(3, len(campaign['targeting']['interests']))),
                        'custom_audiences': self._generate_custom_audiences()
                    },
                    'performance_stats': {
                        'impressions': adset_impressions,
                        'clicks': adset_clicks,
                        'spend': round(adset_spend, 2),
                        'reach': adset_reach,
                        'frequency': round(adset_impressions / adset_reach, 2) if adset_reach > 0 else 1,
                        'ctr': round(adset_clicks / adset_impressions, 4) if adset_impressions > 0 else 0,
                        'cpc': round(adset_spend / adset_clicks, 2) if adset_clicks > 0 else 0,
                        'conversions': adset_conversions,
                        'conversion_rate': round(adset_conversions / adset_clicks, 4) if adset_clicks > 0 else 0
                    }
                }
                
                adsets.append(adset)
                adset_id += 1
                
        logger.info(f"Generated {len(adsets)} Facebook ad sets")
        return adsets
        
    def generate_linkedin_ads_campaigns(self, companies: List[Dict]) -> List[Dict]:
        """Generate LinkedIn Ads campaign performance data"""
        campaigns = []
        campaign_id = 97000000
        
        total_days = (self.config.end_date - self.config.start_date).days
        num_campaigns = random.randint(8, 15)  # LinkedIn typically fewer campaigns
        
        for i in range(num_campaigns):
            campaign_type = random.choice(self.channels['linkedin_ads']['campaign_types'])
            
            # Campaign timing
            start_offset = random.randint(0, max(1, total_days - 30))
            campaign_start = self.config.start_date + timedelta(days=start_offset)
            campaign_end = min(
                campaign_start + timedelta(days=random.randint(30, 90)),
                self.config.end_date
            )
            
            # LinkedIn typically higher budget, lower volume
            daily_budget = random.randint(100, 800)
            total_spend = self._calculate_campaign_spend(daily_budget, campaign_start, campaign_end)
            
            avg_cpc = self.channels['linkedin_ads']['avg_cpc'][campaign_type]
            actual_cpc = avg_cpc * random.uniform(0.8, 1.2)  # Less variance on LinkedIn
            
            clicks = int(total_spend / actual_cpc)
            
            avg_ctr = self.channels['linkedin_ads']['avg_ctr'][campaign_type]
            actual_ctr = avg_ctr * random.uniform(0.7, 1.3)
            
            impressions = int(clicks / actual_ctr) if actual_ctr > 0 else 0
            
            # LinkedIn has higher conversion rates due to B2B targeting
            conversion_rate = random.uniform(0.05, 0.15)  # 5-15% conversion rate
            conversions = int(clicks * conversion_rate)
            
            campaign = {
                'id': str(campaign_id),
                'name': self._generate_campaign_name('LinkedIn', campaign_type, i),
                'status': 'ACTIVE' if campaign_end >= self.config.end_date else 'PAUSED',
                'type': campaign_type,
                'objective_type': self._map_linkedin_objective(campaign_type),
                'start_at': self._safe_timestamp(campaign_start) * 1000,
                'end_at': self._safe_timestamp(campaign_end) * 1000 if campaign_end < self.config.end_date else None,
                'daily_budget': {
                    'currency_code': 'USD',
                    'amount': str(daily_budget)
                },
                'cost_type': 'CPC',
                'targeting': {
                    'included_targeting': {
                        'job_titles': ['Owner', 'Manager', 'Director', 'CEO', 'COO', 'Operations Manager'],
                        'industries': ['Restaurants', 'Food & Beverage', 'Hospitality'],
                        'company_sizes': ['11-50', '51-200', '201-500', '501-1000', '1001-5000'],
                        'seniority_levels': ['Owner', 'Senior', 'Manager', 'Director', 'VP', 'CXO']
                    }
                },
                'performance_stats': {
                    'impressions': impressions,
                    'clicks': clicks,
                    'cost_in_usd': total_spend,
                    'ctr': round(actual_ctr, 4),
                    'average_cpc': round(actual_cpc, 2),
                    'conversions': conversions,
                    'conversion_rate': round(conversion_rate, 4),
                    'cost_per_conversion': round(total_spend / conversions, 2) if conversions > 0 else 0
                }
            }
            
            campaigns.append(campaign)
            campaign_id += 1
            
        logger.info(f"Generated {len(campaigns)} LinkedIn Ads campaigns")
        return campaigns
        
    def generate_iterable_campaigns(self, companies: List[Dict]) -> List[Dict]:
        """Generate email marketing campaign data"""
        campaigns = []
        campaign_id = 98000000
        
        email_types = [
            'Welcome Series', 'Product Announcement', 'Feature Education',
            'Customer Success Story', 'Webinar Invitation', 'Trial Extension',
            'Upgrade Promotion', 'Newsletter', 'Event Invitation', 'Survey Request'
        ]
        
        total_days = (self.config.end_date - self.config.start_date).days
        
        # Generate email campaigns at regular intervals
        num_campaigns = total_days // 7  # Weekly campaigns
        
        for i in range(num_campaigns):
            campaign_type = random.choice(email_types)
            
            # Campaign timing
            send_date = self.config.start_date + timedelta(days=i * 7 + random.randint(0, 6))
            
            if send_date > self.config.end_date:
                break
                
            # Email performance metrics
            # Calculate list size based on company count and growth over time
            days_elapsed = (send_date - self.config.start_date).days
            growth_factor = 1 + (days_elapsed / total_days) * 0.5  # 50% growth over period
            list_size = int(len(companies) * 2.5 * growth_factor)  # 2.5 contacts per company on average
            
            # Email deliverability and engagement
            delivered_rate = random.uniform(0.95, 0.99)
            delivered = int(list_size * delivered_rate)
            
            open_rate = self._get_email_open_rate(campaign_type)
            opens = int(delivered * open_rate)
            
            click_rate = self._get_email_click_rate(campaign_type, open_rate)
            clicks = int(opens * click_rate)
            
            # Email-specific metrics
            bounces = list_size - delivered
            unsubscribes = max(0, int(delivered * random.uniform(0.001, 0.005)))  # 0.1-0.5% unsubscribe rate
            
            campaign = {
                'id': str(campaign_id),
                'name': f"{campaign_type} - {send_date.strftime('%B %Y')}",
                'campaign_type': campaign_type,
                'send_date': send_date.strftime('%Y-%m-%d'),
                'status': 'SENT',
                'list_size': list_size,
                'performance_stats': {
                    'delivered': delivered,
                    'bounces': bounces,
                    'opens': opens,
                    'clicks': clicks,
                    'unsubscribes': unsubscribes,
                    'spam_complaints': max(0, int(delivered * random.uniform(0.0001, 0.001))),
                    'delivery_rate': round(delivered_rate, 4),
                    'open_rate': round(opens / delivered, 4) if delivered > 0 else 0,
                    'click_rate': round(clicks / delivered, 4) if delivered > 0 else 0,
                    'click_to_open_rate': round(clicks / opens, 4) if opens > 0 else 0,
                    'unsubscribe_rate': round(unsubscribes / delivered, 4) if delivered > 0 else 0
                },
                'segment_info': {
                    'target_audience': self._determine_email_audience(campaign_type),
                    'personalization_level': random.choice(['Basic', 'Moderate', 'Advanced'])
                }
            }
            
            campaigns.append(campaign)
            campaign_id += 1
            
        logger.info(f"Generated {len(campaigns)} Iterable email campaigns")
        return campaigns
        
    def generate_google_analytics_sessions(self, companies: List[Dict]) -> List[Dict]:
        """Generate website traffic and session data"""
        sessions = []
        
        # Generate daily session data
        current_date = self.config.start_date
        
        while current_date <= self.config.end_date:
            # Calculate base sessions for the day
            day_of_week = current_date.weekday()  # 0 = Monday, 6 = Sunday
            
            # Business days typically have higher traffic
            if day_of_week < 5:  # Monday-Friday
                base_sessions = random.randint(800, 1200)
            else:  # Weekend
                base_sessions = random.randint(400, 700)
                
            # Add seasonal variation
            month = current_date.month
            seasonal_multiplier = self._get_seasonal_multiplier(month)
            daily_sessions = int(base_sessions * seasonal_multiplier)
            
            # Add random variance
            daily_sessions = int(daily_sessions * random.uniform(0.7, 1.3))
            
            session_data = {
                'date': current_date.strftime('%Y-%m-%d'),
                'sessions': daily_sessions,
                'users': int(daily_sessions * random.uniform(0.7, 0.9)),  # Some users have multiple sessions
                'new_users': int(daily_sessions * random.uniform(0.6, 0.8)),
                'pageviews': int(daily_sessions * random.uniform(3.5, 6.5)),
                'avg_session_duration': random.randint(120, 300),  # 2-5 minutes
                'bounce_rate': random.uniform(0.35, 0.65),
                'goal_completions': int(daily_sessions * random.uniform(0.02, 0.08)),  # 2-8% conversion
                'revenue': daily_sessions * random.uniform(0.5, 2.0),  # Revenue per session
                'traffic_sources': {
                    'organic': random.uniform(0.35, 0.50),
                    'direct': random.uniform(0.20, 0.30),
                    'paid_search': random.uniform(0.15, 0.25),
                    'social': random.uniform(0.05, 0.15),
                    'email': random.uniform(0.03, 0.08),
                    'referral': random.uniform(0.02, 0.05)
                },
                'device_category': {
                    'desktop': random.uniform(0.45, 0.65),
                    'mobile': random.uniform(0.30, 0.45),
                    'tablet': random.uniform(0.05, 0.15)
                }
            }
            
            sessions.append(session_data)
            current_date += timedelta(days=1)
            
        logger.info(f"Generated {len(sessions)} Google Analytics daily sessions")
        return sessions
        
    def generate_marketing_qualified_leads(self, companies: List[Dict], campaigns_data: Dict) -> List[Dict]:
        """Generate marketing qualified leads with attribution"""
        mqls = []
        mql_id = 99000000
        
        # Combine all campaigns for attribution
        all_campaigns = []
        if 'google_ads' in campaigns_data:
            all_campaigns.extend([(c, 'google_ads') for c in campaigns_data['google_ads']])
        if 'facebook_ads' in campaigns_data:
            all_campaigns.extend([(c, 'facebook_ads') for c in campaigns_data['facebook_ads']])
        if 'linkedin_ads' in campaigns_data:
            all_campaigns.extend([(c, 'linkedin_ads') for c in campaigns_data['linkedin_ads']])
        if 'iterable' in campaigns_data:
            all_campaigns.extend([(c, 'iterable') for c in campaigns_data['iterable']])
            
        # Generate MQLs based on total conversion volume
        total_conversions = sum([
            sum([c['performance_stats'].get('conversions', 0) for c in campaigns_data.get('google_ads', [])]),
            sum([c['performance_stats'].get('conversions', 0) for c in campaigns_data.get('facebook_ads', [])]),
            sum([c['performance_stats'].get('conversions', 0) for c in campaigns_data.get('linkedin_ads', [])]),
            # Email campaigns contribute fewer MQLs but some nurturing leads
            int(sum([c['performance_stats'].get('clicks', 0) for c in campaigns_data.get('iterable', [])]) * 0.1)
        ])
        
        for i in range(total_conversions):
            # Select random campaign for attribution
            if all_campaigns:
                campaign, channel = random.choice(all_campaigns)
                
                # Determine MQL date based on campaign timing
                if channel == 'iterable':
                    mql_date = datetime.strptime(campaign['send_date'], '%Y-%m-%d').date()
                else:
                    # Handle different date field names
                    if 'start_date' in campaign:
                        campaign_start = datetime.strptime(campaign['start_date'], '%Y-%m-%d').date()
                    elif 'start_at' in campaign:
                        campaign_start = datetime.fromtimestamp(campaign['start_at'] / 1000).date()
                    else:
                        campaign_start = self.config.start_date
                        
                    campaign_end_str = campaign.get('end_date') or campaign.get('stop_time') or campaign.get('end_at')
                    if campaign_end_str:
                        if channel == 'linkedin_ads' and isinstance(campaign_end_str, int):
                            campaign_end = datetime.fromtimestamp(campaign_end_str / 1000).date()
                        elif isinstance(campaign_end_str, str):
                            campaign_end = datetime.strptime(campaign_end_str, '%Y-%m-%d').date()
                        else:
                            campaign_end = self.config.end_date
                    else:
                        campaign_end = self.config.end_date
                        
                    days_diff = (campaign_end - campaign_start).days
                    random_offset = random.randint(0, max(1, days_diff))
                    mql_date = campaign_start + timedelta(days=random_offset)
                    
                # Generate lead scoring
                lead_score = self._calculate_lead_score(channel, campaign.get('name', ''))
                
                mql = {
                    'id': str(mql_id),
                    'created_date': mql_date.strftime('%Y-%m-%d'),
                    'email': fake.email(),
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'company': fake.company().replace('Group', '').replace('Inc', '').replace('LLC', '').strip(),
                    'job_title': random.choice(['Owner', 'General Manager', 'Operations Manager', 'Director']),
                    'lead_score': lead_score,
                    'lead_source': channel,
                    'campaign_attribution': {
                        'primary_campaign_id': campaign['id'],
                        'primary_campaign_name': campaign['name'],
                        'primary_channel': channel,
                        'attribution_model': 'last_touch'
                    },
                    'qualification_criteria': {
                        'has_multiple_locations': random.choice([True, False]),
                        'budget_qualified': random.choice([True, False]),
                        'timeline_qualified': random.choice([True, False]),
                        'authority_qualified': random.choice([True, False])
                    },
                    'engagement_score': random.randint(1, 100),
                    'conversion_probability': random.uniform(0.1, 0.8)
                }
                
                mqls.append(mql)
                mql_id += 1
                
        logger.info(f"Generated {len(mqls)} marketing qualified leads")
        return mqls
        
    def generate_attribution_touchpoints(self, companies: List[Dict], mqls: List[Dict], campaigns_data: Dict) -> List[Dict]:
        """Generate multi-touch attribution data"""
        touchpoints = []
        touchpoint_id = 100000000
        
        # Generate touchpoint sequences for each MQL
        for mql in mqls:
            conversion_date = datetime.strptime(mql['created_date'], '%Y-%m-%d').date()
            
            # Generate 1-5 touchpoints leading up to conversion
            num_touchpoints = random.randint(1, 5)
            
            for i in range(num_touchpoints):
                # Touchpoints occur before conversion
                days_before = random.randint(0, min(30, (conversion_date - self.config.start_date).days))
                touchpoint_date = conversion_date - timedelta(days=days_before)
                
                # Select random channel and campaign
                channel = random.choice(['google_ads', 'facebook_ads', 'linkedin_ads', 'iterable', 'organic', 'direct'])
                
                if channel in campaigns_data and campaigns_data[channel]:
                    campaign = random.choice(campaigns_data[channel])
                    campaign_id = campaign['id']
                    campaign_name = campaign['name']
                else:
                    campaign_id = None
                    campaign_name = f"Organic {channel.replace('_', ' ').title()}"
                    
                touchpoint = {
                    'id': str(touchpoint_id),
                    'mql_id': mql['id'],
                    'touchpoint_date': touchpoint_date.strftime('%Y-%m-%d'),
                    'channel': channel,
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'touchpoint_type': random.choice(['impression', 'click', 'visit', 'engagement']),
                    'position_in_journey': i + 1,
                    'attribution_weight': self._calculate_attribution_weight(i, num_touchpoints),
                    'interaction_details': {
                        'page_visited': random.choice(['/demo', '/pricing', '/features', '/case-studies', '/contact']),
                        'time_spent': random.randint(30, 300),  # seconds
                        'pages_viewed': random.randint(1, 8)
                    }
                }
                
                touchpoints.append(touchpoint)
                touchpoint_id += 1
                
        logger.info(f"Generated {len(touchpoints)} attribution touchpoints")
        return touchpoints

    # Helper methods for marketing data generation
    def _generate_campaign_name(self, platform: str, campaign_type: str, index: int) -> str:
        """Generate realistic campaign names"""
        modifiers = ['Restaurant', 'Bar', 'Hospitality', 'Multi-Location', 'Business']
        actions = ['Management', 'Solutions', 'Platform', 'Software', 'System']
        
        modifier = random.choice(modifiers)
        action = random.choice(actions)
        
        if platform == 'Google Ads':
            return f"{modifier} {action} - {campaign_type} {index + 1}"
        elif platform == 'Facebook':
            return f"Bar Management Platform - {campaign_type} - Q{random.randint(1, 4)}"
        elif platform == 'LinkedIn':
            return f"B2B {modifier} {action} - {campaign_type}"
        else:
            return f"{modifier} {action} Campaign {index + 1}"
            
    def _calculate_campaign_spend(self, daily_budget: int, start_date: date, end_date: date) -> float:
        """Calculate realistic campaign spend with daily variance"""
        days = (end_date - start_date).days
        if days <= 0:
            return 0
            
        total_spend = 0
        current_date = start_date
        
        while current_date < end_date:
            # Add daily variance (campaigns don't always spend full budget)
            daily_spend = daily_budget * random.uniform(0.70, 1.0)
            
            # Weekend spending typically lower
            if current_date.weekday() >= 5:  # Saturday/Sunday
                daily_spend *= random.uniform(0.5, 0.8)
                
            total_spend += daily_spend
            current_date += timedelta(days=1)
            
        return round(total_spend, 2)
        
    def _map_google_channel_type(self, campaign_type: str) -> str:
        """Map campaign type to Google Ads channel type"""
        mapping = {
            'Search': 'SEARCH',
            'Display': 'DISPLAY', 
            'Video': 'VIDEO',
            'Shopping': 'SHOPPING'
        }
        return mapping.get(campaign_type, 'SEARCH')
        
    def _map_facebook_objective(self, campaign_type: str) -> str:
        """Map campaign type to Facebook objective"""
        mapping = {
            'Traffic': 'LINK_CLICKS',
            'Conversions': 'CONVERSIONS',
            'Brand Awareness': 'BRAND_AWARENESS',
            'Lead Generation': 'LEAD_GENERATION'
        }
        return mapping.get(campaign_type, 'CONVERSIONS')
        
    def _map_linkedin_objective(self, campaign_type: str) -> str:
        """Map campaign type to LinkedIn objective"""
        mapping = {
            'Single Image Ad': 'WEBSITE_CONVERSIONS',
            'Carousel Ad': 'WEBSITE_CONVERSIONS',
            'Video Ad': 'VIDEO_VIEWS',
            'Lead Gen Form': 'LEAD_GENERATION'
        }
        return mapping.get(campaign_type, 'WEBSITE_CONVERSIONS')
        
    def _generate_keywords_for_ad_group(self, campaign_type: str, ad_group_index: int) -> List[str]:
        """Generate relevant keywords for ad groups"""
        base_keywords = [
            'bar management software', 'restaurant management system', 
            'pos system', 'inventory management', 'bar pos',
            'restaurant software', 'hospitality management'
        ]
        
        specific_keywords = {
            'Search': [
                'bar management platform', 'restaurant operations software',
                'multi location management', 'bar inventory system'
            ],
            'Display': [
                'bar management solution', 'restaurant technology',
                'hospitality software', 'bar operations platform'
            ],
            'Video': [
                'bar management demo', 'restaurant software video',
                'hospitality technology showcase'
            ],
            'Shopping': [
                'bar management system', 'restaurant pos system',
                'hospitality management platform'
            ]
        }
        
        keywords = base_keywords + specific_keywords.get(campaign_type, [])
        return random.sample(keywords, min(5, len(keywords)))
        
    def _generate_facebook_interests(self) -> List[str]:
        """Generate Facebook interest targeting"""
        interests = [
            'Restaurant management', 'Bar ownership', 'Hospitality industry',
            'Small business', 'Franchise business', 'Food service',
            'Business management', 'Retail management', 'Point of sale systems'
        ]
        return random.sample(interests, random.randint(3, 6))
        
    def _generate_custom_audiences(self) -> List[str]:
        """Generate Facebook custom audience names"""
        audiences = [
            'Website Visitors - Last 30 Days',
            'Email Subscribers',
            'Existing Customers', 
            'Demo Requesters',
            'Lookalike - Top Customers',
            'Engaged Video Viewers'
        ]
        return random.sample(audiences, random.randint(1, 3))
        
    def _get_email_open_rate(self, campaign_type: str) -> float:
        """Get realistic open rates by email type"""
        open_rates = {
            'Welcome Series': random.uniform(0.45, 0.65),
            'Product Announcement': random.uniform(0.25, 0.35),
            'Feature Education': random.uniform(0.30, 0.40),
            'Customer Success Story': random.uniform(0.28, 0.38),
            'Webinar Invitation': random.uniform(0.35, 0.45),
            'Trial Extension': random.uniform(0.40, 0.55),
            'Upgrade Promotion': random.uniform(0.30, 0.45),
            'Newsletter': random.uniform(0.20, 0.30),
            'Event Invitation': random.uniform(0.35, 0.50),
            'Survey Request': random.uniform(0.25, 0.35)
        }
        return open_rates.get(campaign_type, random.uniform(0.25, 0.35))
        
    def _get_email_click_rate(self, campaign_type: str, open_rate: float) -> float:
        """Get realistic click-to-open rates by email type"""
        cto_rates = {
            'Welcome Series': random.uniform(0.15, 0.25),
            'Product Announcement': random.uniform(0.08, 0.15),
            'Feature Education': random.uniform(0.12, 0.20),
            'Customer Success Story': random.uniform(0.10, 0.18),
            'Webinar Invitation': random.uniform(0.20, 0.35),
            'Trial Extension': random.uniform(0.25, 0.40),
            'Upgrade Promotion': random.uniform(0.18, 0.30),
            'Newsletter': random.uniform(0.06, 0.12),
            'Event Invitation': random.uniform(0.20, 0.30),
            'Survey Request': random.uniform(0.15, 0.25)
        }
        return cto_rates.get(campaign_type, random.uniform(0.10, 0.20))
        
    def _determine_email_audience(self, campaign_type: str) -> str:
        """Determine target audience for email campaigns"""
        audiences = {
            'Welcome Series': 'New Subscribers',
            'Product Announcement': 'All Customers',
            'Feature Education': 'Active Users',
            'Customer Success Story': 'Prospects',
            'Webinar Invitation': 'Prospects + Customers',
            'Trial Extension': 'Trial Users',
            'Upgrade Promotion': 'Starter Plan Users',
            'Newsletter': 'All Subscribers',
            'Event Invitation': 'VIP Customers',
            'Survey Request': 'Recent Customers'
        }
        return audiences.get(campaign_type, 'All Subscribers')
        
    def _get_seasonal_multiplier(self, month: int) -> float:
        """Get seasonal traffic multiplier by month"""
        # Restaurant industry patterns
        seasonal_patterns = {
            1: 0.85,   # January - slow after holidays
            2: 0.90,   # February - still slow
            3: 1.05,   # March - spring pickup
            4: 1.10,   # April - strong spring
            5: 1.15,   # May - peak spring/early summer
            6: 1.20,   # June - summer peak
            7: 1.15,   # July - strong summer
            8: 1.10,   # August - late summer
            9: 1.05,   # September - back to school
            10: 1.10,  # October - fall events
            11: 1.25,  # November - holiday prep
            12: 1.30   # December - holiday peak
        }
        return seasonal_patterns.get(month, 1.0)
        
    def _calculate_lead_score(self, channel: str, campaign_name: str) -> int:
        """Calculate lead score based on channel and campaign quality"""
        base_scores = {
            'google_ads': 70,
            'facebook_ads': 60,
            'linkedin_ads': 85,  # Higher quality B2B leads
            'iterable': 65,
            'organic': 80,
            'direct': 90
        }
        
        base_score = base_scores.get(channel, 60)
        
        # Add variance based on campaign quality indicators
        if 'demo' in campaign_name.lower():
            base_score += 10
        if 'enterprise' in campaign_name.lower():
            base_score += 15
        if 'trial' in campaign_name.lower():
            base_score += 5
            
        # Add random variance
        final_score = base_score + random.randint(-15, 15)
        return max(1, min(100, final_score))
        
    def _calculate_attribution_weight(self, position: int, total_touchpoints: int) -> float:
        """Calculate attribution weight based on position in customer journey"""
        if total_touchpoints == 1:
            return 1.0
            
        # Time-decay attribution model
        if position == 0:  # First touch
            return 0.40
        elif position == total_touchpoints - 1:  # Last touch
            return 0.40
        else:  # Middle touches
            remaining_weight = 0.20
            middle_touches = total_touchpoints - 2
            return remaining_weight / middle_touches if middle_touches > 0 else 0.0
    # Helper methods for marketing data generation
    def _generate_campaign_name(self, platform: str, campaign_type: str, index: int) -> str:
        """Generate realistic campaign names"""
        modifiers = ['Restaurant', 'Bar', 'Hospitality', 'Multi-Location', 'Business']
        actions = ['Management', 'Solutions', 'Platform', 'Software', 'System']
        
        modifier = random.choice(modifiers)
        action = random.choice(actions)
        
        if platform == 'Google Ads':
            return f"{modifier} {action} - {campaign_type} {index + 1}"
        elif platform == 'Facebook':
            return f"Bar Management Platform - {campaign_type} - Q{random.randint(1, 4)}"
        elif platform == 'LinkedIn':
            return f"B2B {modifier} {action} - {campaign_type}"
        else:
            return f"{modifier} {action} Campaign {index + 1}"
            
    def _calculate_campaign_spend(self, daily_budget: int, start_date: date, end_date: date) -> float:
        """Calculate realistic campaign spend with daily variance"""
        days = (end_date - start_date).days
        if days <= 0:
            return 0
            
        total_spend = 0
        current_date = start_date
        
        while current_date < end_date:
            # Add daily variance (campaigns don't always spend full budget)
            daily_spend = daily_budget * random.uniform(0.70, 1.0)
            
            # Weekend spending typically lower
            if current_date.weekday() >= 5:  # Saturday/Sunday
                daily_spend *= random.uniform(0.5, 0.8)
                
            total_spend += daily_spend
            current_date += timedelta(days=1)
            
        return round(total_spend, 2)
        
    def _map_google_channel_type(self, campaign_type: str) -> str:
        """Map campaign type to Google Ads channel type"""
        mapping = {
            'Search': 'SEARCH',
            'Display': 'DISPLAY', 
            'Video': 'VIDEO',
            'Shopping': 'SHOPPING'
        }
        return mapping.get(campaign_type, 'SEARCH')
        
    def _map_facebook_objective(self, campaign_type: str) -> str:
        """Map campaign type to Facebook objective"""
        mapping = {
            'Traffic': 'LINK_CLICKS',
            'Conversions': 'CONVERSIONS',
            'Brand Awareness': 'BRAND_AWARENESS',
            'Lead Generation': 'LEAD_GENERATION'
        }
        return mapping.get(campaign_type, 'CONVERSIONS')
        
    def _map_linkedin_objective(self, campaign_type: str) -> str:
        """Map campaign type to LinkedIn objective"""
        mapping = {
            'Single Image Ad': 'WEBSITE_CONVERSIONS',
            'Carousel Ad': 'WEBSITE_CONVERSIONS',
            'Video Ad': 'VIDEO_VIEWS',
            'Lead Gen Form': 'LEAD_GENERATION'
        }
        return mapping.get(campaign_type, 'WEBSITE_CONVERSIONS')
        
    def _generate_keywords_for_ad_group(self, campaign_type: str, ad_group_index: int) -> List[str]:
        """Generate relevant keywords for ad groups"""
        base_keywords = [
            'bar management software', 'restaurant management system', 
            'pos system', 'inventory management', 'bar pos',
            'restaurant software', 'hospitality management'
        ]
        
        specific_keywords = {
            'Search': [
                'bar management platform', 'restaurant operations software',
                'multi location management', 'bar inventory system'
            ],
            'Display': [
                'bar management solution', 'restaurant technology',
                'hospitality software', 'bar operations platform'
            ],
            'Video': [
                'bar management demo', 'restaurant software video',
                'hospitality technology showcase'
            ],
            'Shopping': [
                'bar management system', 'restaurant pos system',
                'hospitality management platform'
            ]
        }
        
        keywords = base_keywords + specific_keywords.get(campaign_type, [])
        return random.sample(keywords, min(5, len(keywords)))
        
    def _generate_facebook_interests(self) -> List[str]:
        """Generate Facebook interest targeting"""
        interests = [
            'Restaurant management', 'Bar ownership', 'Hospitality industry',
            'Small business', 'Franchise business', 'Food service',
            'Business management', 'Retail management', 'Point of sale systems'
        ]
        return random.sample(interests, random.randint(3, 6))
        
    def _generate_custom_audiences(self) -> List[str]:
        """Generate Facebook custom audience names"""
        audiences = [
            'Website Visitors - Last 30 Days',
            'Email Subscribers',
            'Existing Customers', 
            'Demo Requesters',
            'Lookalike - Top Customers',
            'Engaged Video Viewers'
        ]
        return random.sample(audiences, random.randint(1, 3))
        
    def _get_email_open_rate(self, campaign_type: str) -> float:
        """Get realistic open rates by email type"""
        open_rates = {
            'Welcome Series': random.uniform(0.45, 0.65),
            'Product Announcement': random.uniform(0.25, 0.35),
            'Feature Education': random.uniform(0.30, 0.40),
            'Customer Success Story': random.uniform(0.28, 0.38),
            'Webinar Invitation': random.uniform(0.35, 0.45),
            'Trial Extension': random.uniform(0.40, 0.55),
            'Upgrade Promotion': random.uniform(0.30, 0.45),
            'Newsletter': random.uniform(0.20, 0.30),
            'Event Invitation': random.uniform(0.35, 0.50),
            'Survey Request': random.uniform(0.25, 0.35)
        }
        return open_rates.get(campaign_type, random.uniform(0.25, 0.35))
        
    def _get_email_click_rate(self, campaign_type: str, open_rate: float) -> float:
        """Get realistic click-to-open rates by email type"""
        cto_rates = {
            'Welcome Series': random.uniform(0.15, 0.25),
            'Product Announcement': random.uniform(0.08, 0.15),
            'Feature Education': random.uniform(0.12, 0.20),
            'Customer Success Story': random.uniform(0.10, 0.18),
            'Webinar Invitation': random.uniform(0.20, 0.35),
            'Trial Extension': random.uniform(0.25, 0.40),
            'Upgrade Promotion': random.uniform(0.18, 0.30),
            'Newsletter': random.uniform(0.06, 0.12),
            'Event Invitation': random.uniform(0.20, 0.30),
            'Survey Request': random.uniform(0.15, 0.25)
        }
        return cto_rates.get(campaign_type, random.uniform(0.10, 0.20))
        
    def _determine_email_audience(self, campaign_type: str) -> str:
        """Determine target audience for email campaigns"""
        audiences = {
            'Welcome Series': 'New Subscribers',
            'Product Announcement': 'All Customers',
            'Feature Education': 'Active Users',
            'Customer Success Story': 'Prospects',
            'Webinar Invitation': 'Prospects + Customers',
            'Trial Extension': 'Trial Users',
            'Upgrade Promotion': 'Starter Plan Users',
            'Newsletter': 'All Subscribers',
            'Event Invitation': 'VIP Customers',
            'Survey Request': 'Recent Customers'
        }
        return audiences.get(campaign_type, 'All Subscribers')
        
    def _get_seasonal_multiplier(self, month: int) -> float:
        """Get seasonal traffic multiplier by month"""
        # Restaurant industry patterns
        seasonal_patterns = {
            1: 0.85,   # January - slow after holidays
            2: 0.90,   # February - still slow
            3: 1.05,   # March - spring pickup
            4: 1.10,   # April - strong spring
            5: 1.15,   # May - peak spring/early summer
            6: 1.20,   # June - summer peak
            7: 1.15,   # July - strong summer
            8: 1.10,   # August - late summer
            9: 1.05,   # September - back to school
            10: 1.10,  # October - fall events
            11: 1.25,  # November - holiday prep
            12: 1.30   # December - holiday peak
        }
        return seasonal_patterns.get(month, 1.0)
        
    def _calculate_lead_score(self, channel: str, campaign_name: str) -> int:
        """Calculate lead score based on channel and campaign quality"""
        base_scores = {
            'google_ads': 70,
            'facebook_ads': 60,
            'linkedin_ads': 85,  # Higher quality B2B leads
            'iterable': 65,
            'organic': 80,
            'direct': 90
        }
        
        base_score = base_scores.get(channel, 60)
        
        # Add variance based on campaign quality indicators
        if 'demo' in campaign_name.lower():
            base_score += 10
        if 'enterprise' in campaign_name.lower():
            base_score += 15
        if 'trial' in campaign_name.lower():
            base_score += 5
            
        # Add random variance
        final_score = base_score + random.randint(-15, 15)
        return max(1, min(100, final_score))
        
    def _calculate_attribution_weight(self, position: int, total_touchpoints: int) -> float:
        """Calculate attribution weight based on position in customer journey"""
        if total_touchpoints == 1:
            return 1.0
            
        # Time-decay attribution model
        if position == 0:  # First touch
            return 0.40
        elif position == total_touchpoints - 1:  # Last touch
            return 0.40
        else:  # Middle touches
            remaining_weight = 0.20
            middle_touches = total_touchpoints - 2
            return remaining_weight / middle_touches if middle_touches > 0 else 0.0