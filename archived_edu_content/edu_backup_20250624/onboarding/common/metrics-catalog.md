# Metrics Catalog

This catalog provides a comprehensive list of all pre-calculated metrics available in the SaaS Analytics Platform, organized by domain and entity.

## 📊 Customer Success Metrics

### Health & Risk Indicators
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `customer_health_score` | Composite health score (0-100) | `entity_customers` | Daily |
| `churn_risk_score` | Churn risk indicator (0-100) | `entity_customers` | Daily |
| `composite_success_score` | Overall success metric | `metrics_customer_success` | Daily |
| `health_trend_30d` | 30-day health score trend | `metrics_customer_success` | Daily |

### Engagement Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `monthly_active_users` | MAU count | `entity_customers` | Daily |
| `weekly_active_users` | WAU count | `entity_customers` | Daily |
| `daily_active_users` | DAU count | `entity_customers` | Daily |
| `user_activation_rate` | % of activated users | `metrics_customer_success` | Daily |
| `avg_engagement_score` | Average user engagement | `metrics_customer_success` | Daily |

### Revenue Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `monthly_recurring_revenue` | Current MRR | `entity_customers` | Daily |
| `annual_recurring_revenue` | Current ARR | `entity_customers` | Daily |
| `lifetime_value` | Customer LTV | `entity_customers` | Weekly |
| `expansion_revenue_30d` | Expansion MRR last 30d | `metrics_customer_success` | Daily |

## 💼 Sales Metrics

### Pipeline Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `total_pipeline_value` | Total open pipeline | `metrics_sales` | Daily |
| `qualified_pipeline_value` | Qualified opportunities | `metrics_sales` | Daily |
| `pipeline_coverage_ratio` | Pipeline to quota ratio | `metrics_sales` | Daily |
| `avg_deal_size` | Average deal value | `metrics_sales` | Daily |
| `avg_sales_cycle_days` | Sales cycle length | `metrics_sales` | Daily |

### Performance Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `deals_won_mtd` | Deals closed MTD | `metrics_sales` | Daily |
| `revenue_closed_mtd` | Revenue closed MTD | `metrics_sales` | Daily |
| `win_rate` | Deal win percentage | `metrics_sales` | Daily |
| `quota_attainment` | % of quota achieved | `metrics_sales` | Daily |

### Activity Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `calls_made_30d` | Sales calls last 30d | `metrics_sales` | Daily |
| `emails_sent_30d` | Sales emails last 30d | `metrics_sales` | Daily |
| `meetings_held_30d` | Meetings last 30d | `metrics_sales` | Daily |
| `activities_per_opportunity` | Activity ratio | `metrics_sales` | Daily |

## 📈 Marketing Metrics

### Campaign Performance
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `overall_roi` | Blended campaign ROI | `metrics_marketing` | Daily |
| `facebook_roi` | Facebook ads ROI | `metrics_marketing` | Daily |
| `google_roi` | Google ads ROI | `metrics_marketing` | Daily |
| `linkedin_roi` | LinkedIn ads ROI | `metrics_marketing` | Daily |
| `cost_per_acquisition` | Blended CPA | `metrics_marketing` | Daily |

### Lead Generation
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `total_mqls` | Marketing qualified leads | `metrics_marketing` | Daily |
| `mql_conversion_rate` | MQL to SQL rate | `metrics_marketing` | Daily |
| `cost_per_mql` | Cost per MQL | `metrics_marketing` | Daily |
| `lead_velocity_rate` | Month-over-month growth | `metrics_marketing` | Monthly |

### Attribution Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `avg_touchpoints_to_conversion` | Attribution touchpoints | `metrics_marketing` | Daily |
| `first_touch_channel` | First touch attribution | `entity_campaigns` | Daily |
| `last_touch_channel` | Last touch attribution | `entity_campaigns` | Daily |
| `multi_touch_credit` | Multi-touch attribution | `entity_campaigns` | Daily |

## 🚀 Product Analytics Metrics

### Usage Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `daily_active_users` | DAU | `metrics_product_analytics` | Daily |
| `weekly_active_users` | WAU | `metrics_product_analytics` | Daily |
| `monthly_active_users` | MAU | `metrics_product_analytics` | Daily |
| `dau_mau_ratio` | Stickiness ratio | `metrics_product_analytics` | Daily |

### Feature Adoption
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `feature_adoption_rate` | % using feature | `entity_features` | Daily |
| `usage_intensity_score` | Feature usage depth | `entity_features` | Daily |
| `retention_impact_score` | Impact on retention | `entity_features` | Weekly |
| `time_to_first_use_days` | Adoption speed | `entity_features` | Daily |

### Device Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `overall_health_score` | Device health (0-100) | `entity_devices` | Hourly |
| `uptime_percentage_30d` | 30-day uptime | `entity_devices` | Daily |
| `total_volume_liters_30d` | Volume poured | `entity_devices` | Daily |
| `estimated_revenue_30d` | Revenue contribution | `entity_devices` | Daily |

## 🔄 Unified Metrics

### Cross-Domain Metrics
| Metric | Description | Table | Update Frequency |
|--------|-------------|-------|------------------|
| `net_revenue_retention` | NRR % | `metrics_unified` | Monthly |
| `gross_revenue_retention` | GRR % | `metrics_unified` | Monthly |
| `customer_acquisition_cost` | CAC | `metrics_unified` | Monthly |
| `ltv_cac_ratio` | LTV:CAC ratio | `metrics_unified` | Monthly |

## 📋 Metric Naming Conventions

### Suffixes
- `_30d` - Rolling 30-day window
- `_7d` - Rolling 7-day window
- `_mtd` - Month to date
- `_qtd` - Quarter to date
- `_ytd` - Year to date
- `_rate` - Percentage (0-100)
- `_score` - Normalized score (0-100)
- `_days` - Duration in days
- `_count` - Absolute count

### Prefixes
- `avg_` - Average
- `total_` - Sum
- `min_` - Minimum
- `max_` - Maximum
- `pct_` - Percentage of total

## 🔍 Finding Metrics

### By Domain
```sql
-- List all sales metrics
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'metrics' 
  AND table_name = 'sales'
ORDER BY ordinal_position;
```

### By Entity
```sql
-- List all customer entity metrics
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'entity' 
  AND table_name = 'entity_customers'
  AND column_name LIKE '%score%'
ORDER BY ordinal_position;
```

### Search by Pattern
```sql
-- Find all health-related metrics
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE table_schema IN ('entity', 'metrics')
  AND column_name LIKE '%health%'
ORDER BY table_name, column_name;
```