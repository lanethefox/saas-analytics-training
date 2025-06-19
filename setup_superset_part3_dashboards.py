#!/usr/bin/env python3
"""
Enhanced Superset Setup - Part 3: Dashboard Creation with Documentation
"""

import json
import time
from setup_superset_part1 import SupersetClient
from setup_superset_part2_charts import *

def create_dashboard_with_charts(client, title, slug, description, charts, layout_type="grid"):
    """Create a dashboard with proper layout"""
    headers = {
        'X-CSRFToken': client.api_csrf_token,
        'Content-Type': 'application/json'
    }
    
    # Create position JSON for charts
    position_json = {
        "DASHBOARD_VERSION_KEY": "v2",
        "GRID_ID": {
            "id": "GRID_ID",
            "type": "GRID",
            "children": []
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "type": "HEADER",
            "meta": {
                "text": title
            }
        }
    }
    
    # Add markdown component for documentation
    doc_id = "MARKDOWN-doc"
    position_json[doc_id] = {
        "id": doc_id,
        "type": "MARKDOWN",
        "children": [],
        "meta": {
            "width": 12,
            "height": 4,
            "code": description
        }
    }
    position_json["GRID_ID"]["children"].append(doc_id)
    
    # Layout charts in grid
    row_height = 4
    charts_per_row = 2
    
    for i, chart_id in enumerate(charts):
        row_num = i // charts_per_row
        col_num = i % charts_per_row
        
        row_id = f"ROW-{row_num}"
        if row_id not in position_json:
            position_json[row_id] = {
                "id": row_id,
                "type": "ROW",
                "children": [],
                "meta": {
                    "background": "BACKGROUND_TRANSPARENT"
                }
            }
            position_json["GRID_ID"]["children"].append(row_id)
        
        chart_key = f"CHART-{chart_id}"
        position_json[chart_key] = {
            "id": chart_key,
            "type": "CHART",
            "children": [],
            "meta": {
                "width": 6,
                "height": row_height,
                "chartId": chart_id
            }
        }
        position_json[row_id]["children"].append(chart_key)
    
    # Create dashboard
    dashboard_config = {
        "dashboard_title": title,
        "slug": slug,
        "position_json": json.dumps(position_json),
        "published": True,
        "css": """
            .dashboard-markdown {
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .dashboard-markdown h2 {
                color: #1a73e8;
                margin-bottom: 10px;
            }
            .dashboard-markdown h3 {
                color: #5f6368;
                margin-top: 20px;
            }
            .dashboard-markdown code {
                background-color: #e8eaed;
                padding: 2px 4px;
                border-radius: 3px;
            }
        """,
        "json_metadata": json.dumps({
            "timed_refresh_immune_slices": [],
            "expanded_slices": {},
            "refresh_frequency": 0,
            "default_filters": "{}",
            "color_scheme": "supersetColors",
            "label_colors": {},
            "shared_label_colors": {},
            "color_scheme_domain": [],
            "cross_filters_enabled": True
        })
    }
    
    response = client.session.post(
        f"{SUPERSET_URL}/api/v1/dashboard/",
        headers=headers,
        json=dashboard_config
    )
    
    if response.status_code == 201:
        dashboard_id = response.json()['id']
        print(f"✅ Created dashboard: {title} (ID: {dashboard_id})")
        return dashboard_id
    else:
        print(f"❌ Failed to create dashboard: {response.status_code}")
        print(response.text)
        return None

