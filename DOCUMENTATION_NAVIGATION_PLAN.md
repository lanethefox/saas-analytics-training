# Documentation Navigation Plan

## Overview

This plan outlines the complete structure for creating a coherent, browsable documentation experience across the TapFlow Analytics platform. Every directory will have a README.md that serves as an index page with clear navigation to create a Wikipedia-like browsing experience.

## Core Principles

1. **No Dead Ends**: Every page links to related content, parent pages, and next steps
2. **Progressive Disclosure**: Start with overviews, drill down to details
3. **Role-Based Paths**: Clear learning journeys for each user type
4. **Consistent Navigation**: Same patterns across all documentation
5. **Self-Service**: Users can find what they need without external help

## Directory Structure

```
/ (root)
├── README.md                          # Master documentation hub
├── docs/                              # Technical documentation
│   ├── README.md                      # Technical docs index
│   ├── data_catalog/
│   │   ├── README.md                  # Data catalog overview
│   │   ├── schemas/
│   │   │   ├── README.md              # Schema guide
│   │   │   ├── raw.md
│   │   │   ├── staging.md
│   │   │   ├── intermediate.md
│   │   │   └── metrics.md
│   │   ├── tables/
│   │   │   ├── README.md              # Table index
│   │   │   └── [auto-generated pages]
│   │   ├── relationships.md
│   │   ├── data_quality_report.md
│   │   └── data_dictionary.md
│   ├── metrics_catalog/
│   │   ├── README.md                  # Metrics overview
│   │   ├── revenue_metrics.md
│   │   ├── operational_metrics.md
│   │   ├── customer_metrics.md
│   │   ├── product_metrics.md
│   │   ├── metric_lineage.md
│   │   └── calculation_examples.md
│   ├── api_reference/
│   │   ├── README.md                  # API guide
│   │   ├── query_patterns.md
│   │   ├── performance_tips.md
│   │   └── best_practices.md
│   └── architecture/
│       ├── README.md                  # System architecture
│       ├── data_flow.md
│       └── technology_stack.md
└── edu/                               # Educational content
    ├── README.md                      # Education hub
    ├── getting_started/
    │   ├── README.md                  # New user guide
    │   ├── platform_overview.md
    │   ├── account_setup.md
    │   └── first_query.md
    ├── onboarding/
    │   ├── README.md                  # Role selection
    │   ├── sales/
    │   │   ├── README.md              # Sales track overview
    │   │   ├── day1_platform_overview.md
    │   │   ├── day2_revenue_metrics.md
    │   │   ├── day3_pipeline_analysis.md
    │   │   ├── day4_forecasting.md
    │   │   ├── day5_dashboards.md
    │   │   └── certification.md
    │   ├── marketing/
    │   │   ├── README.md              # Marketing track overview
    │   │   └── [similar structure]
    │   ├── product/
    │   │   ├── README.md              # Product track overview
    │   │   └── [similar structure]
    │   ├── customer_success/
    │   │   ├── README.md              # CS track overview
    │   │   └── [similar structure]
    │   └── analytics_engineering/
    │       ├── README.md              # AE track overview
    │       ├── week1_technical_foundation.md
    │       ├── week2_data_modeling.md
    │       ├── week3_transformations.md
    │       └── week4_optimization.md
    ├── workday_simulations/
    │   ├── README.md                  # Simulation overview
    │   ├── daily/
    │   │   ├── README.md              # Daily tasks guide
    │   │   ├── sales_analyst_day.md
    │   │   ├── marketing_analyst_day.md
    │   │   ├── product_analyst_day.md
    │   │   └── cs_analyst_day.md
    │   ├── monthly_projects/
    │   │   ├── README.md              # Monthly project guide
    │   │   ├── cohort_analysis.md
    │   │   ├── revenue_deep_dive.md
    │   │   ├── customer_segmentation.md
    │   │   └── churn_prediction.md
    │   └── quarterly_initiatives/
    │       ├── README.md              # Quarterly guide
    │       ├── data_quality_improvement.md
    │       ├── new_metrics_rollout.md
    │       └── platform_migration.md
    ├── team_okrs/
    │   ├── README.md                  # OKR overview
    │   ├── methodology.md
    │   ├── templates/
    │   │   ├── README.md
    │   │   └── okr_template.md
    │   └── q1_2025/
    │       ├── README.md              # Q1 overview
    │       ├── sales_okrs.md
    │       ├── marketing_okrs.md
    │       ├── product_okrs.md
    │       ├── cs_okrs.md
    │       └── ae_okrs.md
    └── resources/
        ├── README.md                  # Additional resources
        ├── glossary.md
        ├── faq.md
        └── troubleshooting.md
```

