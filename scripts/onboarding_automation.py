#!/usr/bin/env python3
"""
Automated Onboarding Checklist for Data Platform
This script automates the onboarding process for new data analysts
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import requests
import psycopg2
from psycopg2 import sql

class OnboardingAutomation:
    def __init__(self, analyst_name: str, team: str):
        self.analyst_name = analyst_name
        self.team = team.lower()
        self.start_time = datetime.now()
        self.checklist = []
        self.results = {}
        
        # Configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'saas_platform_dev',
            'user': 'saas_user',
            'password': 'saas_secure_password_2024'
        }
        
        self.services = {
            'superset': {'url': 'http://localhost:8088', 'creds': 'admin/admin_password_2024'},
            'airflow': {'url': 'http://localhost:8080', 'creds': 'admin/admin_password_2024'},
            'jupyter': {'url': 'http://localhost:8888', 'creds': 'token: saas_ml_token_2024'},
            'mlflow': {'url': 'http://localhost:5001', 'creds': 'No auth required'},
            'dbt_docs': {'url': 'http://localhost:8085', 'creds': 'No auth required'},
            'grafana': {'url': 'http://localhost:3000', 'creds': 'admin/grafana_admin_2024'}
        }

    def run_checklist(self):
        """Execute the complete onboarding checklist"""
        print(f"\n🚀 Starting Automated Onboarding for {self.analyst_name} ({self.team} team)")
        print("=" * 60)
        
        # Run all checks
        self.check_database_access()
        self.verify_services()
        self.create_user_workspace()
        self.run_sample_queries()
        self.generate_credentials_file()
        self.create_personal_dashboard()
        self.setup_git_access()
        self.send_welcome_message()
        
        # Generate report
        self.generate_onboarding_report()
        
        print(f"\n✅ Onboarding completed in {(datetime.now() - self.start_time).seconds} seconds!")

    def check_database_access(self):
        """Verify database connectivity"""
        print("\n📊 Checking Database Access...")
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Test basic query
            cur.execute("SELECT COUNT(*) FROM entity.entity_customers WHERE is_active = true")
            count = cur.fetchone()[0]
            
            self.results['database_access'] = {
                'status': 'success',
                'message': f'Connected successfully. Found {count} active customers.'
            }
            print(f"  ✅ Database connection successful")
            
            # Check team-specific tables
            team_tables = {
                'sales': 'metrics.sales',
                'customer-experience': 'metrics.customer_success',
                'marketing': 'metrics.marketing',
                'product': 'metrics.product_analytics'
            }
            
            if self.team in team_tables:
                cur.execute(f"SELECT COUNT(*) FROM {team_tables[self.team]} LIMIT 1")
                print(f"  ✅ Access to {team_tables[self.team]} verified")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            self.results['database_access'] = {
                'status': 'failed',
                'message': str(e)
            }
            print(f"  ❌ Database connection failed: {e}")

    def verify_services(self):
        """Check all platform services"""
        print("\n🔧 Verifying Platform Services...")
        
        for service_name, config in self.services.items():
            try:
                response = requests.get(config['url'], timeout=5)
                if response.status_code < 400:
                    self.results[f'service_{service_name}'] = 'available'
                    print(f"  ✅ {service_name.capitalize()}: {config['url']} ({config['creds']})")
                else:
                    self.results[f'service_{service_name}'] = 'error'
                    print(f"  ⚠️  {service_name.capitalize()}: HTTP {response.status_code}")
            except:
                self.results[f'service_{service_name}'] = 'unreachable'
                print(f"  ❌ {service_name.capitalize()}: Unreachable")

    def create_user_workspace(self):
        """Create personal workspace directories"""
        print("\n📁 Creating User Workspace...")
        
        workspace_dirs = [
            f"workspaces/{self.analyst_name}/queries",
            f"workspaces/{self.analyst_name}/dashboards",
            f"workspaces/{self.analyst_name}/notebooks",
            f"workspaces/{self.analyst_name}/reports"
        ]
        
        for dir_path in workspace_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"  ✅ Created: {dir_path}")
            except Exception as e:
                print(f"  ❌ Failed to create {dir_path}: {e}")

    def run_sample_queries(self):
        """Execute team-specific sample queries"""
        print(f"\n🔍 Running {self.team.title()} Team Sample Queries...")
        
        sample_queries = {
            'sales': """
                SELECT 
                    DATE_TRUNC('month', metric_date) as month,
                    SUM(total_deals) as deals,
                    SUM(pipeline_value) as pipeline,
                    AVG(win_rate) as win_rate
                FROM metrics.sales
                WHERE metric_date >= CURRENT_DATE - INTERVAL '3 months'
                GROUP BY month
                ORDER BY month DESC
            """,
            'customer-experience': """
                SELECT 
                    metric_date,
                    avg_health_score,
                    avg_churn_risk,
                    active_customers,
                    total_mrr
                FROM metrics.customer_success
                ORDER BY metric_date DESC
                LIMIT 7
            """,
            'marketing': """
                SELECT 
                    channel,
                    SUM(spend) as total_spend,
                    SUM(conversions) as total_conversions,
                    AVG(roi) as avg_roi
                FROM metrics.marketing
                WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY channel
            """,
            'product': """
                SELECT 
                    metric_date,
                    daily_active_users,
                    monthly_active_users,
                    dau_mau_ratio,
                    avg_engagement_score
                FROM metrics.product_analytics
                ORDER BY metric_date DESC
                LIMIT 7
            """
        }
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            if self.team in sample_queries:
                cur.execute(sample_queries[self.team])
                results = cur.fetchall()
                print(f"  ✅ Sample query executed successfully ({len(results)} rows)")
                
                # Save results
                with open(f'workspaces/{self.analyst_name}/queries/sample_{self.team}_query.sql', 'w') as f:
                    f.write(sample_queries[self.team])
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")

    def generate_credentials_file(self):
        """Generate credentials reference file"""
        print("\n🔐 Generating Credentials File...")
        
        creds_content = f"""# Data Platform Credentials for {self.analyst_name}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