def create_all_dashboards(client):
    """Create all domain dashboards"""
    dashboards = []
    
    # 1. Customer Success Dashboard
    cs_description = """## 🎯 Customer Success Command Center

### Overview
This dashboard provides real-time visibility into customer health, satisfaction, and retention metrics. Use it to identify at-risk accounts, track customer lifecycle progression, and measure the impact of customer success initiatives.

### Key Metrics Explained
- **Customer Health Score (0-100)**: Composite metric based on:
  - Product usage frequency (40%)
  - Feature adoption depth (20%)  
  - Support ticket sentiment (20%)
  - Payment history (20%)

- **Churn Risk Score**: ML-powered prediction based on:
  - Historical churn patterns
  - Usage decline indicators
  - Support interaction frequency
  - Contract renewal proximity

- **Net Revenue Retention (NRR)**: Measures expansion revenue from existing customers
  - >120% = Excellent (strong upsells)
  - 100-120% = Good (stable growth)
  - <100% = Needs attention (churn > expansion)

### Action Triggers
🔴 **Immediate Action** (Risk Score >80):
- Schedule executive business review
- Prepare retention offer
- Assign senior CSM

🟡 **Proactive Outreach** (Risk Score 60-80):
- Increase check-in frequency
- Offer training sessions
- Review feature adoption

🟢 **Growth Opportunity** (Health Score >85):
- Present upsell options
- Request testimonials
- Explore referral opportunities

### Data Sources & Freshness
- **Real-time**: Usage events, support tickets
- **Hourly**: Health score recalculation
- **Daily**: Churn risk model update
- **Weekly**: NRR calculation
"""
    
    cs_charts = create_customer_success_charts(client)
    if cs_charts:
        dash_id = create_dashboard_with_charts(
            client,
            "🎯 Customer Success Command Center",
            "customer-success",
            cs_description,
            cs_charts
        )
        if dash_id:
            dashboards.append(("Customer Success", dash_id))
    
    # 2. Sales Dashboard
    sales_description = """## 💰 Sales Pipeline & Performance

### Overview
Track pipeline health, conversion rates, and sales velocity across all stages. This dashboard helps sales leaders identify bottlenecks, forecast revenue, and optimize sales processes.

### Pipeline Stages
1. **Qualified Lead** → 2. **Demo Scheduled** → 3. **Proposal Sent** → 4. **Negotiation** → 5. **Closed Won/Lost**

### Key Performance Indicators
- **Pipeline Coverage Ratio**: Pipeline value ÷ Quota (Target: 3-4x)
- **Stage Conversion Rates**: Success rate between stages
- **Sales Velocity**: (Opportunities × Deal Size × Win Rate) ÷ Cycle Length
- **Average Deal Size**: Total revenue ÷ Number of deals

### Sales Methodology Notes
- Follows MEDDIC qualification framework
- Weighted pipeline uses stage-based probabilities
- Multi-threaded deals have 2.5x higher close rates

### Forecasting Accuracy
- **Commit**: 90% confidence (included in forecast)
- **Best Case**: 60% confidence (upside scenario)
- **Pipeline**: <30% confidence (future quarters)
"""
    
    sales_charts = create_sales_charts(client)
    if sales_charts:
        dash_id = create_dashboard_with_charts(
            client,
            "💰 Sales Pipeline & Performance",
            "sales-pipeline",
            sales_description,
            sales_charts
        )
        if dash_id:
            dashboards.append(("Sales", dash_id))
    
    # 3. Marketing Dashboard
    marketing_description = """## 📈 Marketing Attribution & Performance

### Overview
Multi-touch attribution analysis across all marketing channels. Understand which campaigns drive revenue, optimize channel mix, and improve marketing ROI.

### Attribution Models
- **First Touch**: Credits initial awareness touchpoint
- **Last Touch**: Credits converting interaction
- **Linear**: Equal distribution across all touches
- **Time Decay**: Recent touches weighted higher (half-life: 7 days)
- **W-Shaped**: 30% first, 30% lead creation, 30% opportunity, 10% others

### Channel Taxonomy
- **Paid Search**: Google Ads, Bing Ads (intent-based)
- **Social Paid**: LinkedIn, Facebook, Twitter (awareness)
- **Email**: Nurture sequences, newsletters (engagement)
- **Organic**: SEO, content marketing (thought leadership)
- **Direct**: Brand searches, type-in traffic (brand strength)

### ROI Calculations
- **CAC** = Total Spend ÷ New Customers
- **ROAS** = Revenue ÷ Ad Spend
- **Payback Period** = CAC ÷ (ARPU × Gross Margin)

### Campaign Naming Convention
Format: `[Channel]_[Type]_[Audience]_[Date]_[Version]`
Example: `LinkedIn_Sponsored_Enterprise_2024Q1_A`
"""
    
    marketing_charts = create_marketing_charts(client)
    if marketing_charts:
        dash_id = create_dashboard_with_charts(
            client,
            "📈 Marketing Attribution & Performance",
            "marketing-attribution",
            marketing_description,
            marketing_charts
        )
        if dash_id:
            dashboards.append(("Marketing", dash_id))
    
    # 4. Product Dashboard  
    product_description = """## 🚀 Product Adoption & Usage Analytics

### Overview
Monitor feature adoption, user engagement patterns, and product-market fit indicators. Guide product development priorities based on usage data and user feedback.

### Adoption Metrics Framework
- **Adoption Rate**: Users who tried feature ÷ Total users
- **Activation Rate**: Users who achieved value ÷ Users who tried
- **Retention Rate**: Users still active after 30 days ÷ Activated users
- **Depth of Use**: Features used per user (target: >3)

### User Segmentation
- **Power Users**: Top 10% by activity (early adopters)
- **Regular Users**: 25-75th percentile (core base)
- **Casual Users**: Bottom 25% (growth opportunity)
- **Dormant Users**: No activity >30 days (win-back targets)

### Feature Value Scoring
Value Score = (Adoption × Retention × Revenue Impact) ^ (1/3)
- High Value (>80): Core differentiators
- Medium Value (50-80): Table stakes
- Low Value (<50): Sunset candidates

### Product-Led Growth Signals
- Time to Value: <24 hours (excellent)
- Feature Discovery Rate: >60% (viral loops working)
- User Invitation Rate: >0.5 per user (network effects)
"""
    
    product_charts = create_product_charts(client)
    if product_charts:
        dash_id = create_dashboard_with_charts(
            client,
            "🚀 Product Adoption & Usage Analytics",
            "product-analytics",
            product_description,
            product_charts
        )
        if dash_id:
            dashboards.append(("Product", dash_id))
    
    # 5. Operations Dashboard
    operations_description = """## ⚙️ Operations Command Center

### Overview
Real-time monitoring of device fleet health, location performance, and operational efficiency. Ensure SLA compliance and optimize resource allocation.

### Device Health Monitoring
- **Online**: Responding to pings, processing transactions
- **Offline**: No response >5 minutes (investigate)
- **Maintenance**: Scheduled downtime (planned)
- **Error State**: Repeated failures (urgent)

### Performance Thresholds
- **Response Time**: <200ms (green), 200-500ms (yellow), >500ms (red)
- **Error Rate**: <0.1% (green), 0.1-1% (yellow), >1% (red)
- **Throughput**: >100 tps (green), 50-100 tps (yellow), <50 tps (red)

### Predictive Maintenance Model
- **Risk Score Components**:
  - Device age and usage hours
  - Error frequency patterns
  - Environmental factors
  - Historical failure data

### SLA Tracking
- **Uptime Target**: 99.9% (43 minutes/month allowed)
- **MTTR Target**: <4 hours
- **MTBF Target**: >720 hours

### Escalation Matrix
- L1: Device offline >15 min → Field tech dispatch
- L2: Location down >1 hour → Regional manager
- L3: Multiple locations affected → VP Operations
"""
    
    ops_charts = create_operations_charts(client)
    if ops_charts:
        dash_id = create_dashboard_with_charts(
            client,
            "⚙️ Operations Command Center",
            "operations-monitoring",
            operations_description,
            ops_charts
        )
        if dash_id:
            dashboards.append(("Operations", dash_id))
    
    return dashboards

