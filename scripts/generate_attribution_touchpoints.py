#!/usr/bin/env python3
"""
Generate synthetic attribution touchpoints data for the bar management SaaS platform.

This script creates:
- 15,000 touchpoints for multi-touch journeys
- Channel distribution
- Attribution weight calculations
- Conversion paths
"""

import json
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from faker import Faker
from scripts.database_config import db_helper
from scripts.environment_config import get_environment_config

fake = Faker()

def load_campaigns_mapping():
    """Load existing campaigns mapping."""
    with open('data/marketing_campaigns_mapping.json', 'r') as f:
        return json.load(f)

def load_hubspot_deals():
    """Load HubSpot deals to get conversion data."""
    with open('data/hubspot_deals_mapping.json', 'r') as f:
        return json.load(f)

def generate_attribution_touchpoints(env_config):
    """Generate attribution touchpoints data."""
    touchpoints = []
    campaigns = load_campaigns_mapping()
    deals = load_hubspot_deals()
    
    # Filter for won deals (these represent conversions)
    won_deals = [d for d in deals if d['stage'] == 'closedwon']
    
    # Channel mix for B2B SaaS
    channel_weights = {
        'organic': 0.25,
        'paid_search': 0.30,
        'paid_social': 0.15,
        'email': 0.10,
        'direct': 0.10,
        'referral': 0.05,
        'display': 0.05
    }
    
    # Attribution models
    attribution_models = {
        'first_touch': lambda positions: {0: 1.0},
        'last_touch': lambda positions: {positions[-1]: 1.0},
        'linear': lambda positions: {p: 1.0/len(positions) for p in range(len(positions))},
        'time_decay': lambda positions: {
            p: 0.5 ** ((len(positions) - 1 - p) * 0.5) for p in range(len(positions))
        },
        'u_shaped': lambda positions: {
            p: 0.4 if p == 0 or p == len(positions)-1 else 0.2/(len(positions)-2) 
            for p in range(len(positions))
        } if len(positions) > 1 else {0: 1.0}
    }
    
    # Medium/source combinations
    medium_source_map = {
        'organic': [
            ('organic', 'google'),
            ('organic', 'bing'),
            ('organic', 'duckduckgo')
        ],
        'paid_search': [
            ('cpc', 'google'),
            ('cpc', 'bing'),
            ('ppc', 'google')
        ],
        'paid_social': [
            ('cpc', 'facebook'),
            ('cpc', 'linkedin'),
            ('cpc', 'twitter')
        ],
        'email': [
            ('email', 'newsletter'),
            ('email', 'nurture'),
            ('email', 'product')
        ],
        'direct': [
            ('none', 'direct'),
            (None, None)
        ],
        'referral': [
            ('referral', 'partner'),
            ('referral', 'blog'),
            ('referral', 'review-site')
        ],
        'display': [
            ('display', 'google'),
            ('banner', 'programmatic')
        ]
    }
    
    # Content types
    content_types = [
        'homepage', 'product-page', 'pricing', 'demo-request',
        'case-study', 'blog-post', 'webinar', 'ebook',
        'free-trial', 'contact-sales'
    ]
    
    # Touchpoint types
    touchpoint_types = [
        'page_view', 'form_submission', 'demo_request', 'content_download',
        'email_click', 'ad_click', 'webinar_attendance', 'trial_signup',
        'sales_call', 'event_attendance'
    ]
    
    # Generate touchpoints for each won deal (these led to conversions)
    for deal in won_deals:
        # Determine number of touchpoints in journey (B2B has longer journeys)
        num_touchpoints = random.choices(
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            weights=[5, 10, 15, 20, 20, 15, 8, 4, 2, 1]
        )[0]
        
        # Parse deal close date
        close_date = datetime.fromisoformat(deal['closedate'])
        
        # Generate touchpoints working backwards from conversion
        journey_touchpoints = []
        
        for i in range(num_touchpoints):
            touchpoint_id = str(uuid.uuid4())
            
            # Calculate touchpoint date (spread over 30-90 days)
            days_before_conversion = random.randint(i * 3, (i + 1) * 10)
            touchpoint_date = close_date - timedelta(days=days_before_conversion)
            
            # Select channel based on position in journey
            if i == 0:  # Last touch often direct or branded search
                channel = random.choices(
                    ['direct', 'organic', 'paid_search'],
                    weights=[0.3, 0.4, 0.3]
                )[0]
            elif i == num_touchpoints - 1:  # First touch often discovery
                channel = random.choices(
                    ['organic', 'paid_social', 'referral', 'display'],
                    weights=[0.4, 0.3, 0.2, 0.1]
                )[0]
            else:  # Middle touches
                channel = random.choices(
                    list(channel_weights.keys()),
                    weights=list(channel_weights.values())
                )[0]
            
            # Get medium/source
            medium, source = random.choice(medium_source_map[channel])
            
            # Get campaign if paid channel
            campaign_id = None
            campaign_name = None
            if channel in ['paid_search', 'paid_social', 'display']:
                # Find a campaign from the appropriate platform
                if source == 'google' and channel == 'paid_search':
                    platform_campaigns = campaigns.get('google_ads', [])
                elif source == 'facebook':
                    platform_campaigns = campaigns.get('facebook_ads', [])
                elif source == 'linkedin':
                    platform_campaigns = campaigns.get('linkedin_ads', [])
                else:
                    platform_campaigns = []
                
                if platform_campaigns:
                    campaign = random.choice(platform_campaigns)
                    campaign_id = campaign['id']
                    campaign_name = campaign['name']
            
            # Select content
            content = random.choice(content_types)
            
            # Select touchpoint type based on content and channel
            if content in ['demo-request', 'contact-sales']:
                touchpoint_type = 'form_submission'
            elif content == 'free-trial':
                touchpoint_type = 'trial_signup'
            elif content in ['webinar']:
                touchpoint_type = 'webinar_attendance'
            elif content in ['ebook', 'case-study']:
                touchpoint_type = 'content_download'
            elif channel == 'email':
                touchpoint_type = 'email_click'
            elif channel in ['paid_search', 'paid_social', 'display']:
                touchpoint_type = 'ad_click'
            else:
                touchpoint_type = 'page_view'
            
            journey_touchpoints.append({
                'id': touchpoint_id,
                'mql_id': None,  # Will be set when we generate MQLs
                'touchpoint_date': touchpoint_date,
                'channel': channel,
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'medium': medium,
                'source': source,
                'content': content,
                'touchpoint_position': num_touchpoints - i,  # Reverse order
                'deal_id': deal['id'],
                'created_at': touchpoint_date
            })
        
        # Apply attribution model (using linear for now)
        model = attribution_models['linear']
        weights = model(list(range(len(journey_touchpoints))))
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Apply weights to touchpoints
        for idx, tp in enumerate(journey_touchpoints):
            tp['attribution_weight'] = float(normalized_weights.get(idx, 0))
            tp['touchpoint_position'] = idx + 1
            touchpoints.append(tp)
    
    # Generate additional touchpoints for non-converting journeys
    # (to make it realistic, not all touchpoints lead to conversions)
    num_converting_touchpoints = len(touchpoints)
    num_non_converting = 15000 - num_converting_touchpoints
    
    for i in range(num_non_converting):
        touchpoint_id = str(uuid.uuid4())
        
        # Random date in the last 180 days
        touchpoint_date = datetime.now() - timedelta(days=random.randint(1, 180))
        
        # Random channel
        channel = random.choices(
            list(channel_weights.keys()),
            weights=list(channel_weights.values())
        )[0]
        
        # Get medium/source
        medium, source = random.choice(medium_source_map[channel])
        
        # Campaign assignment for paid channels
        campaign_id = None
        campaign_name = None
        if channel in ['paid_search', 'paid_social', 'display'] and random.random() > 0.3:
            all_campaigns = []
            for platform_campaigns in campaigns.values():
                all_campaigns.extend(platform_campaigns)
            if all_campaigns:
                campaign = random.choice(all_campaigns)
                campaign_id = campaign['id']
                campaign_name = campaign['name']
        
        content = random.choice(content_types)
        
        touchpoint = {
            'id': touchpoint_id,
            'mql_id': None,
            'touchpoint_date': touchpoint_date.isoformat(),
            'channel': channel,
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'medium': medium,
            'source': source,
            'content': content,
            'attribution_weight': 0.0,  # No attribution for non-converting
            'touchpoint_position': 1,  # Single touchpoint
            'created_at': touchpoint_date.isoformat()
        }
        
        touchpoints.append(touchpoint)
    
    return touchpoints[:15000]  # Ensure exactly 15,000

