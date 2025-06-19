DO $$
DECLARE
    r RECORD;
    sql_query TEXT;
BEGIN
    -- Create temp table to store results
    CREATE TEMP TABLE IF NOT EXISTS table_row_counts (
        fully_qualified_name TEXT,
        row_count BIGINT
    );
    
    -- Clear any existing data
    TRUNCATE table_row_counts;
    
    -- Loop through all tables
    FOR r IN 
        SELECT 
            schemaname,
            tablename,
            'saas_platform_dev.' || schemaname || '.' || tablename as fqn
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename
    LOOP
        -- Build and execute count query
        sql_query := format('INSERT INTO table_row_counts SELECT %L, COUNT(*) FROM %I.%I',
                           r.fqn, r.schemaname, r.tablename);
        EXECUTE sql_query;
    END LOOP;
END $$;

-- Display results
SELECT * FROM table_row_counts
ORDER BY 
    CASE 
        WHEN fully_qualified_name LIKE '%.raw.%' THEN 1
        WHEN fully_qualified_name LIKE '%.staging.%' THEN 2
        WHEN fully_qualified_name LIKE '%.intermediate.%' THEN 3
        WHEN fully_qualified_name LIKE '%.entity.%' THEN 4
        WHEN fully_qualified_name LIKE '%.mart.%' THEN 5
        ELSE 6
    END,
    fully_qualified_name;