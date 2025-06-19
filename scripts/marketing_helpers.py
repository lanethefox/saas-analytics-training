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