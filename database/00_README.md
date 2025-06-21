# Database Initialization Scripts

This directory contains SQL scripts that initialize the database schema. They are executed in alphabetical order by Docker during container initialization.

## Execution Order

### Core Scripts (Required)
1. **`01_main_schema.sql`** - Creates the main database schema
   - Creates `saas_platform_dev` and `superset_db` databases
   - Sets up the `raw` schema with all application tables
   - Includes columns for both existing data and data generator compatibility
   - Creates indexes and constraints

2. **`02_superset_init.sql`** - Initializes Superset database
   - Creates Superset user and permissions
   - Sets up read-only access to main database
   - Configures proper grants for Superset operation

### Optional Scripts
- **`99_optional_warp_memory.sql`** - Vector database for memory features
  - Creates `warp_memory` database with pgvector extension
  - Only needed if using memory/embedding features
  - Can be safely ignored for standard analytics setup

## Notes
- Files are executed in alphabetical order
- The `01_main_schema.sql` is the enhanced schema that supports the data generator
- All scripts are idempotent (can be run multiple times safely)
- Docker's postgres initialization only runs these on first container creation

## Adding New Scripts
- Use numbering prefix to control execution order
- Core functionality: 01-50
- Optional features: 51-98
- Experimental/development: 99