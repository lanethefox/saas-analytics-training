#!/usr/bin/env python3
"""
Analytics Pipeline Orchestrator
Simple Python-based orchestration for the analytics pipeline
"""

import subprocess
import json
import os
import sys
from datetime import datetime
import time
import psycopg2

class AnalyticsPipeline:
    def __init__(self):
        self.start_time = datetime.now()
        self.log_file = f"logs/pipeline_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        self.results = {
            "start_time": self.start_time.isoformat(),
            "steps": []
        }
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
    def log(self, message, level="INFO"):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, command, description, timeout=300):
        """Run a shell command and capture output"""
        self.log(f"Starting: {description}")
        step_start = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - step_start
            
            if result.returncode == 0:
                self.log(f"✅ Success: {description} (took {duration:.1f}s)")
                self.results["steps"].append({
                    "name": description,
                    "status": "success",
                    "duration": duration
                })
                return True, result.stdout
            else:
                self.log(f"❌ Failed: {description}", "ERROR")
                self.log(f"Error: {result.stderr}", "ERROR")
                self.results["steps"].append({
                    "name": description,
                    "status": "failed",
                    "duration": duration,
                    "error": result.stderr[:500]  # First 500 chars of error
                })
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.log(f"⏱️ Timeout: {description} (after {timeout}s)", "ERROR")
            self.results["steps"].append({
                "name": description,
                "status": "timeout",
                "duration": timeout
            })
            return False, "Command timed out"
    
    def get_metrics(self):
        """Get current platform metrics"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="saas_platform_dev",
                user="saas_user",
                password="saas_secure_password_2024"
            )
            cursor = conn.cursor()
            
            # Get key metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_customers,
                    COUNT(CASE WHEN customer_status = 'active' THEN 1 END) as active_customers,
                    SUM(CASE WHEN customer_status = 'active' THEN monthly_recurring_revenue ELSE 0 END) as total_mrr
                FROM entity.entity_customers
            """)
            
            customers, active, mrr = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                "total_customers": customers,
                "active_customers": active,
                "total_mrr": float(mrr) if mrr else 0
            }
            
        except Exception as e:
            self.log(f"Failed to get metrics: {e}", "WARN")
            return {}
    
    def run_pipeline(self):
        """Run the complete analytics pipeline"""
        self.log("===== Starting Analytics Pipeline =====")
        
        # Step 1: Check prerequisites
        success, _ = self.run_command(
            "docker ps | grep -E '(postgres|dbt)' | wc -l",
            "Checking container status",
            timeout=10
        )
        
        # Step 2: Get initial metrics
        initial_metrics = self.get_metrics()
        self.log(f"Initial metrics: {json.dumps(initial_metrics)}")
        
        # Step 3: Run dbt models
        success, output = self.run_command(
            "docker exec saas_platform_dbt_core bash -c 'cd /opt/dbt_project && dbt run --profiles-dir .'",
            "Running dbt models",
            timeout=600
        )
        
        if success:
            # Count successful models
            model_count = output.count("OK created")
            self.log(f"Successfully created/updated {model_count} models")
        
        # Step 4: Run dbt tests (don't fail pipeline if tests fail)
        self.run_command(
            "docker exec saas_platform_dbt_core bash -c 'cd /opt/dbt_project && dbt test --profiles-dir . --select test_type:generic'",
            "Running dbt tests",
            timeout=300
        )
        
        # Step 5: Generate documentation
        self.run_command(
            "docker exec saas_platform_dbt_core bash -c 'cd /opt/dbt_project && dbt docs generate --profiles-dir .'",
            "Generating documentation",
            timeout=120
        )
        
        # Step 6: Get final metrics
        final_metrics = self.get_metrics()
        self.log(f"Final metrics: {json.dumps(final_metrics)}")
        
        # Calculate duration
        duration = (datetime.now() - self.start_time).total_seconds()
        
        # Update results
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration"] = duration
        self.results["initial_metrics"] = initial_metrics
        self.results["final_metrics"] = final_metrics
        self.results["status"] = "completed"
        
        # Save results
        results_file = f"logs/pipeline_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"===== Pipeline Complete (took {duration:.1f}s) =====")
        self.log(f"Results saved to: {results_file}")
        
        # Create summary
        self.create_summary()
        
    def create_summary(self):
        """Create a human-readable summary"""
        summary_file = f"logs/summary_{datetime.now().strftime('%Y%m%d')}.txt"
        
        with open(summary_file, "w") as f:
            f.write("Analytics Pipeline Summary\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {self.results['duration']:.1f} seconds\n")
            f.write(f"Status: {self.results['status']}\n\n")
            
            f.write("Steps Summary:\n")
            for step in self.results["steps"]:
                status_icon = "✅" if step["status"] == "success" else "❌"
                f.write(f"  {status_icon} {step['name']} ({step['duration']:.1f}s)\n")
            
            f.write(f"\nMetrics:\n")
            if "final_metrics" in self.results:
                m = self.results["final_metrics"]
                f.write(f"  Total Customers: {m.get('total_customers', 'N/A')}\n")
                f.write(f"  Active Customers: {m.get('active_customers', 'N/A')}\n")
                f.write(f"  Total MRR: ${m.get('total_mrr', 0):,.2f}\n")
            
            f.write(f"\nLog file: {self.log_file}\n")
        
        print(f"\nSummary saved to: {summary_file}")

def main():
    """Main entry point"""
    pipeline = AnalyticsPipeline()
    
    try:
        pipeline.run_pipeline()
        return 0
    except KeyboardInterrupt:
        pipeline.log("Pipeline interrupted by user", "WARN")
        return 1
    except Exception as e:
        pipeline.log(f"Pipeline failed with error: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())