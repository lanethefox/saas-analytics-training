#!/usr/bin/env python3
"""
Enhanced Superset Setup - Part 2: Dashboard Creation Functions
"""

import json
from datetime import datetime

def create_customer_success_charts(client):
    """Create all charts for Customer Success dashboard"""
    print("\n📊 Creating Customer Success Charts...")
    charts = []
    
    # 1. Customer Health Distribution
    chart_id = client.create_chart({
        "slice_name": "Customer Health Distribution",
        "viz_type": "pie",
        "datasource_id": client.datasets.get("entity.entity_customers"),
        "datasource_type": "table",
        "params": {
            "viz_type": "pie",
            "groupby": ["customer_health_tier"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "account_id"},
                "aggregate": "COUNT_DISTINCT",
                "label": "Customer Count"
            },
            "color_scheme": "supersetColors",
            "show_labels": True,
            "labels_outside": True,
            "number_format": ",.0f",
            "show_legend": True,
            "legendType": "scroll",
            "legendOrientation": "right"
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 2. MRR by Customer Tier
    chart_id = client.create_chart({
        "slice_name": "MRR by Customer Tier",
        "viz_type": "bar",
        "datasource_id": client.datasets.get("entity.entity_customers"),
        "datasource_type": "table",
        "params": {
            "viz_type": "bar",
            "x_axis": "customer_health_tier",
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "monthly_recurring_revenue"},
                "aggregate": "SUM",
                "label": "Total MRR"
            }],
            "color_scheme": "googleCategory10c",
            "show_legend": False,
            "y_axis_format": "$,.0f",
            "show_value": True,
            "bar_stacked": False
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 3. Churn Risk Heatmap
    chart_id = client.create_chart({
        "slice_name": "Churn Risk by Segment",
        "viz_type": "heatmap",
        "datasource_id": client.datasets.get("entity.entity_customers"),
        "datasource_type": "table",
        "params": {
            "viz_type": "heatmap",
            "all_columns_x": ["industry"],
            "all_columns_y": ["customer_segment"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "churn_risk_score"},
                "aggregate": "AVG",
                "label": "Avg Churn Risk"
            },
            "linear_color_scheme": "red_yellow_blue",
            "xscale_interval": 1,
            "yscale_interval": 1,
            "canvas_image_rendering": "pixelated",
            "normalize_across": "heatmap",
            "value_format": ".1f"
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 4. Customer Health Trend
    chart_id = client.create_chart({
        "slice_name": "Customer Health Score Trend",
        "viz_type": "line",
        "datasource_id": client.datasets.get("entity.entity_customers_daily"),
        "datasource_type": "table",
        "params": {
            "viz_type": "line",
            "x_axis": "snapshot_date",
            "time_grain_sqla": "P1D",
            "metrics": [
                {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "avg_health_score"},
                    "aggregate": "AVG",
                    "label": "Avg Health Score"
                }
            ],
            "groupby": ["customer_health_tier"],
            "color_scheme": "bnbColors",
            "show_legend": True,
            "rich_tooltip": True,
            "y_axis_format": ".1f",
            "x_axis_time_format": "%Y-%m-%d"
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 5. Top At-Risk Customers Table
    chart_id = client.create_chart({
        "slice_name": "Top At-Risk Customers",
        "viz_type": "table",
        "datasource_id": client.datasets.get("entity.entity_customers"),
        "datasource_type": "table",
        "params": {
            "viz_type": "table",
            "query_mode": "aggregate",
            "groupby": ["company_name", "customer_health_tier", "primary_csm"],
            "metrics": [
                {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "monthly_recurring_revenue"},
                    "aggregate": "SUM",
                    "label": "MRR"
                },
                {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "churn_risk_score"},
                    "aggregate": "MAX",
                    "label": "Risk Score"
                }
            ],
            "row_limit": 20,
            "server_page_length": 20,
            "order_desc": True,
            "table_timestamp_format": "%Y-%m-%d",
            "page_length": 10,
            "include_search": True,
            "table_filter": True,
            "filters": [
                {
                    "col": "churn_risk_score",
                    "op": ">",
                    "val": 70
                }
            ]
        }
    })
    if chart_id: charts.append(chart_id)
    
    return charts

def create_sales_charts(client):
    """Create all charts for Sales dashboard"""
    print("\n📊 Creating Sales Charts...")
    charts = []
    
    # 1. Pipeline by Stage
    chart_id = client.create_chart({
        "slice_name": "Sales Pipeline by Stage",
        "viz_type": "funnel",
        "datasource_id": client.datasets.get("mart.mart_sales__pipeline"),
        "datasource_type": "table",
        "params": {
            "viz_type": "funnel",
            "groupby": ["pipeline_stage"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "opportunity_value"},
                "aggregate": "SUM",
                "label": "Pipeline Value"
            },
            "color_scheme": "bnbColors",
            "show_legend": False,
            "number_format": "$,.0f",
            "sort_by_metric": False
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 2. Win Rate by Product
    chart_id = client.create_chart({
        "slice_name": "Win Rate by Product",
        "viz_type": "bar",
        "datasource_id": client.datasets.get("mart.mart_sales__pipeline"),
        "datasource_type": "table",
        "params": {
            "viz_type": "bar",
            "x_axis": "product_category",
            "metrics": [{
                "expressionType": "SQL",
                "sqlExpression": "SUM(CASE WHEN deal_status = 'won' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)",
                "label": "Win Rate %"
            }],
            "color_scheme": "googleCategory10c",
            "show_legend": False,
            "y_axis_format": ".1f",
            "show_value": True,
            "order_bars": True
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 3. Sales Velocity Metrics
    chart_id = client.create_chart({
        "slice_name": "Sales Velocity Metrics",
        "viz_type": "big_number_total",
        "datasource_id": client.datasets.get("mart.mart_sales__pipeline"),
        "datasource_type": "table",
        "params": {
            "viz_type": "big_number_total",
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "days_in_pipeline"},
                "aggregate": "AVG",
                "label": "Avg Days to Close"
            },
            "subheader": "Sales Cycle Length",
            "y_axis_format": ".0f",
            "time_format": "%Y-%m-%d"
        }
    })
    if chart_id: charts.append(chart_id)
    
    return charts

def create_marketing_charts(client):
    """Create all charts for Marketing dashboard"""
    print("\n📊 Creating Marketing Charts...")
    charts = []
    
    # 1. Channel Performance
    chart_id = client.create_chart({
        "slice_name": "Marketing Channel Performance",
        "viz_type": "sunburst",
        "datasource_id": client.datasets.get("mart.mart_marketing__attribution"),
        "datasource_type": "table",
        "params": {
            "viz_type": "sunburst",
            "groupby": ["channel", "campaign_type"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "attributed_revenue"},
                "aggregate": "SUM",
                "label": "Attributed Revenue"
            },
            "color_scheme": "googleCategory20c",
            "linear_color_scheme": "blue_white_yellow",
            "secondary_metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "conversions"},
                "aggregate": "COUNT",
                "label": "Conversions"
            }
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 2. CAC by Channel
    chart_id = client.create_chart({
        "slice_name": "Customer Acquisition Cost by Channel",
        "viz_type": "bar",
        "datasource_id": client.datasets.get("mart.mart_marketing__attribution"),
        "datasource_type": "table",
        "params": {
            "viz_type": "bar",
            "x_axis": "channel",
            "metrics": [{
                "expressionType": "SQL",
                "sqlExpression": "SUM(spend) / NULLIF(COUNT(DISTINCT customer_id), 0)",
                "label": "CAC"
            }],
            "color_scheme": "bnbColors",
            "show_legend": False,
            "y_axis_format": "$,.0f",
            "show_value": True,
            "bar_stacked": False,
            "order_bars": True
        }
    })
    if chart_id: charts.append(chart_id)
    
    return charts

def create_product_charts(client):
    """Create all charts for Product dashboard"""
    print("\n📊 Creating Product Charts...")
    charts = []
    
    # 1. Feature Adoption Funnel
    chart_id = client.create_chart({
        "slice_name": "Feature Adoption Funnel",
        "viz_type": "funnel",
        "datasource_id": client.datasets.get("entity.entity_features"),
        "datasource_type": "table",
        "params": {
            "viz_type": "funnel",
            "groupby": ["adoption_stage"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "unique_users"},
                "aggregate": "SUM",
                "label": "Users"
            },
            "color_scheme": "purpleBlueWhite",
            "show_legend": False,
            "number_format": ",.0f"
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 2. User Engagement Distribution
    chart_id = client.create_chart({
        "slice_name": "User Engagement Distribution",
        "viz_type": "histogram",
        "datasource_id": client.datasets.get("entity.entity_users"),
        "datasource_type": "table",
        "params": {
            "viz_type": "histogram",
            "all_columns_x": ["engagement_score"],
            "row_limit": 10000,
            "bins": 20,
            "color_scheme": "bnbColors",
            "x_axis_label": "Engagement Score",
            "y_axis_label": "Number of Users",
            "normalize": False
        }
    })
    if chart_id: charts.append(chart_id)
    
    return charts

def create_operations_charts(client):
    """Create all charts for Operations dashboard"""
    print("\n📊 Creating Operations Charts...")
    charts = []
    
    # 1. Device Fleet Status
    chart_id = client.create_chart({
        "slice_name": "Device Fleet Status",
        "viz_type": "pie",
        "datasource_id": client.datasets.get("entity.entity_devices"),
        "datasource_type": "table",
        "params": {
            "viz_type": "pie",
            "groupby": ["device_status"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "device_id"},
                "aggregate": "COUNT_DISTINCT",
                "label": "Device Count"
            },
            "color_scheme": "googleCategory10c",
            "show_labels": True,
            "labels_outside": True,
            "number_format": ",.0f",
            "donut": True,
            "innerRadius": 30
        }
    })
    if chart_id: charts.append(chart_id)
    
    # 2. Device Performance Heatmap
    chart_id = client.create_chart({
        "slice_name": "Device Performance by Hour",
        "viz_type": "cal_heatmap",
        "datasource_id": client.datasets.get("entity.entity_devices_hourly"),
        "datasource_type": "table",
        "params": {
            "viz_type": "cal_heatmap",
            "time_grain_sqla": "PT1H",
            "metrics": [{
                "expressionType": "SIMPLE",
                "column": {"column_name": "avg_response_time"},
                "aggregate": "AVG",
                "label": "Avg Response Time"
            }],
            "linear_color_scheme": "green_white_red",
            "cell_size": 10,
            "cell_padding": 2,
            "cell_radius": 0,
            "steps": 10
        }
    })
    if chart_id: charts.append(chart_id)
    
    return charts