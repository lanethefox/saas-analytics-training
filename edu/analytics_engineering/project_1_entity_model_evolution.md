# Project 1: Entity Model Evolution - Teams Feature Implementation

## Project Overview

TapFlow Analytics is launching a new "Teams" feature that allows customers to organize users into teams for better collaboration and permissions management. As the Analytics Engineer, you'll design and implement the complete entity model, including incremental processing, historical tracking, and multiple grain tables.

**Duration**: 3 weeks  
**Complexity**: Advanced  
**Prerequisites**: Entity modeling experience, dbt proficiency, SQL optimization

## Business Context

### Current State
- Customers have multiple users with individual permissions
- No ability to group users for reporting or access control
- Increasing demand for team-based analytics
- 40% of enterprise customers requesting this feature

### Desired State
- Users can belong to one or more teams
- Teams have hierarchical structure (teams within teams)
- Team-based usage analytics and permissions
- Historical tracking of team membership changes

## Technical Requirements

### 1. Entity Model Design

Create the complete Teams entity following ECM principles:

```sql
-- entity_teams (Atomic table)
CREATE TABLE entity.entity_teams (
    team_id VARCHAR PRIMARY KEY,
    team_name VARCHAR NOT NULL,
    customer_id VARCHAR NOT NULL,
    parent_team_id VARCHAR,
    team_type VARCHAR, -- 'department', 'project', 'location', 'custom'
    
    -- Metadata
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by_user_id VARCHAR,
    is_active BOOLEAN,
    
    -- Computed Metrics
    total_members INTEGER,
    active_members INTEGER,
    direct_members INTEGER, -- Excluding sub-teams
    total_subteams INTEGER,
    hierarchy_depth INTEGER,
    
    -- Activity Metrics
    last_activity_at TIMESTAMP,
    total_actions_30d INTEGER,
    active_days_30d INTEGER,
    collaboration_score DECIMAL(3,2), -- 0-100
    
    -- Resource Metrics
    total_devices_accessible INTEGER,
    total_locations_accessible INTEGER,
    storage_used_gb DECIMAL(10,2),
    api_calls_30d INTEGER,
    
    -- Health Metrics
    team_health_score DECIMAL(3,2), -- 0-100
    engagement_score DECIMAL(3,2),
    adoption_score DECIMAL(3,2),
    
    -- Snapshot metadata
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE
);

-- entity_teams_history (SCD Type 2)
CREATE TABLE entity.entity_teams_history (
    surrogate_key VARCHAR PRIMARY KEY, -- team_id || valid_from
    team_id VARCHAR NOT NULL,
    -- All columns from entity_teams
    -- ...
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    is_current BOOLEAN DEFAULT FALSE,
    change_reason VARCHAR
);

-- entity_teams_daily (Time-series grain)
CREATE TABLE entity.entity_teams_daily (
    team_id VARCHAR,
    date DATE,
    
    -- Membership Metrics
    total_members INTEGER,
    members_added INTEGER,
    members_removed INTEGER,
    member_churn_rate DECIMAL(5,4),
    
    -- Activity Metrics
    active_members INTEGER,
    total_actions INTEGER,
    avg_actions_per_member DECIMAL(10,2),
    unique_features_used INTEGER,
    
    -- Collaboration Metrics
    internal_messages INTEGER,
    shared_reports INTEGER,
    cross_team_interactions INTEGER,
    
    -- Performance
    avg_query_time_ms INTEGER,
    total_queries INTEGER,
    api_calls INTEGER,
    
    PRIMARY KEY (team_id, date)
);
```

### 2. Incremental Processing Implementation

Convert the entity model to use incremental processing:

```sql
-- models/entity/teams/entity_teams.sql
{{
    config(
        materialized='incremental',
        unique_key='team_id',
        on_schema_change='fail',
        incremental_strategy='merge',
        merge_exclude_columns=['created_at'],
        tags=['entity', 'teams', 'tier_1']
    )
}}

WITH teams_base AS (
    SELECT * FROM {{ ref('int_teams__enriched') }}
    {% if is_incremental() %}
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
       OR team_id IN (
           -- Include teams with membership changes
           SELECT DISTINCT team_id 
           FROM {{ ref('stg_app__team_members') }}
           WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
       )
    {% endif %}
),

member_metrics AS (
    SELECT 
        team_id,
        COUNT(DISTINCT user_id) as total_members,
        COUNT(DISTINCT CASE WHEN is_active THEN user_id END) as active_members,
        COUNT(DISTINCT CASE WHEN is_direct_member THEN user_id END) as direct_members
    FROM {{ ref('int_teams__members_current') }}
    GROUP BY team_id
),

activity_metrics AS (
    SELECT
        team_id,
        MAX(activity_timestamp) as last_activity_at,
        COUNT(DISTINCT activity_id) as total_actions_30d,
        COUNT(DISTINCT DATE(activity_timestamp)) as active_days_30d
    FROM {{ ref('int_teams__activity') }}
    WHERE activity_timestamp >= CURRENT_DATE - 30
    GROUP BY team_id
)

-- Main SELECT combining all metrics
SELECT 
    t.*,
    m.total_members,
    m.active_members,
    m.direct_members,
    a.last_activity_at,
    a.total_actions_30d,
    a.active_days_30d,
    -- Calculate derived metrics
    CASE 
        WHEN m.total_members > 0 
        THEN (a.active_days_30d::DECIMAL / 30 * 100)::DECIMAL(3,2)
        ELSE 0 
    END as engagement_score,
    CURRENT_TIMESTAMP as updated_at
FROM teams_base t
LEFT JOIN member_metrics m ON t.team_id = m.team_id
LEFT JOIN activity_metrics a ON t.team_id = a.team_id
```

### 3. History Tracking Implementation

Implement SCD Type 2 history tracking:

```sql
-- models/entity/teams/entity_teams_history.sql
{{
    config(
        materialized='incremental',
        unique_key='surrogate_key',
        incremental_strategy='append'
    )
}}

WITH current_records AS (
    SELECT 
        *,
        MD5(
            COALESCE(team_name, '') || '|' ||
            COALESCE(parent_team_id, '') || '|' ||
            COALESCE(team_type, '') || '|' ||
            COALESCE(is_active::TEXT, '') || '|' ||
            COALESCE(total_members::TEXT, '') || '|' ||
            -- Include all Type 2 tracked fields
            COALESCE(team_health_score::TEXT, '')
        ) as record_hash
    FROM {{ ref('entity_teams') }}
),

{% if is_incremental() %}
previous_records AS (
    SELECT * FROM {{ this }}
    WHERE is_current = TRUE
),

changes_detected AS (
    SELECT 
        c.team_id,
        c.record_hash != p.record_hash as has_changed,
        p.valid_from as previous_valid_from
    FROM current_records c
    LEFT JOIN previous_records p ON c.team_id = p.team_id
)
{% endif %}

SELECT 
    team_id || '_' || TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDDHH24MISS') as surrogate_key,
    *,
    CURRENT_TIMESTAMP as valid_from,
    NULL::TIMESTAMP as valid_to,
    TRUE as is_current,
    'Incremental Load' as change_reason
FROM current_records

{% if is_incremental() %}
WHERE team_id IN (
    SELECT team_id FROM changes_detected WHERE has_changed = TRUE
)

UNION ALL

-- Close out previous records
SELECT 
    surrogate_key,
    team_id,
    -- ... all other columns
    valid_from,
    CURRENT_TIMESTAMP as valid_to,
    FALSE as is_current,
    'Record Updated' as change_reason
FROM previous_records
WHERE team_id IN (
    SELECT team_id FROM changes_detected WHERE has_changed = TRUE
)
{% endif %}
```

### 4. Grain Table Development

Create multiple grain tables for different reporting needs:

```sql
-- models/entity/teams/entity_teams_hourly.sql (Real-time dashboards)
{{
    config(
        materialized='incremental',
        unique_key=['team_id', 'hour'],
        partition_by={
            'field': 'hour',
            'data_type': 'timestamp',
            'granularity': 'day'
        },
        cluster_by=['team_id']
    )
}}

WITH hourly_activity AS (
    SELECT 
        team_id,
        DATE_TRUNC('hour', activity_timestamp) as hour,
        COUNT(DISTINCT user_id) as active_users,
        COUNT(DISTINCT session_id) as sessions,
        COUNT(*) as total_actions,
        AVG(response_time_ms) as avg_response_time
    FROM {{ ref('fct_team_activity') }}
    {% if is_incremental() %}
    WHERE activity_timestamp >= DATE_TRUNC('hour', CURRENT_TIMESTAMP - INTERVAL '3 hours')
    {% endif %}
    GROUP BY 1, 2
)

SELECT * FROM hourly_activity

-- models/entity/teams/entity_teams_weekly.sql (Executive reporting)
{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['week_start'], 'type': 'btree'},
            {'columns': ['team_id', 'week_start'], 'unique': True}
        ]
    )
}}

WITH weekly_aggregations AS (
    SELECT 
        team_id,
        DATE_TRUNC('week', date) as week_start,
        -- Growth metrics
        FIRST_VALUE(total_members) OVER w as members_week_start,
        LAST_VALUE(total_members) OVER w as members_week_end,
        -- Activity metrics
        SUM(total_actions) as total_actions,
        AVG(active_members) as avg_active_members,
        -- Collaboration
        SUM(internal_messages) as total_messages,
        SUM(shared_reports) as total_shares
    FROM {{ ref('entity_teams_daily') }}
    WINDOW w AS (
        PARTITION BY team_id, DATE_TRUNC('week', date) 
        ORDER BY date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
)

SELECT 
    *,
    members_week_end - members_week_start as member_growth,
    CASE 
        WHEN members_week_start > 0 
        THEN ((members_week_end - members_week_start)::DECIMAL / members_week_start * 100)
        ELSE 0 
    END as growth_rate_percent
FROM weekly_aggregations
```

### 5. Testing Strategy

Implement comprehensive tests:

```yaml
# models/entity/teams/schema.yml
version: 2

models:
  - name: entity_teams
    description: Current state of all teams with calculated metrics
    columns:
      - name: team_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('entity_customers')
              field: customer_id
      - name: hierarchy_depth
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 5  # Business rule: max 5 levels
      - name: team_health_score
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 100
              
    tests:
      # Ensure incremental logic works
      - dbt_utils.recency:
          datepart: hour
          field: updated_at
          threshold: 2
          
      # No orphaned teams
      - dbt_expectations.expect_compound_columns_to_be_unique:
          column_list: ['team_id', 'valid_from']
          
  - name: entity_teams_history
    tests:
      # Ensure no gaps in history
      - assert_no_gaps_in_history:
          team_id: team_id
          valid_from: valid_from
          valid_to: valid_to
          
  - name: entity_teams_daily
    tests:
      # Ensure complete daily coverage
      - assert_continuous_dates:
          date_column: date
          group_by: team_id
```

## Deliverables

### Week 1: Design & Implementation
- [ ] Complete entity model design document
- [ ] Implement atomic table with all metrics
- [ ] Create staging and intermediate models
- [ ] Write initial test suite

### Week 2: Incremental & History
- [ ] Convert to incremental processing
- [ ] Implement SCD Type 2 history
- [ ] Add late-arriving data handling
- [ ] Performance testing and optimization

### Week 3: Grains & Deployment
- [ ] Create hourly, daily, weekly grains
- [ ] Build monthly grain with backfill
- [ ] Documentation and knowledge transfer
- [ ] Production deployment plan

## Success Criteria

1. **Performance**
   - Incremental runs < 5 minutes
   - Full refresh < 30 minutes
   - Query response < 2 seconds

2. **Data Quality**
   - 100% test coverage
   - Zero data quality alerts in first week
   - Metric variance < 0.1% vs. source

3. **Business Impact**
   - Teams feature launches on schedule
   - Self-service analytics enabled day 1
   - 80% of queries use entity model

## Learning Resources

- [dbt Incremental Models](https://docs.getdbt.com/docs/build/incremental-models)
- [Slowly Changing Dimensions](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/)
- [Entity-Centric Modeling](/docs/entity_tables_documentation.md)
- [Performance Tuning Guide](/docs/performance_optimization.md)

## Instructor Notes

See [Instructor Guide](../instructor_guides/analytics_engineering_project_1_instructor_guide.md) for:
- Common pitfalls and solutions
- Grading rubric
- Extension challenges
- Discussion topics