def save_attribution_mapping(touchpoints):
    """Save attribution touchpoints mapping for future reference."""
    # Summary statistics
    converting_touchpoints = [t for t in touchpoints if t.get('deal_id')]
    non_converting = [t for t in touchpoints if not t.get('deal_id')]
    
    summary = {
        'total_touchpoints': len(touchpoints),
        'converting_touchpoints': len(converting_touchpoints),
        'non_converting_touchpoints': len(non_converting),
        'unique_deals': len(set(t.get('deal_id') for t in converting_touchpoints if t.get('deal_id'))),
        'channel_distribution': {},
        'attribution_total': sum(t['attribution_weight'] for t in touchpoints)
    }
    
    # Channel distribution
    for tp in touchpoints:
        channel = tp['channel']
        summary['channel_distribution'][channel] = summary['channel_distribution'].get(channel, 0) + 1
    
    with open('data/attribution_touchpoints_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✓ Saved attribution touchpoints summary to data/attribution_touchpoints_summary.json")

def main():
    print("=== Generating Attribution Touchpoints ===")
    
    # Get environment configuration
    env_config = get_environment_config()
    print(f"Environment: {env_config.name}")
    
    # Test database connection
    if not db_helper.test_connection():
        print("✗ Failed to connect to database")
        return
    
    # Generate touchpoints
    print("\nGenerating attribution touchpoints...")
    touchpoints = generate_attribution_touchpoints(env_config)
    print(f"✓ Generated {len(touchpoints)} attribution touchpoints")
    
    # Show statistics
    converting = [t for t in touchpoints if t.get('deal_id')]
    print(f"  - Converting journeys: {len(set(t.get('deal_id') for t in converting if t.get('deal_id')))}")
    print(f"  - Total converting touchpoints: {len(converting)}")
    print(f"  - Non-converting touchpoints: {len(touchpoints) - len(converting)}")
    
    # Channel distribution
    channels = {}
    for tp in touchpoints:
        channel = tp['channel']
        channels[channel] = channels.get(channel, 0) + 1
    
    print("\nChannel distribution:")
    for channel, count in sorted(channels.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(touchpoints)) * 100
        print(f"  - {channel}: {count:,} ({percentage:.1f}%)")
    
    # Verify attribution weights
    total_attribution = sum(t['attribution_weight'] for t in converting)
    unique_deals = len(set(t.get('deal_id') for t in converting if t.get('deal_id')))
    print(f"\nAttribution verification:")
    print(f"  - Total attribution weight: {total_attribution:.2f}")
    print(f"  - Expected (number of deals): {unique_deals}")
    print(f"  - Verification: {'✓ PASS' if abs(total_attribution - unique_deals) < 1 else '✗ FAIL'}")
    
    # Insert into database
    print("\nInserting into database...")
    # Remove deal_id field before inserting (not in table schema)
    touchpoints_for_db = []
    for tp in touchpoints:
        tp_copy = tp.copy()
        if 'deal_id' in tp_copy:
            del tp_copy['deal_id']
        touchpoints_for_db.append(tp_copy)
    
    db_helper.bulk_insert('attribution_touchpoints', touchpoints_for_db)
    
    # Save mapping
    save_attribution_mapping(touchpoints)
    
    # Verify
    count = db_helper.get_row_count('attribution_touchpoints')
    print(f"\n✓ Total attribution touchpoints in database: {count:,}")

if __name__ == "__main__":
    main()