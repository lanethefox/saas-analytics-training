# Data Literacy Prerequisites Guide

## Introduction

This guide outlines the foundational data literacy skills required for success in the analytics curriculum. These prerequisites ensure all learners start with a common baseline understanding of data concepts, enabling them to focus on advanced analytical techniques rather than basic data comprehension.

## Core Data Concepts

### 1. Data Types and Structures

**Quantitative Data**
- **Continuous**: Measurements that can take any value (e.g., revenue, time, temperature)
- **Discrete**: Countable values (e.g., number of customers, transactions)

**Qualitative Data**
- **Nominal**: Categories without order (e.g., customer segment, product type)
- **Ordinal**: Categories with order (e.g., satisfaction ratings, tier levels)

**Data Structures**
- **Structured Data**: Organized in tables with rows and columns
- **Time Series Data**: Data points indexed by time
- **Hierarchical Data**: Parent-child relationships (e.g., account → locations → devices)

### 2. Basic Statistical Concepts

**Measures of Central Tendency**
- **Mean**: Average value, sensitive to outliers
- **Median**: Middle value, robust to outliers
- **Mode**: Most frequent value

**Measures of Spread**
- **Range**: Difference between max and min
- **Standard Deviation**: Average distance from mean
- **Percentiles**: Values below which a percentage of data falls

**Common Business Applications**
- Average Revenue Per User (ARPU) uses mean
- Median deal size for typical transactions
- 90th percentile for performance SLAs

### 3. Data Quality Fundamentals

**Accuracy**
- Data correctly represents real-world values
- Example: Customer email addresses are valid

**Completeness**
- All required data is present
- Example: No missing values in critical fields

**Consistency**
- Data follows the same format and rules
- Example: Dates always in YYYY-MM-DD format

**Timeliness**
- Data is current and relevant
- Example: Daily metrics updated by 9 AM

**Common Data Quality Issues**
- Duplicates: Same entity recorded multiple times
- Missing values: NULL or empty fields
- Outliers: Extreme values that may be errors
- Inconsistent formats: Mixed date or currency formats

## Essential Technical Skills

### 1. Spreadsheet Proficiency

**Basic Functions**
```
=SUM(A1:A10)          # Sum values
=AVERAGE(B1:B10)      # Calculate mean
=COUNT(C1:C10)        # Count non-empty cells
=IF(D1>100,"High","Low")  # Conditional logic
```

**Data Manipulation**
- Sorting and filtering data
- Creating pivot tables
- Using VLOOKUP/INDEX-MATCH
- Basic chart creation

**Best Practices**
- Use clear column headers
- Format numbers appropriately
- Document formulas
- Validate data before analysis

### 2. Basic SQL Understanding

**Core Commands**
```sql
-- Selecting data
SELECT column1, column2 
FROM table_name
WHERE condition;

-- Aggregating data
SELECT 
    category,
    COUNT(*) as count,
    AVG(revenue) as avg_revenue
FROM sales
GROUP BY category;

-- Joining tables
SELECT 
    c.customer_name,
    s.total_revenue
FROM customers c
JOIN sales s ON c.customer_id = s.customer_id;
```

**Key Concepts**
- Primary and foreign keys
- Table relationships
- Filtering with WHERE
- Grouping and aggregation
- Basic joins (INNER, LEFT)

### 3. Data Visualization Basics

**Chart Selection**
- **Bar Charts**: Comparing categories
- **Line Charts**: Showing trends over time
- **Scatter Plots**: Examining relationships
- **Pie Charts**: Showing composition (use sparingly)

**Visualization Best Practices**
- Choose appropriate chart types
- Use clear titles and labels
- Avoid chartjunk and 3D effects
- Consider color blindness
- Tell a story with data

## Business Context Understanding

### 1. Key SaaS Metrics

**Revenue Metrics**
- **MRR (Monthly Recurring Revenue)**: Predictable monthly revenue
- **ARR (Annual Recurring Revenue)**: MRR × 12
- **ARPU (Average Revenue Per User)**: MRR / Active Customers

**Growth Metrics**
- **Customer Acquisition**: New customers added
- **Churn Rate**: Percentage of customers lost
- **Net Revenue Retention**: Revenue retained + expansion

**Efficiency Metrics**
- **CAC (Customer Acquisition Cost)**: Cost to acquire customer
- **LTV (Lifetime Value)**: Total revenue from customer
- **CAC Payback Period**: Months to recover CAC

### 2. Business Model Comprehension

**Subscription Business Basics**
- Recurring revenue model
- Importance of retention
- Expansion revenue opportunities
- Churn impact on growth

**B2B vs B2C Differences**
- Longer sales cycles
- Higher contract values
- Multiple stakeholders
- Account-based approaches

### 3. Analytical Thinking

**Problem Decomposition**
- Break complex problems into components
- Identify key drivers and dependencies
- Prioritize based on impact

**Hypothesis Formation**
- State clear, testable hypotheses
- Identify required data
- Plan analysis approach
- Consider alternative explanations

**Critical Evaluation**
- Question assumptions
- Validate data sources
- Consider biases
- Seek corroborating evidence

## Self-Assessment Checklist

### Data Concepts ✓
- [ ] I understand different data types
- [ ] I can calculate mean, median, and mode
- [ ] I recognize common data quality issues
- [ ] I understand the importance of data context

### Technical Skills ✓
- [ ] I can use basic spreadsheet functions
- [ ] I can write simple SQL queries
- [ ] I can create basic charts
- [ ] I understand table relationships

### Business Understanding ✓
- [ ] I know key SaaS metrics
- [ ] I understand subscription business models
- [ ] I can frame business questions
- [ ] I think critically about data

### Communication ✓
- [ ] I can explain findings clearly
- [ ] I choose appropriate visualizations
- [ ] I consider my audience
- [ ] I tell stories with data

## Recommended Preparation

### If You Need to Strengthen These Skills:

**Week 1: Data Fundamentals**
- Complete online statistics primer
- Practice identifying data types
- Work through data quality exercises

**Week 2: Technical Skills**
- SQL tutorial (focus on SELECT, WHERE, GROUP BY)
- Spreadsheet functions practice
- Create 5 different chart types

**Week 3: Business Context**
- Read SaaS metrics guide
- Study provided business cases
- Practice metric calculations

**Week 4: Integration**
- Complete practice assessment
- Work through sample analysis
- Present findings to peers

## Resources for Skill Building

### Online Courses
- Khan Academy: Statistics and Probability
- SQLiteracy: Basic SQL Course
- Google Analytics Academy: Data Analysis Basics

### Practice Datasets
- Course sample data (1,000 rows)
- Public datasets for exploration
- Spreadsheet exercises with solutions

### Reading Materials
- "Data Literacy for Business" (provided)
- SaaS Metrics Cheat Sheet
- Visualization Best Practices Guide

## Getting Help

### During the Course
- Instructor office hours
- Peer study groups
- Course Slack channel
- Technical support team

### Self-Study Resources
- Video tutorials library
- Practice problem sets
- Solution walkthroughs
- FAQ documentation

## Final Preparation Checklist

Before starting the curriculum:
1. ✓ Complete self-assessment
2. ✓ Address any skill gaps
3. ✓ Set up technical access
4. ✓ Review course materials
5. ✓ Join communication channels

Remember: These are prerequisites, not expertise requirements. The curriculum will build on these foundations to develop advanced analytical capabilities. Focus on understanding concepts rather than memorizing techniques - practical application throughout the course will reinforce and expand your skills.