-- Test HubSpot staging models for CRM data integrity
WITH hubspot_validation AS (
    -- Check companies
    SELECT 
        'companies' AS entity_type,
        COUNT(*) AS total_records,
        SUM(CASE WHEN company_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN name IS NULL OR TRIM(name) = '' THEN 1 ELSE 0 END) AS missing_names,
        SUM(CASE WHEN createdate > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_dates
    FROM {{ ref('stg_hubspot__companies') }}
    
    UNION ALL
    
    -- Check contacts
    SELECT 
        'contacts' AS entity_type,
        COUNT(*) AS total_records,
        SUM(CASE WHEN contact_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN email IS NULL OR email NOT LIKE '%@%' THEN 1 ELSE 0 END) AS missing_names,
        SUM(CASE WHEN createdate > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_dates
    FROM {{ ref('stg_hubspot__contacts') }}
    
    UNION ALL
    
    -- Check deals
    SELECT 
        'deals' AS entity_type,
        COUNT(*) AS total_records,
        SUM(CASE WHEN deal_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
        SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END) AS missing_names,
        SUM(CASE WHEN createdate > CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS future_dates
    FROM {{ ref('stg_hubspot__deals') }}
),
deal_stage_validation AS (
    -- Validate deal stages
    SELECT 
        COUNT(*) AS invalid_stages
    FROM {{ ref('stg_hubspot__deals') }}
    WHERE dealstage NOT IN ('appointmentscheduled', 'qualifiedtobuy', 'presentationscheduled', 
                            'decisionmakerboughtin', 'contractsent', 'closedwon', 'closedlost')
),
hubspot_issues AS (
    SELECT 
        v.*,
        ds.invalid_stages
    FROM hubspot_validation v
    CROSS JOIN deal_stage_validation ds
    WHERE v.null_ids > 0
       OR v.missing_names > 0
       OR v.future_dates > 0
       OR ds.invalid_stages > 0
)
-- Test fails if HubSpot data has quality issues
SELECT * FROM hubspot_issues