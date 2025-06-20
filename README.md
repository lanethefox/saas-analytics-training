# 🎓 B2B SaaS Analytics Platform - Educational Edition

Learn real-world data analytics with production-grade tools and comprehensive business scenarios.

## 🚀 Quick Start (15 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/data-platform
cd data-platform

# Run the setup script
./setup.sh

# Access the platform
# Superset: http://localhost:8088 (admin/admin_password_2024)
# Jupyter: http://localhost:8888 (token: saas_ml_token_2024)
```

## 📚 What You'll Learn

- **Modern Data Stack**: PostgreSQL, dbt, Apache Superset, Docker
- **Entity-Centric Modeling**: Industry best practices for analytics
- **Business Analytics**: Sales, Marketing, Customer Success, Product domains
- **Real-World Skills**: SQL, data modeling, KPIs, dashboards, reporting

### 🆕 Enhanced Learning Features
- **Interactive SQL Tutorials**: Level-based exercises with instant feedback
- **Automated Onboarding**: Self-guided setup verification and skill assessment
- **Metric Lineage Docs**: Visual tracking from raw data to business insights

## 🎯 Perfect For

- Data Analytics Bootcamps
- University Data Science Courses
- Corporate Training Programs
- Self-Directed Learning

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

## 📊 Platform Overview

### Sample Data
- 40,000 synthetic B2B accounts
- 84,000 locations across industries
- 180,000 IoT devices with telemetry
- $27M in monthly recurring revenue
- 3 years of historical data

### Technology Stack
- **Database**: PostgreSQL with raw data schemas
- **Transformation**: dbt with 81 pre-built models
- **Visualization**: Apache Superset dashboards
- **Orchestration**: Apache Airflow (optional)
- **Development**: Jupyter Lab environment

### Learning Modules
1. **Sales Analytics**: Pipeline health, forecasting, territory planning
2. **Customer Success**: Churn prediction, health scoring, expansion
3. **Marketing Analytics**: Attribution, CAC, campaign ROI
4. **Product Analytics**: Feature adoption, usage patterns, retention

## 🛠️ Prerequisites

- Docker Desktop (8GB RAM minimum)
- Python 3.8+ (for data generation scripts)
- 20GB free disk space
- Basic SQL knowledge helpful

## 📖 Documentation

- [Installation Guide](SETUP.md) - Detailed setup instructions
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Curriculum Guide](education/curriculum_overview.md) - Learning paths
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/data-platform/issues)
- **Community**: [Discord Server](https://discord.gg/analytics-education)
- **Updates**: Watch this repo for new features

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

*Built with ❤️ for analytics education. Transform how you teach and learn data analytics.*