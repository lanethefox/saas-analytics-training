# Documentation Maintenance Guide

## Overview

This guide explains how to maintain and update the self-generating documentation system for the TapFlow Analytics platform.

## Architecture

### Documentation Generators

1. **Data Catalog Generator** (`scripts/documentation/generate_data_catalog.py`)
   - Introspects database schema
   - Documents all tables, columns, relationships
   - Generates ERDs and data quality reports

2. **Metrics Catalog Generator** (`scripts/documentation/generate_metrics_catalog.py`)
   - Documents business metrics and KPIs
   - Shows calculation logic and examples
   - Tracks metric lineage

3. **Education Content Generator** (`scripts/documentation/generate_education_content.py`)
   - Creates role-specific onboarding guides
   - Generates workday simulations
   - Maintains team OKRs and priorities

4. **Master Generator** (`scripts/documentation/generate_all_docs.py`)
   - Orchestrates all generators
   - Creates master index
   - Logs generation history

## Automated Updates

### GitHub Actions Workflow

The documentation automatically updates via `.github/workflows/generate_docs.yml`:

**Triggers:**
- Push to main branch (schema/model changes)
- Daily at 2 AM UTC
- Manual workflow dispatch

**Process:**
1. Spins up PostgreSQL database
2. Loads sample data
3. Runs dbt models
4. Executes all documentation generators
5. Commits updates back to repository

### Manual Updates

```bash
# Generate all documentation
python scripts/documentation/generate_all_docs.py

# Generate specific documentation
python scripts/documentation/generate_data_catalog.py
python scripts/documentation/generate_metrics_catalog.py
python scripts/documentation/generate_education_content.py
```

## Adding New Content

### 1. New Metrics

To add a new metric to the catalog:

1. Add metric definition to `generate_metrics_catalog.py`:
```python
def add_new_metric(self, f):
    """Add documentation for new metric"""
    f.write("## New Metric Name\n\n")
    f.write("### Definition\n")
    f.write("Clear business definition\n\n")
    
    f.write("### Calculation\n")
    f.write("```sql\n")
    f.write("-- SQL calculation\n")
    f.write("```\n\n")
    
    # Get current value from database
    self.cur.execute("SELECT ...")
    result = self.cur.fetchone()
    
    f.write("### Current Value\n")
    f.write(f"- **Metric**: {result['value']}\n")
```

2. Call the function in appropriate category method

### 2. New Educational Module

To add a new training module:

1. Create generation method in `generate_education_content.py`:
```python
def generate_new_role_onboarding(self):
    """Generate onboarding for new role"""
    output_dir = self.edu_dir / 'onboarding' / 'new_role'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use real data for examples
    self.cur.execute("SELECT ...")
    real_data = self.cur.fetchall()
    
    with open(output_dir / 'day1_overview.md', 'w') as f:
        # Write content using real_data
```

2. Add to `generate_all()` method

### 3. New Table/Schema

When adding new database objects:

1. The data catalog generator will automatically pick them up
2. Consider adding specific documentation in `document_table()` method
3. Update sample queries if needed

## Maintenance Tasks

### Weekly
- Review generation logs in `docs/generation_log.json`
- Check for failed generations
- Validate documentation accuracy

### Monthly
- Update OKRs and team priorities
- Refresh workday simulations with new scenarios
- Add new metrics based on business needs

### Quarterly
- Major curriculum updates
- New role onboarding programs
- Archive outdated educational content

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify credentials in scripts
   - Ensure database has sample data

2. **Generator Timeout**
   - Large datasets may need pagination
   - Add progress indicators
   - Consider parallel processing

3. **Missing Documentation**
   - Check generator completed successfully
   - Verify output directories exist
   - Review error logs

### Debug Mode

Add verbose logging:
```python
# In any generator
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Use Real Data**
   - Always pull examples from actual database
   - Show current metric values
   - Use real account names (sanitized if needed)

2. **Keep It Current**
   - Documentation should reflect today's data
   - Update examples regularly
   - Remove deprecated content

3. **Maintain Consistency**
   - Follow existing formatting patterns
   - Use same terminology across docs
   - Link between related content

4. **Version Control**
   - Commit documentation updates separately
   - Use clear commit messages
   - Tag major documentation releases

## Quality Checks

Before releasing documentation:

1. **Accuracy**
   - Verify SQL queries execute correctly
   - Check metric calculations match production
   - Validate example data is current

2. **Completeness**
   - All tables documented
   - All metrics defined
   - All roles have onboarding

3. **Usability**
   - Clear navigation structure
   - Working links between documents
   - Searchable content

## Contact

For questions or improvements:
- Analytics Engineering Team: Primary maintainers
- Documentation issues: Create GitHub issue
- Feature requests: Discuss in team meeting