def main():
    """Main execution function"""
    print("🚀 Superset Setup - Creating Dashboards")
    print("=" * 50)
    
    # Initialize client
    client = SupersetClient()
    
    # Login
    if not client.login():
        print("❌ Failed to login to Superset")
        return
    
    # Load dataset mappings from Part 1
    try:
        with open('/tmp/superset_datasets.json', 'r') as f:
            client.datasets = json.load(f)
        print(f"✅ Loaded {len(client.datasets)} dataset mappings")
    except:
        print("⚠️  No dataset mappings found - running dataset setup first")
        client.setup_all_datasets()
    
    # Create all dashboards
    dashboards = create_all_dashboards(client)
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Dashboard Creation Complete!")
    print("=" * 50)
    
    print("\n📊 Dashboards Created:")
    for name, dash_id in dashboards:
        print(f"   • {name} (ID: {dash_id})")
        print(f"     URL: {SUPERSET_URL}/superset/dashboard/{dash_id}/")
    
    print("\n📚 Each Dashboard Includes:")
    print("   • Interactive visualizations with drill-down capability")
    print("   • Comprehensive documentation and metric definitions")
    print("   • Action triggers and thresholds")
    print("   • Data freshness indicators")
    print("   • Cross-filtering between charts")
    
    print("\n🎯 Next Steps:")
    print("   1. Visit each dashboard URL above")
    print("   2. Set up scheduled email reports")
    print("   3. Configure alerts for critical metrics")
    print("   4. Share dashboards with stakeholders")
    print("   5. Customize layouts and add additional charts as needed")

if __name__ == "__main__":
    main()