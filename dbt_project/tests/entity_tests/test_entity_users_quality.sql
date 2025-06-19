-- Test: Entity Users Engagement and Role Validation
-- Ensures user engagement scores and role assignments are consistent

select 
    user_id,
    user_key,
    account_id,
    email,
    role_type_standardized,
    engagement_score,
    features_adopted,
    total_sessions_30d,
    feature_interactions_30d
from {{ ref('entity_users') }}
where 
    -- Engagement score validation
    engagement_score < 0 
    or engagement_score > 1
    
    -- Feature adoption validation
    or features_adopted < 0
    or features_adopted > 50  -- Reasonable upper bound
    
    -- Session validation
    or total_sessions_30d < 0
    or total_sessions_30d > 1000  -- Reasonable upper bound
    
    -- Feature interaction validation
    or feature_interactions_30d < 0
    or feature_interactions_30d < features_adopted  -- Should have at least one interaction per adopted feature
    
    -- Required field validation
    or user_key is null
    or account_id is null
    or email is null
    or role_type_standardized is null
    
    -- Email format validation (basic check)
    or email not like '%@%'
    
    -- Role type validation
    or role_type_standardized not in ('admin', 'standard_user', 'viewer', 'manager')
    
    -- Logical consistency checks
    or (user_status = 'active' and last_active_date < current_date - 60)  -- Active users should have recent activity
    or (engagement_score > 0.8 and total_sessions_30d = 0)  -- High engagement should correlate with sessions