# Team: {self.team.title()}

## Database Access
Host: localhost
Port: 5432
Database: saas_platform_dev
Username: saas_user
Password: saas_secure_password_2024

## Connection String
postgresql://saas_user:saas_secure_password_2024@localhost:5432/saas_platform_dev

## Service Credentials
"""
        
        for service, config in self.services.items():
            creds_content += f"\n### {service.title()}\n"
            creds_content += f"URL: {config['url']}\n"
            creds_content += f"Credentials: {config['creds']}\n"
        
        creds_content += f"""
## Team-Specific Resources
Primary Table: {self._get_team_table()}
Documentation: docs/onboarding/{self.team}/README.md
Quarterly Goals: docs/onboarding/{self.team}/quarterly-goals.md

## SQL Snippet
```sql
-- Your first query
SELECT *
FROM {self._get_team_table()}
WHERE metric_date = CURRENT_DATE
LIMIT 10;
```

## Support
Slack: #data-platform
Wiki: Internal documentation
Office Hours: Tuesdays & Thursdays 2-3 PM
"""
        
        try:
            with open(f'workspaces/{self.analyst_name}/credentials.md', 'w') as f:
                f.write(creds_content)
            print(f"  ✅ Credentials file created")
        except Exception as e:
            print(f"  ❌ Failed to create credentials file: {e}")

    def _get_team_table(self):
        """Get primary table for team"""
        team_tables = {
            'sales': 'metrics.sales',
            'customer-experience': 'metrics.customer_success',
            'marketing': 'metrics.marketing',
            'product': 'metrics.product_analytics'
        }
        return team_tables.get(self.team, 'entity.entity_customers')

    def create_personal_dashboard(self):
        """Create starter dashboard configuration"""
        print("\n📊 Creating Personal Dashboard Template...")
        
        dashboard_config = {
            'name': f'{self.analyst_name}_{self.team}_dashboard',
            'created': datetime.now().isoformat(),
            'team': self.team,
            'charts': self._get_team_charts(),
            'filters': ['date_range', 'customer_tier', 'is_active'],
            'refresh_schedule': 'daily'
        }
        
        try:
            with open(f'workspaces/{self.analyst_name}/dashboards/starter_dashboard.json', 'w') as f:
                json.dump(dashboard_config, f, indent=2)
            print(f"  ✅ Dashboard template created")
        except Exception as e:
            print(f"  ❌ Failed to create dashboard template: {e}")

    def _get_team_charts(self):
        """Get team-specific chart configurations"""
        team_charts = {
            'sales': [
                {'type': 'line', 'metric': 'pipeline_value', 'title': 'Pipeline Trend'},
                {'type': 'bar', 'metric': 'win_rate', 'title': 'Win Rate by Month'},
                {'type': 'table', 'metric': 'top_deals', 'title': 'Top Opportunities'}
            ],
            'customer-experience': [
                {'type': 'gauge', 'metric': 'avg_health_score', 'title': 'Avg Health Score'},
                {'type': 'line', 'metric': 'churn_risk_trend', 'title': 'Churn Risk Trend'},
                {'type': 'heatmap', 'metric': 'health_by_tier', 'title': 'Health by Tier'}
            ],
            'marketing': [
                {'type': 'pie', 'metric': 'spend_by_channel', 'title': 'Spend Distribution'},
                {'type': 'line', 'metric': 'roi_trend', 'title': 'ROI Trend'},
                {'type': 'funnel', 'metric': 'conversion_funnel', 'title': 'Lead Funnel'}
            ],
            'product': [
                {'type': 'line', 'metric': 'dau_mau', 'title': 'DAU/MAU Trend'},
                {'type': 'bar', 'metric': 'feature_adoption', 'title': 'Feature Adoption'},
                {'type': 'scatter', 'metric': 'engagement_retention', 'title': 'Engagement vs Retention'}
            ]
        }
        return team_charts.get(self.team, [])

    def setup_git_access(self):
        """Create git configuration"""
        print("\n🔧 Setting Up Git Access...")
        
        gitignore_content = """# Personal workspace