## Navigation Components

### 1. Standard Page Header
Every README.md and content page includes:

```markdown
[🏠 Home](/) > [📚 Docs](/docs/) > [📊 Data Catalog](/docs/data_catalog/) > Current Page

# Page Title

*Brief description of what this section contains*

**Last Updated:** 2024-12-16 | **Est. Reading Time:** 10 min | **Difficulty:** Beginner
```

### 2. Navigation Cards
Index pages use card-based navigation:

```markdown
## 📂 In This Section

<div class="nav-cards">

### 📊 [Data Catalog](/docs/data_catalog/)
Explore database schemas, tables, and relationships. Perfect for understanding our data model.
**450+ tables documented**

### 📈 [Metrics Catalog](/docs/metrics_catalog/)
Business metrics and KPIs with SQL examples. Essential for analysts.
**50+ metrics defined**

### 🔌 [API Reference](/docs/api_reference/)
Query patterns and optimization tips. For power users.
**20+ examples**

</div>
```

### 3. Progress Indicators
For educational content:

```markdown
## 📚 Your Learning Progress

- [x] Day 1: Platform Overview
- [x] Day 2: Revenue Metrics
- [ ] Day 3: Pipeline Analysis ← **You are here**
- [ ] Day 4: Forecasting
- [ ] Day 5: Dashboards
```

### 4. Standard Page Footer

```markdown
---

<div class="nav-footer">

← [Previous: Topic Name](./previous.md) | [Up: Parent Section](./README.md) | [Next: Topic Name](./next.md) →

</div>

**Need help?** Check our [FAQ](/edu/resources/faq.md) or [Troubleshooting Guide](/edu/resources/troubleshooting.md)
```

## Content Templates

### 1. Master Hub (Root README.md)

```markdown
# 🎯 TapFlow Analytics Documentation Hub

Welcome to the comprehensive documentation for TapFlow Analytics, your B2B SaaS platform for beverage dispensing analytics.

## 🚀 Quick Start

Choose your path:

### 👨‍💼 I'm a Business User
Start with our [Education Hub](/edu/) for role-based learning paths, hands-on tutorials, and real-world scenarios.

**Popular destinations:**
- [5-Day Sales Onboarding](/edu/onboarding/sales/)
- [Marketing Analytics Basics](/edu/onboarding/marketing/)
- [Daily Workflow Simulations](/edu/workday_simulations/daily/)

### 👩‍💻 I'm a Technical User
Dive into our [Technical Documentation](/docs/) for detailed API references, data models, and architecture guides.

**Popular destinations:**
- [Data Catalog](/docs/data_catalog/)
- [SQL Query Patterns](/docs/api_reference/query_patterns.md)
- [dbt Model Documentation](/docs/data_catalog/schemas/metrics.md)

## 📍 Navigation Tips

- Every folder has a README.md with an overview
- Use breadcrumbs at the top of each page
- Look for "Related Topics" sections
- Check "Prerequisites" before starting new sections

## 🔍 Search
Use Ctrl+F (Cmd+F on Mac) to search within pages. For global search, use GitHub's search feature.
```

### 2. Section Index (e.g., docs/README.md)

