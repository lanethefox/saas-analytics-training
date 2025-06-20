#!/usr/bin/env python3
"""
Analytics Pipeline Orchestrator - Container Version
Runs from within Airflow container
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
        self.log_file = f"/opt/airflow/logs/pipeline_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        self.results = {
            "start_time": self.start_time.isoformat(),
            "steps": []
        }
        
        # Ensure logs directory exists
        os.makedirs("/opt/airflow/logs", exist_ok=True)
        
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
                    "error": result.stderr[:500]
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
                host="postgres",  # Use container hostname
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
    
    def run_dbt_direct(self, dbt_command, description):
        """Run dbt command directly (assuming dbt is installed in container)"""
        # Change to dbt project directory
        os.chdir('/opt/dbt_project')
        
        cmd = f"dbt {dbt_command} --profiles-dir ."
        return self.run_command(cmd, description, timeout=600)
    
    def run_pipeline(self):
        """Run the complete analytics pipeline"""
        self.log("===== Starting Analytics Pipeline (Container Mode) =====")
        
        # Step 1: Check prerequisites
        success, _ = self.run_command(
            "echo 'Checking environment...' && which dbt && which psql",
            "Checking prerequisites",
            timeout=10
        )
        
        # Step 2: Get initial metrics
        initial_metrics = self.get_metrics()
        self.log(f"Initial metrics: {json.dumps(initial_metrics)}")
        
        # Step 3: Run dbt models
        success, output = self.run_dbt_direct("run", "Running dbt models")
        
        if success:
            # Count successful models
            model_count = output.count("OK created")
            self.log(f"Successfully created/updated {model_count} models")
        
        # Step 4: Run dbt tests (don't fail pipeline if tests fail)
        self.run_dbt_direct("test --select test_type:generic", "Running dbt tests")
        
        # Step 5: Generate documentation
        self.run_dbt_direct("docs generate", "Generating documentation")
        
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
        results_file = f"/opt/airflow/logs/pipeline_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"===== Pipeline Complete (took {duration:.1f}s) =====")
        self.log(f"Results saved to: {results_file}")
        
        # Return success if we have metrics
        return final_metrics.get('total_customers', 0) > 0
        
def main():
    """Main entry point"""
    pipeline = AnalyticsPipeline()
    
    try:
        success = pipeline.run_pipeline()
        return 0 if success else 1
    except KeyboardInterrupt:
        pipeline.log("Pipeline interrupted by user", "WARN")
        return 1
    except Exception as e:
        pipeline.log(f"Pipeline failed with error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())