*.csv
*.xlsx
.DS_Store
.env
credentials.md
__pycache__/
*.pyc
.ipynb_checkpoints/
"""
        
        try:
            with open(f'workspaces/{self.analyst_name}/.gitignore', 'w') as f:
                f.write(gitignore_content)
            print(f"  ✅ Git configuration created")
        except Exception as e:
            print(f"  ❌ Failed to create git config: {e}")

    def send_welcome_message(self):
        """Generate welcome message with next steps"""
        print("\n📧 Generating Welcome Message...")
        
        welcome_msg = f"""
Welcome to the Data Platform, {self.analyst_name}!

You've been successfully onboarded to the {self.team.title()} team.

Your workspace has been created at: workspaces/{self.analyst_name}/

Next steps:
1. Review your team documentation: docs/onboarding/{self.team}/README.md
2. Complete the SQL tutorial: docs/onboarding/common/interactive-sql-tutorial.md
3. Access Superset and create your first visualization
4. Join #data-platform and #{self.team}-analytics on Slack
5. Schedule 1:1 with your team lead

Your credentials are saved in: workspaces/{self.analyst_name}/credentials.md

Happy analyzing! 🚀
"""
        
        try:
            with open(f'workspaces/{self.analyst_name}/WELCOME.md', 'w') as f:
                f.write(welcome_msg)
            print(f"  ✅ Welcome message created")
        except Exception as e:
            print(f"  ❌ Failed to create welcome message: {e}")

    def generate_onboarding_report(self):
        """Generate comprehensive onboarding report"""
        print("\n📋 Generating Onboarding Report...")
        
        report = {
            'analyst': self.analyst_name,
            'team': self.team,
            'onboarding_date': self.start_time.isoformat(),
            'duration_seconds': (datetime.now() - self.start_time).seconds,
            'checks_performed': self.results,
            'workspace_created': True,
            'next_steps': [
                'Complete SQL tutorial',
                'Create first dashboard',
                'Run team-specific queries',
                'Join Slack channels',
                'Meet with team lead'
            ]
        }
        
        try:
            with open(f'workspaces/{self.analyst_name}/onboarding_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            print(f"  ✅ Onboarding report saved")
        except Exception as e:
            print(f"  ❌ Failed to save report: {e}")

def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python onboarding_automation.py <analyst_name> <team>")
        print("Teams: sales, customer-experience, marketing, product")
        sys.exit(1)
    
    analyst_name = sys.argv[1].lower().replace(' ', '_')
    team = sys.argv[2].lower()
    
    valid_teams = ['sales', 'customer-experience', 'marketing', 'product']
    if team not in valid_teams:
        print(f"Invalid team. Choose from: {', '.join(valid_teams)}")
        sys.exit(1)
    
    # Run onboarding
    automation = OnboardingAutomation(analyst_name, team)
    automation.run_checklist()

if __name__ == "__main__":
    main()