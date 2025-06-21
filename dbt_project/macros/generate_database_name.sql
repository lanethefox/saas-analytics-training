{% macro generate_database_name(custom_database_name=none, node=none) -%}

    {%- set default_database = target.database -%}
    
    {#- 
    For sources, if a custom database is specified in the source configuration,
    use that. Otherwise use the target database (saas_platform_dev).
    -#}
    
    {%- if custom_database_name is none -%}
        {{ default_database }}
    {%- else -%}
        {#- If custom database name contains 'analytics', replace it with 'dev' -#}
        {%- if 'analytics' in custom_database_name -%}
            {{ custom_database_name | replace('analytics_db', 'dev') }}
        {%- else -%}
            {{ custom_database_name | trim }}
        {%- endif -%}
    {%- endif -%}

{%- endmacro %}
