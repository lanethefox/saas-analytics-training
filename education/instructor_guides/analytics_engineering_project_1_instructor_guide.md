# Instructor Guide: Entity Model Evolution Project

## Project Overview

This project challenges students to build a complete entity model from scratch, implementing advanced analytics engineering concepts including incremental processing, SCD Type 2 history, and multiple grain tables.

## Learning Objectives Assessment

### 1. Entity Model Design (25%)
- **Excellent**: Comprehensive metrics, clear relationships, follows ECM principles
- **Good**: Most metrics included, minor relationship issues
- **Needs Improvement**: Missing key metrics, unclear relationships

**Common Issues**:
- Forgetting to include hierarchy calculations
- Not handling NULL parent_team_id for root teams
- Missing bi-temporal modeling considerations

### 2. Incremental Implementation (25%)
- **Excellent**: Handles all edge cases, optimized performance, clear logic
- **Good**: Basic incremental works, some edge cases missed
- **Needs Improvement**: Incremental logic errors, poor performance

**Key Evaluation Points**:
```sql
-- Check for proper late-arriving data handling
{% if is_incremental() %}
WHERE updated_at > (SELECT MAX(updated_at) - INTERVAL '1 hour' FROM {{ this }})
{% endif %}
```

### 3. History Tracking (25%)
- **Excellent**: No gaps, proper record closure, efficient querying
- **Good**: Basic SCD2 works, minor gaps possible
- **Needs Improvement**: Gaps in history, incorrect record handling

**Test Query**:
```sql
-- Verify no gaps in history
WITH history_check AS (
    SELECT 
        team_id,
        valid_from,
        valid_to,
        LEAD(valid_from) OVER (PARTITION BY team_id ORDER BY valid_from) as next_valid_from
    FROM entity_teams_history
)
SELECT * FROM history_check
WHERE valid_to IS NOT NULL 
  AND valid_to != next_valid_from;
```

### 4. Grain Development (25%)
- **Excellent**: Multiple grains, appropriate partitioning, optimized
- **Good**: Basic grains work, some optimization needed
- **Needs Improvement**: Performance issues, incorrect aggregations

## Common Pitfalls & Solutions

### 1. Incremental Performance Issues

**Problem**: Students often forget to index the update timestamp
```sql
-- Solution: Add index hint in dbt
{{ config(
    indexes=[
        {'columns': ['updated_at'], 'type': 'btree'},
        {'columns': ['team_id', 'updated_at'], 'type': 'btree'}
    ]
) }}
```

### 2. History Table Gaps

**Problem**: Not handling simultaneous updates correctly
```sql
-- Solution: Use transaction timestamp
WITH updates AS (
    SELECT 
        *,
        CURRENT_TIMESTAMP as update_timestamp
    FROM source_data
)
```

### 3. Circular Dependencies

**Problem**: Team hierarchies creating circular references
```sql
-- Solution: Recursive CTE with cycle detection
WITH RECURSIVE team_hierarchy AS (
    -- Base case
    SELECT team_id, parent_team_id, 0 as level, 
           ARRAY[team_id] as path,
           FALSE as is_cycle
    FROM teams
    WHERE parent_team_id IS NULL
    
    UNION ALL
    
    -- Recursive case with cycle detection
    SELECT t.team_id, t.parent_team_id, h.level + 1,
           h.path || t.team_id,
           t.team_id = ANY(h.path) as is_cycle
    FROM teams t
    JOIN team_hierarchy h ON t.parent_team_id = h.team_id
    WHERE NOT h.is_cycle
)
```

## Stakeholder Simulation Scripts

### 1. Initial Requirements Meeting
**You (as Product Manager)**: "We're launching Teams in Q4. Here's what we need:
- Users can create teams and sub-teams
- Track team performance and collaboration
- Historical reporting for compliance
- Real-time dashboards for team leads"

**Expected Student Questions**:
- "What's the maximum hierarchy depth?" → "Let's limit to 5 levels"
- "Can users belong to multiple teams?" → "Yes, with one primary team"
- "How far back do we need history?" → "2 years for compliance"

### 2. Mid-Project Change Request
**You (as Sales Director)**: "Great progress! We just closed a deal that requires:
- Team-based billing metrics
- API usage tracking by team
- Hourly granularity for real-time monitoring"

**Guidance**: This tests their ability to adapt the model without breaking existing work.

### 3. Performance Review
**You (as Data Platform Lead)**: "The model looks good, but I'm concerned about:
- Daily refresh takes 45 minutes
- History table is growing rapidly
- Analysts complain about query performance"

**Expected Solutions**:
- Implement proper incremental strategies
- Add partitioning to history table
- Create materialized views for common queries

## Extension Challenges

For advanced students who finish early:

### 1. Cross-Entity Metrics
"Add team-based device utilization metrics that require joining with entity_devices"

### 2. Dynamic Grain Generation
"Create a macro that generates grain tables dynamically based on configuration"

### 3. Real-time Streaming
"Design how this model would work with streaming data from Kafka"

## Discussion Topics

### 1. Design Decisions (15 min)
- Why separate atomic, history, and grain tables?
- When would you denormalize vs. normalize?
- How do you balance query performance vs. storage?

### 2. Incremental Strategies (15 min)
- Compare merge vs. delete+insert
- Discuss late-arriving data strategies
- When to force a full refresh?

### 3. Testing Philosophy (15 min)
- What constitutes "enough" test coverage?
- How do you test incremental logic?
- Balancing test runtime vs. coverage

## Grading Rubric

| Component | Weight | Excellent (90-100%) | Good (70-89%) | Needs Improvement (<70%) |
|-----------|--------|-------------------|--------------|------------------------|
| Entity Design | 25% | Complete metrics, clear documentation, extensible | Most requirements met, minor issues | Missing key requirements |
| Incremental Logic | 25% | Handles all cases, optimized, well-tested | Basic implementation works | Logic errors or poor performance |
| History Tracking | 25% | No gaps, efficient, properly tested | Minor issues, mostly complete | Gaps or incorrect implementation |
| Grain Tables | 15% | Multiple grains, optimized, documented | Basic grains implemented | Performance or logic issues |
| Code Quality | 10% | Clean, documented, follows standards | Readable, some documentation | Difficult to understand |

## Sample Solution Structure

```
models/entity/teams/
├── _teams__models.yml           # Documentation
├── entity_teams.sql             # Atomic table
├── entity_teams_history.sql     # SCD Type 2
├── entity_teams_daily.sql       # Daily grain
├── entity_teams_weekly.sql      # Weekly grain
├── entity_teams_monthly.sql     # Monthly grain
└── tests/
    ├── assert_teams_hierarchy_valid.sql
    ├── assert_no_history_gaps.sql
    └── assert_grain_completeness.sql
```

## Time Management Guide

- **Week 1**: Focus on getting atomic model correct first
- **Week 2**: Incremental can be tricky - allocate extra time
- **Week 3**: Grains are straightforward if base model is solid

## Resources for Students

1. [Incremental Models Best Practices](https://discourse.getdbt.com/t/incremental-models-best-practices/3580)
2. [The Data Warehouse Toolkit](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/)
3. Internal: [Entity Model Template](/templates/entity_model_template.sql)
4. Internal: [Performance Tuning Checklist](/docs/performance_checklist.md)

## Post-Project Reflection

Lead a discussion on:
1. What was harder than expected?
2. What would you do differently?
3. How would this scale to 1000+ teams?
4. What monitoring would you add?

Remember: The goal is not just to build a working model, but to understand the trade-offs and decisions that go into production analytics engineering.