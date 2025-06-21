# 🎓 B2B SaaS Analytics Training Platform

Learn data analytics with a complete, production-ready B2B SaaS platform. Real tools, real data, real skills.

## 🚀 What Is This?

This is a fully-functional analytics platform that simulates **TapFlow Analytics** - a B2B SaaS company providing IoT-powered beverage management for bars and restaurants. You'll learn by doing real analytics work on a platform used by 40,000+ businesses.

**New: Simplified setup!** Core services only by default. Get running in minutes, not hours.

### 🎯 Perfect For
- **Career Changers** wanting to break into data analytics
- **Students** learning practical data skills
- **Teams** training new analysts
- **Instructors** teaching analytics courses

## 📊 The Business You'll Analyze

**TapFlow Analytics** helps bars and restaurants:
- Track beverage pours in real-time
- Monitor inventory and reduce waste  
- Analyze sales patterns
- Predict equipment maintenance
- Optimize pricing and promotions

You'll work with data from:
- 🏢 40,000 customer accounts
- 📍 84,000 bar/restaurant locations
- 🔧 180,000 IoT tap devices
- 📈 3 years of business history
- 💰 Complete financial records
- 👥 User engagement tracking

## 🛠️ Tech Stack You'll Master

### Core Services (Default Setup)
- **PostgreSQL** - Industry-standard database with 3 years of data
- **dbt** - Modern data transformation framework
- **Apache Superset** - Business intelligence and dashboards
- **Jupyter Lab** - Interactive notebooks for analysis
- **Redis** - High-performance caching

### Optional Full Stack
Available with `--full` flag (see [BACKLOG.md](BACKLOG.md)):
- Apache Airflow - Workflow orchestration
- MLflow - ML experiment tracking
- Grafana & Prometheus - System monitoring

## 🎓 Choose Your Path

### 📚 [Learn Analytics](/edu)
Complete curriculum with hands-on projects:
- 16-week structured program
- Day-in-the-life simulations
- Real analyst projects
- Domain expertise in Sales, Marketing, Product & Customer Success

**[➡️ Start Learning](/edu)**

### 🔧 [Explore the Platform](/docs)
Technical documentation for the platform:
- Architecture & data models
- Setup & configuration
- API documentation
- Troubleshooting guides

**[➡️ View Documentation](/docs)**
## 🚦 Quick Start (10 minutes)

### Prerequisites
- Docker Desktop (4GB RAM for core, 8GB for full stack)
- Python 3.8+ (optional, for data generation)
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/data-platform.git
   cd data-platform
   ```

2. **Run the setup script**
   ```bash
   # Core services (recommended)
   ./setup.sh
   
   # Or full stack with all services
   ./setup.sh --full
   ```
   This will:
   - Start services (PostgreSQL, Redis, dbt, Superset, Jupyter)
   - Create databases and schemas
   - Generate sample data
   - Initialize dashboards

3. **Access your tools**
   
   | Tool | URL | Username | Password |
   |------|-----|----------|----------|
   | **Superset** (Dashboards) | http://localhost:8088 | admin | admin_password_2024 |
   | **Jupyter** (Notebooks) | http://localhost:8888 | - | Token: saas_ml_token_2024 |
   | **PostgreSQL** (Database) | localhost:5432 | saas_user | saas_secure_password_2024 |

4. **Verify setup**
   ```bash
   ./validate_setup.sh
   ```

5. **Start learning!**
   - Open Superset and explore the dashboards
   - Access Jupyter for interactive SQL and Python
   - Check out the education materials in `/edu`

## 💡 What You'll Build

By completing this program, you'll have:

### Portfolio Projects
- Sales pipeline optimization dashboard
- Customer churn prediction model
- Marketing attribution analysis
- Product adoption scorecard
- Executive KPI dashboard

### Practical Skills
- Write complex SQL queries
- Build data models with dbt
- Create compelling visualizations
- Automate data pipelines
- Present insights to stakeholders

### Career Readiness
- Real experience with industry tools
- Portfolio of completed projects
- Understanding of SaaS metrics
- Cross-functional business knowledge

## 🤝 Getting Help

- **Setup Issues?** Check [Troubleshooting](/docs/TROUBLESHOOTING.md)
- **Learning Questions?** See the [Education Hub](/edu)
- **Found a Bug?** [Open an issue](https://github.com/yourusername/saas-analytics-training/issues)
- **Community** Join our [Discord](https://discord.gg/analytics)

## 📈 Success Stories

> "This platform gave me the hands-on experience I needed to land my first analytics job. The projects in my portfolio were exactly what employers wanted to see." - Sarah M., Data Analyst

> "We use this to onboard all new analysts. They're productive in half the time compared to traditional training." - Tech Startup CPO

## 🎯 Ready to Start?

1. **[Set up the platform](/docs/SETUP.md)** (15 minutes)
2. **[Explore the curriculum](/edu/curriculum_overview.md)** (self-paced)
3. **[Try your first project](/edu/quarterly-projects)** (when ready)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>Transform your career with real analytics experience</b><br>
  <a href="/edu">Start Learning</a> •
  <a href="/docs">Documentation</a> •
  <a href="https://github.com/yourusername/saas-analytics-training">GitHub</a>
</p>