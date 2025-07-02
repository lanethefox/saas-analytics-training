[🏠 Home](../../) > [📚 Technical Docs](../) > 📊 Data Catalog

# 📊 Data Catalog

Comprehensive documentation of the TapFlow Analytics data warehouse.

**Last Updated:** 2024-12-16 | **Est. Reading Time:** 15 min | **Difficulty:** Intermediate

## 🎯 Overview

The Data Catalog provides complete documentation for our data warehouse containing:
- **450+ tables** across 5 schemas
- **2,500+ columns** with detailed descriptions
- **Entity relationships** and foreign keys
- **Data quality metrics** and profiling
- **Sample queries** for every table

## 📂 Catalog Sections

### [📁 Schemas](./schemas/)
High-level overview of our database schemas and their purposes.

**Available Schemas:**
- **[raw](./schemas/raw.md)** - Source system data (unchanged)
- **[staging](./schemas/staging.md)** - Cleaned and typed data
- **[intermediate](./schemas/intermediate.md)** - Business logic applied
- **[metrics](./schemas/metrics.md)** - Aggregated metrics and KPIs
- **[ml](./schemas/ml.md)** - Machine learning features and predictions

**Use this when:** Understanding data flow and transformation layers.

---

### [📋 Tables](./tables/)
Detailed documentation for every table in the warehouse.

**Popular Tables:**
- [Subscriptions](./tables/raw_app_database_subscriptions.md) - Revenue and billing
- [Accounts](./tables/raw_app_database_accounts.md) - Customer master data
- [Devices](./tables/raw_app_database_devices.md) - IoT device information
- [Tap Events](./tables/raw_app_database_tap_events.md) - Usage data

**Use this when:** Looking up specific table details and columns.

---

### [🔗 Relationships](./relationships.md)
Entity relationship diagrams and foreign key documentation.

**Key Relationships:**
- Account → Subscription (1:many)
- Account → Location (1:many)
- Location → Device (1:many)
- Device → Tap Event (1:many)

**Use this when:** Understanding how tables connect.

---

### [📊 Data Quality Report](./data_quality_report.md)
Current data quality metrics and monitoring.

**Metrics Tracked:**
- Completeness (null values)
- Uniqueness (duplicates)
- Validity (data types)
- Consistency (relationships)
- Timeliness (data freshness)

**Use this when:** Validating data reliability.

## 🔍 Quick Navigation

### By Business Domain

#### 🏢 Customer Data
- [Accounts](./tables/raw_app_database_accounts.md)
- [Users](./tables/raw_app_database_users.md)
- [Account Users](./tables/raw_app_database_account_users.md)

#### 💰 Revenue Data
- [Subscriptions](./tables/raw_app_database_subscriptions.md)
- [Subscription Events](./tables/raw_app_database_subscription_events.md)
- [Billing](./tables/raw_app_database_billing.md)

#### 📍 Location Data
- [Locations](./tables/raw_app_database_locations.md)
- [Location Types](./tables/raw_app_database_location_types.md)
- [Coordinates](./tables/raw_app_database_coordinates.md)

#### 🔧 Device Data
- [Devices](./tables/raw_app_database_devices.md)
- [Device Types](./tables/raw_app_database_device_types.md)
- [Device Events](./tables/raw_app_database_device_events.md)

#### 📊 Usage Data
- [Tap Events](./tables/raw_app_database_tap_events.md)
- [Session Analytics](./tables/raw_ga_session_analytics.md)
- [Feature Usage](./tables/raw_app_database_feature_usage.md)

## 📈 Data Statistics

### Current Scale
```
Total Database Size: 2.5 GB
Total Row Count: 50M+
Daily Growth Rate: ~100K rows
Update Frequency: Real-time to Daily
```

### Table Statistics
| Schema | Tables | Total Rows | Size |
|--------|--------|------------|------|
| raw | 285 | 45M | 1.8 GB |
| staging | 95 | 30M | 500 MB |
| intermediate | 45 | 15M | 150 MB |
| metrics | 20 | 5M | 50 MB |
| ml | 5 | 1M | 10 MB |

## 🛠️ Using the Data Catalog

### Finding Tables

1. **By Schema**: Browse [schemas](./schemas/) for logical groupings
2. **By Domain**: Use quick navigation above
3. **By Search**: Use browser search (Ctrl+F) on this page
4. **By Relationship**: Follow foreign keys in [relationships](./relationships.md)

### Understanding Tables

Each table page includes:
- **Description**: Business purpose and contents
- **Columns**: Full list with data types and descriptions
- **Keys**: Primary and foreign key definitions
- **Sample Data**: Example rows
- **Common Queries**: Copy-paste SQL examples
- **Data Quality**: Completeness and validity metrics

### Best Practices

1. **Start with schemas** to understand the big picture
2. **Check relationships** before writing JOINs
3. **Review data quality** before analysis
4. **Use sample queries** as templates
5. **Check update frequency** for freshness

## 🔗 Integration with Other Docs

### Related Documentation
- [Metrics Catalog](../metrics_catalog/) - Business metrics using these tables
- [Query Patterns](../api_reference/query_patterns.md) - Common SQL patterns
- [dbt Models](../../transform/models/) - Transformation logic
- [Entity Models](../core_entity_data_model.md) - Conceptual data model

### For Analysts
- [Sales Analytics Guide](../../edu/onboarding/sales/) - Using revenue tables
- [Marketing Analytics Guide](../../edu/onboarding/marketing/) - Campaign data
- [Product Analytics Guide](../../edu/onboarding/product/) - Usage analysis

## 🚀 Quick Start Queries

### Find Active Customers
```sql
SELECT COUNT(DISTINCT customer_id) as active_customers
FROM raw.app_database_subscriptions
WHERE status = 'active';
```

### Calculate MRR
```sql
SELECT SUM(monthly_price) as mrr
FROM raw.app_database_subscriptions
WHERE status = 'active';
```

### Device Uptime
```sql
SELECT 
    COUNT(CASE WHEN status = 'online' THEN 1 END) * 100.0 / COUNT(*) as uptime_pct
FROM raw.app_database_devices;
```

## 📋 Maintenance

The data catalog is automatically regenerated daily to reflect:
- New tables and columns
- Updated descriptions
- Current row counts
- Data quality metrics
- Fresh sample data

Manual regeneration:
```bash
python scripts/documentation/generate_data_catalog.py
```

---

<div class="nav-footer">

[← Technical Docs](../) | [Schemas →](./schemas/)

</div>

**Need help?** Check [SQL patterns](../api_reference/query_patterns.md) or [troubleshooting](../troubleshooting.md)