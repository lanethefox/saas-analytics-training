# SaaS Analytics Platform - Data Team Onboarding Guide

Welcome to the SaaS Analytics Platform! This comprehensive guide will help you get started as a Senior Data Analyst working with our B2B SaaS analytics platform for bar management systems.

## 🎯 Platform Overview

Our platform serves **20,000+ accounts** across **30,000+ locations** with IoT-enabled tap devices, providing real-time analytics and insights for bar operations, customer success, sales, marketing, and product teams.

### Key Platform Features
- **Entity-Centric Modeling (ECM)** with 7 core business entities
- **150+ pre-calculated metrics** for self-service analytics
- **Sub-3 second query performance** for dashboards
- **Unified data from 4+ source systems** (App, HubSpot, Stripe, Marketing)
- **Time-series support** with daily, weekly, and monthly aggregations

## 📚 Team-Specific Guides

Choose your team's guide to get started:

### 📊 [Sales Analytics Guide](./sales/README.md)
- Pipeline visibility and forecasting
- Sales performance tracking
- Lead quality analysis
- Territory management insights

### 🤝 [Customer Experience Analytics Guide](./customer-experience/README.md)
- Customer health monitoring
- Churn risk identification
- Support performance metrics
- User engagement analysis

### 📈 [Marketing Analytics Guide](./marketing/README.md)
- Campaign ROI analysis
- Multi-touch attribution
- Lead generation metrics
- Channel performance optimization

### 🚀 [Product Analytics Guide](./product/README.md)
- Feature adoption tracking
- User behavior analysis
- Platform usage patterns
- Retention and engagement metrics

## 🏗️ Platform Architecture

### Data Model Layers
```
Sources → Staging → Intermediate → Entity → Mart
```

### Core Entities
1. **Customers** - Account-level analytics
2. **Devices** - IoT tap monitoring
3. **Locations** - Venue operations
4. **Users** - User engagement
5. **Subscriptions** - Revenue tracking
6. **Campaigns** - Marketing ROI
7. **Features** - Product analytics

### Common Resources
- [Metrics Catalog](./common/metrics-catalog.md) - Complete list of available metrics
- [Query Patterns](./common/query-patterns.md) - Common SQL patterns and examples
- [Data Dictionary](./common/data-dictionary.md) - Entity and field definitions
- [Best Practices](./common/best-practices.md) - Analytics best practices

## 🚀 Getting Started

### 1. **Access Setup**
```bash
# Connect to the database
psql -h localhost -U saas_user -d saas_platform_dev
# Password: saas_secure_password_2024
```

### 2. **Key Tables to Know**
- **Current State**: `entity.entity_<name>` (e.g., `entity.entity_customers`)
- **Time Series**: `entity.entity_<name>_<grain>` (e.g., `entity.entity_customers_daily`)
- **History**: `entity.entity_<name>_history` (audit trail)
- **Metrics**: `metrics.<domain>` (e.g., `metrics.sales`)

### 3. **Your First Query**
```sql
-- Top 10 customers by health score
SELECT 
    customer_id,
    company_name,
    customer_health_score,
    monthly_recurring_revenue,
    churn_risk_score
FROM entity.entity_customers
WHERE customer_health_score IS NOT NULL
ORDER BY customer_health_score DESC
LIMIT 10;
```

## 🛠️ Tools & Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Apache Superset** | http://localhost:8088 | admin / admin_password_2024 |
| **Apache Airflow** | http://localhost:8080 | admin / admin_password_2024 |
| **Jupyter Lab** | http://localhost:8888 | Token: saas_ml_token_2024 |
| **MLflow** | http://localhost:5001 | - |
| **Grafana** | http://localhost:3000 | admin / grafana_admin_2024 |

## 📖 Documentation Structure

```
docs/onboarding/
├── README.md                    # This file
├── sales/                       # Sales team guide
│   ├── README.md               # Sales overview
│   ├── metrics-guide.md        # Sales metrics
│   ├── common-reports.md       # Standard reports
│   └── sql-examples.md         # Query examples
├── customer-experience/         # CX team guide
├── marketing/                   # Marketing team guide
├── product/                     # Product team guide
├── common/                      # Shared resources
│   ├── metrics-catalog.md      # All metrics
│   ├── query-patterns.md       # SQL patterns
│   ├── data-dictionary.md      # Entity definitions
│   └── best-practices.md       # Best practices
└── roadmap/                     # Future development
    ├── analyst-roadmap.md      # Analyst priorities
    └── data-scientist-roadmap.md # DS priorities
```

## 🔄 Development Workflow

1. **Explore Data**: Use Superset or SQL to explore entities
2. **Build Queries**: Start with pre-calculated metrics
3. **Create Reports**: Build domain-specific dashboards
4. **Share Insights**: Document and share findings
5. **Contribute**: Add new metrics or improve existing ones

## 🎯 Next Steps

1. Review your team-specific guide
2. Set up your local environment
3. Run example queries from your domain
4. Connect with your team lead for specific projects
5. Join the #data-platform Slack channel

## 📞 Support

- **Slack**: #data-platform
- **Documentation**: This guide + team wikis
- **Office Hours**: Tuesdays & Thursdays 2-3 PM

---

Welcome aboard! We're excited to have you join our data team. 🚀