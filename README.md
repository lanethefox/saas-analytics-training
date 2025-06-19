# Data Platform - Entity-Centric Analytics

A comprehensive data platform implementing Entity-Centric Modeling (ECM) for a bar management SaaS platform. This educational project demonstrates how to build production-grade analytics infrastructure that makes complex business questions answerable with simple SQL queries.

## 🎯 Project Overview

This platform serves 20,000+ accounts across 30,000+ locations with IoT-enabled tap systems. It showcases modern data engineering practices while teaching the principles of Entity-Centric Modeling - an approach that pre-aggregates business metrics into wide, denormalized tables for optimal analytical performance.

## 🚀 Quick Start

Get up and running in 5 minutes:

```bash
# 1. Clone the repository
git clone <repository-url>
cd data-platform

# 2. Set up environment
cp .env.example .env
# Edit .env with your database credentials

# 3. Run setup
./setup.sh

# 4. Connect and query
psql -h localhost -U analytics_user -d analytics
```

See [QUICK_START.md](QUICK_START.md) for detailed instructions.

## 📊 Core Entities

The platform implements 7 core business entities, each with 3 complementary tables:

| Entity | Description | Key Metrics |
|--------|-------------|-------------|
| **Customers** | Account-level business metrics | MRR, health score, churn risk |
| **Devices** | IoT tap device operations | Uptime, events, maintenance |
| **Locations** | Venue operational metrics | Revenue, device health |
| **Users** | Platform user engagement | Activity, adoption, features |
| **Subscriptions** | Revenue and billing | MRR movements, lifecycle |
| **Campaigns** | Marketing attribution | CAC, ROI, conversions |
| **Features** | Product analytics | Adoption, usage, impact |

## 🏗️ Architecture

### Entity-Centric Modeling (ECM)

Each entity follows a three-table pattern:

1. **Atomic Tables** (`entity_customers`) - Current state with real-time metrics
2. **History Tables** (`entity_customers_history`) - Complete change tracking
3. **Grain Tables** (`entity_customers_daily`) - Time-series aggregations

### Technology Stack

- **Database**: PostgreSQL with specialized schemas
- **Transformation**: dbt (data build tool) with 5-layer architecture
- **Orchestration**: Apache Airflow
- **Testing**: Comprehensive dbt tests and data quality checks

## 📚 Learning Resources

### Modules

1. **[SaaS Fundamentals](learning_modules/module_1_saas_fundamentals/)** - Bridge academic statistics to business analytics
2. **Advanced ECM** (Coming Soon) - Master temporal analytics and modeling
3. **Marketing Attribution** (Coming Soon) - Multi-touch attribution models
4. **ML Applications** (Coming Soon) - Churn prediction and CLV modeling

### Key Documentation

- [**Cross-Domain Interactions & Best Practices**](docs/CROSS_DOMAIN_INTERACTIONS_AND_BEST_PRACTICES.md) - Domain synthesis, governance, and dashboard design
- [Entity-Centric Data Model Guide](core_entity_data_model.md) - Complete entity structure and relationships
- [Platform Context](PLATFORM_CONTEXT.md) - Architecture and implementation status

### Example Queries

- [Power Queries](examples/01_power_queries_entity_customers.sql) - Single-table analytics magic
- [Business Scenarios](examples/02_business_scenarios.sql) - Real-world problem solving
- [Advanced Analytics](examples/03_advanced_power_queries.sql) - Sophisticated metrics
- [Strategic Analysis](examples/04_strategic_scenarios.sql) - Executive-level insights

## 🛠️ Project Structure

```
data-platform/
├── dbt_project/          # dbt models and transformations
│   ├── models/
│   │   ├── sources/      # Raw data definitions
│   │   ├── staging/      # Data standardization
│   │   ├── intermediate/ # Business logic
│   │   ├── entity/       # Core ECM entities
│   │   └── mart/         # Domain-specific views
│   └── tests/            # Data quality tests
├── examples/             # SQL query examples
├── learning_modules/     # Educational content
├── docs/                 # Documentation
└── scripts/              # Data generation tools
```

## 🔧 Key Features

- **No Joins Required**: 90% of business questions answered with single-table queries
- **Real-Time Ready**: Sub-3 second query performance on large datasets
- **Self-Service Analytics**: Business users can write their own queries
- **Comprehensive Metrics**: Pre-calculated health scores, risk indicators, and KPIs
- **Temporal Analytics**: Full history tracking for trend analysis

## 📈 Sample Insights

```sql
-- Find at-risk enterprise customers
SELECT company_name, mrr, churn_risk_score, customer_health_score
FROM entity.entity_customers
WHERE customer_tier = 3 AND churn_risk_score > 60
ORDER BY mrr DESC;

-- Identify expansion opportunities
SELECT company_name, current_mrr, 
       (999 - current_mrr) as expansion_potential
FROM entity.entity_customers
WHERE customer_tier = 1 AND total_devices > 10;
```

## 🤝 Contributing

This is an educational project designed to teach data modeling and analytics. Contributions that enhance the learning experience are welcome!

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built as a comprehensive educational resource for bridging the gap between academic statistical training and practical business analytics.