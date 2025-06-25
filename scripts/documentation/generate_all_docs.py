#!/usr/bin/env python3
"""
Master documentation generator that orchestrates all documentation and educational content generation.
This ensures all documentation stays synchronized with the actual platform state.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class MasterDocumentationGenerator:
    def __init__(self):
        self.timestamp = datetime.now()
        self.scripts_dir = Path(__file__).parent
        self.project_root = self.scripts_dir.parent.parent
        self.log_file = self.project_root / 'docs' / 'generation_log.json'
        
    def generate_all(self):
        """Generate all documentation and educational content"""
        print("=" * 80)
        print("TapFlow Analytics - Master Documentation Generation")
        print(f"Started: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        results = {
            'timestamp': self.timestamp.isoformat(),
            'generators': {}
        }
        
        # Run all generators
        generators = [
            {
                'name': 'Data Catalog',
                'script': 'generate_data_catalog.py',
                'description': 'Database schema and table documentation'
            },
            {
                'name': 'Metrics Catalog',
                'script': 'generate_metrics_catalog.py',
                'description': 'Business metrics and KPI documentation'
            },
            {
                'name': 'Educational Content',
                'script': 'generate_education_content.py',
                'description': 'Onboarding guides and training materials'
            }
        ]
        
        for generator in generators:
            print(f"\n{'='*60}")
            print(f"Running {generator['name']} Generator")
            print(f"Description: {generator['description']}")
            print(f"{'='*60}")
            
            start_time = datetime.now()
            success = self.run_generator(generator['script'])
            end_time = datetime.now()
            
            results['generators'][generator['name']] = {
                'script': generator['script'],
                'success': success,
                'duration': (end_time - start_time).total_seconds(),
                'timestamp': start_time.isoformat()
            }
            
            if success:
                print(f"✅ {generator['name']} completed successfully")
            else:
                print(f"❌ {generator['name']} failed")
        
        # Generate index and summary
        self.generate_documentation_index()
        
        # Save generation log
        self.save_generation_log(results)
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def run_generator(self, script_name):
        """Run a specific generator script"""
        script_path = self.scripts_dir / script_name
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print(f"Errors: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error running {script_name}: {e}")
            return False
    
    def generate_documentation_index(self):
        """Generate master index for all documentation"""
        print("\n📚 Generating Master Documentation Index...")
        
        docs_dir = self.project_root / 'docs'
        docs_dir.mkdir(exist_ok=True)
        
        index_path = docs_dir / 'index.md'
        
        with open(index_path, 'w') as f:
            f.write("# TapFlow Analytics Documentation Hub\n\n")
            f.write(f"Last Updated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 Platform Documentation\n\n")
            
            f.write("### [Data Catalog](data_catalog/index.md)\n")
            f.write("Comprehensive documentation of all tables, columns, and relationships.\n")
            f.write("- Database schemas and tables\n")
            f.write("- Column definitions and data types\n")
            f.write("- Entity relationship diagrams\n")
            f.write("- Data quality reports\n\n")
            
            f.write("### [Metrics Catalog](metrics_catalog/index.md)\n")
            f.write("Business metrics and KPI definitions with calculations.\n")
            f.write("- Revenue metrics (MRR, ARR, LTV)\n")
            f.write("- Operational metrics (uptime, performance)\n")
            f.write("- Customer metrics (churn, NPS, health)\n")
            f.write("- Product metrics (adoption, engagement)\n\n")
            
            f.write("## 🎓 Educational Resources\n\n")
            
            f.write("### [Onboarding Guides](../edu/onboarding/)\n")
            f.write("Role-specific onboarding programs:\n")
            f.write("- [Sales Analytics](../edu/onboarding/sales/day1_platform_overview.md)\n")
            f.write("- [Marketing Analytics](../edu/onboarding/marketing/day1_marketing_overview.md)\n")
            f.write("- [Product Analytics](../edu/onboarding/product/day1_product_overview.md)\n")
            f.write("- [Customer Success](../edu/onboarding/customer_success/day1_cs_overview.md)\n")
            f.write("- [Analytics Engineering](../edu/onboarding/analytics_engineering/week1_technical_foundation.md)\n\n")
            
            f.write("### [Workday Simulations](../edu/workday_simulations/)\n")
            f.write("Real-world scenarios and daily workflows:\n")
            f.write("- [Sales Analyst Day](../edu/workday_simulations/sales_analyst_day.md)\n")
            f.write("- Monthly projects and exercises\n")
            f.write("- Quarterly initiatives\n\n")
            
            f.write("### [Team OKRs](../edu/team_okrs/)\n")
            f.write("Objectives and key results by team:\n")
            f.write("- [Q1 2025 OKRs](../edu/team_okrs/q1_2025_okrs.md)\n")
            f.write("- Team priorities and initiatives\n\n")
            
            f.write("## 🔧 Technical Documentation\n\n")
            
            f.write("### Data Pipeline\n")
            f.write("- [Setup Guide](../README.md)\n")
            f.write("- [dbt Project](../transform/README.md)\n")
            f.write("- [Data Generation](../scripts/README.md)\n\n")
            
            f.write("### API Reference\n")
            f.write("- Query patterns and examples\n")
            f.write("- Performance optimization tips\n")
            f.write("- Best practices\n\n")
            
            f.write("## 🔄 Documentation Updates\n\n")
            f.write("This documentation is automatically generated and updated:\n")
            f.write("- **Trigger**: Database schema changes, new data, or manual run\n")
            f.write("- **Frequency**: Daily at 2 AM UTC\n")
            f.write("- **Manual Update**: `python scripts/documentation/generate_all_docs.py`\n\n")
            
            f.write("## 📈 Platform Statistics\n\n")
            
            # Add some basic stats
            stats_file = self.project_root / 'docs' / 'data_catalog' / 'data_quality_report.md'
            if stats_file.exists():
                f.write("See [Data Quality Report](data_catalog/data_quality_report.md) for current statistics.\n\n")
            
            f.write("## 📞 Support\n\n")
            f.write("- **Analytics Engineering Team**: For technical questions\n")
            f.write("- **Documentation Issues**: Create an issue in the repository\n")
            f.write("- **Training Requests**: Contact your team lead\n")
        
        print(f"✅ Master index created at {index_path}")
    
    def save_generation_log(self, results):
        """Save generation results to log file"""
        log_dir = self.log_file.parent
        log_dir.mkdir(exist_ok=True)
        
        # Load existing log if it exists
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {'generations': []}
        
        # Add new generation
        log_data['generations'].append(results)
        
        # Keep only last 30 generations
        log_data['generations'] = log_data['generations'][-30:]
        
        # Save updated log
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n📝 Generation log saved to {self.log_file}")
    
    def print_summary(self, results):
        """Print generation summary"""
        print("\n" + "=" * 80)
        print("GENERATION SUMMARY")
        print("=" * 80)
        
        total_duration = sum(g['duration'] for g in results['generators'].values())
        successful = sum(1 for g in results['generators'].values() if g['success'])
        total = len(results['generators'])
        
        print(f"Total Generators Run: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        
        print("\nGenerator Results:")
        for name, result in results['generators'].items():
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {name}: {result['duration']:.2f}s")
        
        print("\n" + "=" * 80)
        print(f"Documentation generation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

def main():
    """Main entry point"""
    generator = MasterDocumentationGenerator()
    results = generator.generate_all()
    
    # Exit with appropriate code
    all_successful = all(g['success'] for g in results['generators'].values())
    sys.exit(0 if all_successful else 1)

if __name__ == "__main__":
    main()