```markdown
# 📚 Technical Documentation

Complete technical reference for the TapFlow Analytics platform.

## 🎯 What You'll Find Here

This section contains detailed technical documentation for developers, data engineers, and power users.

## 📂 Documentation Sections

### [📊 Data Catalog](/docs/data_catalog/)
- Database schemas and tables
- Column definitions and data types
- Entity relationships
- Data quality metrics
- **Use when:** You need to understand data structure

### [📈 Metrics Catalog](/docs/metrics_catalog/)
- Business metric definitions
- Calculation methodologies
- SQL implementations
- Metric lineage
- **Use when:** You need to implement or verify metrics

### [🔌 API Reference](/docs/api_reference/)
- Query patterns and examples
- Performance optimization
- Best practices
- Common pitfalls
- **Use when:** You're writing queries or integrations

### [🏗️ Architecture](/docs/architecture/)
- System design
- Data flow diagrams
- Technology stack
- Infrastructure details
- **Use when:** You need system-level understanding

## 🚦 Prerequisites

- Basic SQL knowledge
- Understanding of data warehousing concepts
- Familiarity with business intelligence

## 🎓 New to Technical Concepts?

Start with our [Analytics Engineering Onboarding](/edu/onboarding/analytics_engineering/) for a guided introduction.
```

### 3. Learning Path Index (e.g., edu/onboarding/sales/README.md)

```markdown
# 💼 Sales Analytics Onboarding

Welcome to your 5-day journey to becoming a Sales Analytics expert!

## 🎯 What You'll Learn

By the end of this program, you'll be able to:
- ✅ Navigate the TapFlow Analytics platform confidently
- ✅ Build and interpret revenue dashboards
- ✅ Analyze sales pipeline health
- ✅ Create accurate forecasts
- ✅ Present insights to stakeholders

## 📅 Your 5-Day Journey

### Day 1: [Platform Overview](./day1_platform_overview.md)
Get familiar with TapFlow's interface, data model, and core concepts.
**Duration:** 2 hours | **Hands-on exercises:** 3

### Day 2: [Revenue Metrics Mastery](./day2_revenue_metrics.md)
Deep dive into MRR, ARR, and other key revenue indicators.
**Duration:** 3 hours | **Hands-on exercises:** 5

### Day 3: [Pipeline Analysis](./day3_pipeline_analysis.md)
Learn to track deals, conversion rates, and sales velocity.
**Duration:** 3 hours | **Hands-on exercises:** 4

### Day 4: [Forecasting Fundamentals](./day4_forecasting.md)
Build reliable revenue forecasts using historical data.
**Duration:** 2.5 hours | **Hands-on exercises:** 3

### Day 5: [Executive Dashboards](./day5_dashboards.md)
Create compelling visualizations for leadership.
**Duration:** 2.5 hours | **Final project:** 1

## 📋 Prerequisites

- [ ] TapFlow account with Sales Analyst permissions
- [ ] Basic understanding of SaaS business models
- [ ] Familiarity with spreadsheets
- [ ] 15 hours available over 5 days

## 🏆 Certification

Complete all exercises to earn your **Sales Analytics Certification**!

## 🚀 Ready to Start?

[Begin Day 1: Platform Overview →](./day1_platform_overview.md)

---

**Need help?** Join our [Sales Analysts Slack channel](#) or check the [FAQ](/edu/resources/faq.md)
```

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Create all README.md index files
2. Implement navigation templates
3. Set up breadcrumb structure
4. Create master hub pages

### Phase 2: Content Migration (Week 2)
1. Update existing content with navigation
2. Add metadata headers
3. Implement cross-references
4. Create missing linking pages

### Phase 3: Enhancement (Week 3)
1. Add progress tracking
2. Implement navigation cards
3. Create role-based paths
4. Add search functionality

### Phase 4: Polish (Week 4)
1. User testing
2. Fix broken links
3. Optimize navigation flow
4. Add interactive elements

## Maintenance Strategy

1. **Automated Checks**
   - Link validation in CI/CD
   - Navigation consistency tests
   - Last-updated timestamps

2. **Regular Reviews**
   - Monthly navigation audit
   - Quarterly content reorganization
   - Annual structure assessment

3. **User Feedback**
   - Navigation analytics
   - User journey tracking
   - Feedback forms on each page

## Success Metrics

- Average pages per session > 5
- Bounce rate < 30%
- Time to find information < 2 minutes
- User satisfaction > 4.5/5
- Complete learning paths > 70%

## Next Steps

1. Review and approve this plan
2. Create implementation tickets
3. Begin with Phase 1 foundation work
4. Set up analytics tracking
5. Schedule user testing sessions