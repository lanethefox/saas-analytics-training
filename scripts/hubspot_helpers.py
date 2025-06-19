    def _calculate_deal_value(self, company: Dict) -> int:
        """Calculate realistic deal value based on company characteristics"""
        location_count = company['location_count']
        business_type = company['business_type']
        
        # Base pricing per location per year
        base_price_mapping = {
            'Restaurant': 1800,      # Higher complexity
            'Sports Bar': 1600,      
            'Brewery': 2000,         # Complex inventory
            'Wine Bar': 1400,        
            'Cocktail Lounge': 1500,
            'Sports Grill': 1700,
            'Pub': 1300,
            'Nightclub': 1900,       # Complex operations
            'Rooftop Bar': 1600,
            'Dive Bar': 1200        # Simpler operations
        }
        
        base_price = base_price_mapping.get(business_type, 1500)
        
        # Volume discounts for larger customers
        if location_count >= 10:
            discount = 0.20  # 20% discount for enterprise
        elif location_count >= 5:
            discount = 0.10  # 10% discount for mid-market
        else:
            discount = 0.0   # No discount for SMB
            
        annual_value = int(base_price * location_count * (1 - discount))
        
        # Add some randomness
        variance = random.uniform(0.8, 1.2)
        return int(annual_value * variance)
        
    def _calculate_win_probability(self, company: Dict) -> float:
        """Calculate deal win probability based on company characteristics"""
        base_probability = 0.35  # Base 35% win rate
        
        # Adjust based on company size (larger companies harder to close)
        if company['location_count'] >= 10:
            size_modifier = -0.10
        elif company['location_count'] >= 5:
            size_modifier = 0.0
        else:
            size_modifier = 0.15  # SMB easier to close
            
        # Adjust based on lead source
        source_modifiers = {
            'Referral': 0.25,
            'Website': 0.10,
            'Content Marketing': 0.15,
            'Google Ads': 0.05,
            'Facebook Ads': 0.0,
            'LinkedIn Ads': 0.05,
            'Webinar': 0.20,
            'Trade Show': 0.10,
            'Cold Outreach': -0.15,
            'Organic Search': 0.05
        }
        
        source_modifier = source_modifiers.get(company['properties']['lead_source'], 0.0)
        
        final_probability = base_probability + size_modifier + source_modifier
        return max(0.1, min(0.8, final_probability))  # Clamp between 10-80%
        
    def _get_stage_probability(self, stage: str) -> str:
        """Get probability percentage for deal stage"""
        stage_probabilities = {
            'Lead': '5',
            'Marketing Qualified Lead': '10', 
            'Sales Qualified Lead': '20',
            'Discovery': '30',
            'Demo Scheduled': '40',
            'Proposal': '60',
            'Negotiation': '80',
            'Closed Won': '100',
            'Closed Lost': '0'
        }
        return stage_probabilities.get(stage, '25')
        
    def _determine_ticket_priority(self, category: str) -> str:
        """Determine ticket priority based on category"""
        priority_mapping = {
            'Technical Issue': random.choice(['HIGH', 'MEDIUM', 'MEDIUM', 'LOW']),  # Tech issues often urgent
            'Billing Question': random.choice(['MEDIUM', 'LOW', 'LOW']),
            'Feature Request': 'LOW',
            'Training': 'LOW',
            'Integration Support': random.choice(['HIGH', 'MEDIUM', 'MEDIUM']),
            'Account Management': 'MEDIUM',
            'Bug Report': random.choice(['HIGH', 'HIGH', 'MEDIUM']),  # Bugs often high priority
            'General Inquiry': 'LOW'
        }
        return priority_mapping.get(category, 'MEDIUM')
        
    def _determine_ticket_status(self, ticket_date: datetime) -> str:
        """Determine ticket status based on age"""
        days_old = (datetime.now().date() - ticket_date.date()).days
        
        if days_old > 30:
            return 'Closed'  # Old tickets are likely closed
        elif days_old > 7:
            return random.choice(['Closed', 'Waiting on customer', 'In progress'])
        else:
            return random.choice(['New', 'In progress', 'Waiting on customer'])
            
    def _generate_ticket_subject(self, category: str) -> str:
        """Generate realistic ticket subjects"""
        subjects = {
            'Technical Issue': [
                'POS System Not Responding',
                'Inventory Scanner Connection Error', 
                'Payment Terminal Offline',
                'Kitchen Display Not Updating',
                'Network Connectivity Issues'
            ],
            'Billing Question': [
                'Question About Recent Invoice',
                'Need Copy of Previous Billing Statement',
                'Pricing Inquiry for Additional Location',
                'Payment Method Update Required'
            ],
            'Feature Request': [
                'Request for Custom Reporting Feature',
                'Integration with Existing POS System',
                'Mobile App Enhancement Request',
                'Custom Dashboard Requirements'
            ],
            'Training': [
                'New Staff Training Session Request',
                'Advanced Features Training Needed',
                'Manager Training for New Location',
                'Refresher Training on Inventory Management'
            ],
            'Integration Support': [
                'Help with QuickBooks Integration',
                'Third-party POS System Setup',
                'API Integration Questions',
                'Data Migration Assistance'
            ],
            'Account Management': [
                'Account Review Meeting Request',
                'Contract Renewal Discussion',
                'Account Expansion Planning',
                'Service Level Review'
            ],
            'Bug Report': [
                'Data Not Syncing Properly',
                'Report Generation Error',
                'Dashboard Display Issue',
                'Mobile App Crash Report'
            ],
            'General Inquiry': [
                'General Product Questions',
                'Service Availability Inquiry',
                'Reference Request',
                'Industry Best Practices Question'
            ]
        }
        
        return random.choice(subjects.get(category, ['General Support Request']))
        
    def _generate_ticket_content(self, category: str, company: Dict) -> str:
        """Generate realistic ticket content"""
        templates = {
            'Technical Issue': f"We're experiencing technical difficulties at {company['name']}. Our {random.choice(['POS system', 'inventory scanner', 'payment terminal'])} has been {random.choice(['unresponsive', 'showing errors', 'disconnecting frequently'])} since {random.choice(['yesterday', 'this morning', 'last night'])}. This is impacting our {random.choice(['daily operations', 'customer service', 'sales processing'])}. Please help resolve this as soon as possible.",
            
            'Billing Question': f"Hi, I'm reviewing our account for {company['name']} and have a question about {random.choice(['our recent invoice', 'the billing cycle', 'payment methods', 'pricing structure'])}. Could someone please {random.choice(['explain the charges', 'provide clarification', 'send documentation', 'schedule a call'])} to help us understand this better?",
            
            'Feature Request': f"Our team at {company['name']} would like to request a new feature for {random.choice(['reporting', 'inventory management', 'staff scheduling', 'customer analytics'])}. Specifically, we need {random.choice(['custom dashboard capabilities', 'integration with our existing systems', 'mobile access', 'automated reporting'])}. This would help us {random.choice(['improve efficiency', 'better serve customers', 'streamline operations', 'make data-driven decisions'])}.",
            
            'Training': f"We need to schedule training for our team at {company['name']}. We have {random.choice(['new staff members', 'a new location opening', 'team members who need refreshers'])} and would like to arrange {random.choice(['on-site training', 'virtual training sessions', 'customized training materials'])}. Please let us know your availability.",
            
            'Integration Support': f"We're trying to integrate our existing {random.choice(['POS system', 'accounting software', 'inventory system', 'scheduling platform'])} with your platform at {company['name']}. We need assistance with {random.choice(['API configuration', 'data mapping', 'testing the connection', 'troubleshooting errors'])}. Can someone from your technical team help us with this?",
            
            'Account Management': f"I'd like to schedule an account review for {company['name']}. We want to discuss {random.choice(['our current service level', 'expansion plans', 'contract renewal', 'additional features'])} and ensure we're getting the most value from our partnership. Please let me know when we can schedule a meeting.",
            
            'Bug Report': f"We've discovered what appears to be a bug in the system at {company['name']}. The issue occurs when {random.choice(['generating reports', 'processing payments', 'updating inventory', 'accessing the dashboard'])} and results in {random.choice(['incorrect data', 'system errors', 'unexpected behavior', 'data not saving'])}. We can reproduce this consistently and have screenshots available.",
            
            'General Inquiry': f"Hi, I have a general question about {random.choice(['your service offerings', 'industry best practices', 'system capabilities', 'future roadmap'])} for {company['name']}. We're {random.choice(['evaluating options', 'planning for growth', 'looking to optimize', 'considering changes'])} and would appreciate any guidance you can provide."
        }
        
        return templates.get(category, f"General support request for {company['name']}.")
        
    def _generate_engagement_subject(self, engagement_type: str, context: str) -> str:
        """Generate realistic engagement subjects"""
        if context == 'sales':
            subjects = {
                'EMAIL': [
                    'Follow-up on Bar Management Demo',
                    'Pricing Proposal for Your Locations',
                    'Next Steps for Implementation',
                    'ROI Analysis for Your Review'
                ],
                'CALL': [
                    'Discovery Call - Bar Management Needs',
                    'Demo Scheduling Call',
                    'Pricing Discussion',
                    'Implementation Planning Call'
                ],
                'MEETING': [
                    'Product Demo Meeting',
                    'Stakeholder Alignment Meeting', 
                    'Contract Discussion Meeting',
                    'Implementation Kickoff Meeting'
                ],
                'NOTE': [
                    'Prospect Research Notes',
                    'Discovery Call Summary',
                    'Demo Feedback Notes',
                    'Decision Timeline Notes'
                ]
            }
        else:  # customer_success
            subjects = {
                'EMAIL': [
                    'Monthly Check-in',
                    'Feature Adoption Review',
                    'Account Health Assessment',
                    'Expansion Opportunity Discussion'
                ],
                'CALL': [
                    'Quarterly Business Review',
                    'Support Resolution Follow-up',
                    'Feature Training Call',
                    'Expansion Planning Call'
                ],
                'MEETING': [
                    'Quarterly Business Review Meeting',
                    'Success Planning Meeting',
                    'Training Session',
                    'Strategy Alignment Meeting'
                ],
                'NOTE': [
                    'Account Health Notes',
                    'Feature Usage Analysis',
                    'Expansion Readiness Assessment',
                    'Risk Mitigation Notes'
                ]
            }
            
        return random.choice(subjects.get(engagement_type, ['General Communication']))
        
    def _generate_engagement_body(self, engagement_type: str, company: Dict, context: str) -> str:
        """Generate realistic engagement content"""
        if context == 'sales':
            if engagement_type == 'EMAIL':
                return f"Following up on our conversation about implementing bar management solutions for {company['name']}. Based on your {company['location_count']} location{'s' if company['location_count'] > 1 else ''}, I've prepared a customized proposal that addresses your specific operational needs."
            elif engagement_type == 'CALL':
                return f"Discovery call with {company['name']} to understand their current challenges with managing {company['location_count']} location{'s' if company['location_count'] > 1 else ''}. Discussed pain points around inventory management, POS integration, and operational efficiency."
            elif engagement_type == 'MEETING':
                return f"Product demonstration for {company['name']} stakeholders. Showed key features relevant to {company['business_type'].lower()} operations including real-time inventory tracking, analytics dashboard, and multi-location management capabilities."
            else:  # NOTE
                return f"Researched {company['name']} - {company['business_type'].lower()} with {company['location_count']} location{'s' if company['location_count'] > 1 else ''}. Key decision makers identified, competitive landscape analyzed, and initial pain points documented."
        else:  # customer_success
            if engagement_type == 'EMAIL':
                return f"Monthly check-in for {company['name']}. Account is performing well with {company['location_count']} active location{'s' if company['location_count'] > 1 else ''}. Identified opportunities for feature adoption improvement and potential expansion."
            elif engagement_type == 'CALL':
                return f"Quarterly business review with {company['name']}. Reviewed performance metrics, discussed ROI achieved, and planned for upcoming quarter. Account health is strong with opportunities for growth."
            elif engagement_type == 'MEETING':
                return f"Success planning meeting with {company['name']} leadership. Aligned on business objectives, reviewed feature utilization across {company['location_count']} location{'s' if company['location_count'] > 1 else ''}, and identified expansion opportunities."
            else:  # NOTE
                return f"Account health assessment for {company['name']}. Strong engagement across locations, good feature adoption, low support ticket volume. Account is healthy with expansion potential identified."