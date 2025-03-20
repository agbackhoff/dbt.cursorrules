# dbt Core

A powerful open-source data transformation tool that enables analytics engineers to transform data in their warehouses by writing modular SQL enhanced with Jinja templating.

## Quick Start

1. Activate the virtual environment:
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. Configure your environment:
   - Copy `.env.example` to `.env` if you haven't already
   - Add your API keys in `.env` (optional)

3. Install dbt:
   ```bash
   pip install dbt-core
   # Install the adapter for your data warehouse
   pip install dbt-bigquery  # or dbt-snowflake, dbt-redshift, etc.
   ```

4. Initialize a new dbt project:
   ```bash
   dbt init my_project
   ```

## Understanding dbt Core

dbt (data build tool) transforms data by:
- Writing SELECT statements, not INSERT/UPDATE/DELETE
- Applying software engineering principles to SQL (modularity, portability, CI/CD, documentation)
- Using Jinja templating for DRY code patterns
- Running, testing, and documenting your SQL transformations within your data warehouse

dbt operates within your data warehouse, assembling source data into analytics-ready models without moving data outside of your database.

## Project Structure

A typical dbt project follows this structure:
```
my_project/
├── README.md
├── dbt_project.yml          # Project configuration
├── models/                  # Core transformation logic
│   ├── staging/             # Clean and standardize source data
│   ├── intermediate/        # Purpose-built transformations
│   └── marts/               # Business-defined output models
├── macros/                  # Reusable Jinja code blocks
├── tests/                   # Custom data tests
├── seeds/                   # Static CSV files to load
├── snapshots/               # Type 2 SCD logic
├── analyses/                # Non-materialized queries
└── packages.yml             # External dependencies
```

## The Three-Layer Architecture

dbt projects thrive when following a three-layer approach to transformation:

### 1. Staging Layer

The staging layer prepares source data into standardized "atomic" building blocks:

- One staging model per source table (1:1 relationship)
- Uses the naming convention `stg_[source]__[entity]`
- Performs light transformations:
  - Renames fields to a consistent standard
  - Converts data types appropriately
  - Handles basic NULL values
  - Creates consistent surrogate keys
- Typically materialized as views (unless performance requires otherwise)
- Example: `stg_stripe__payments.sql`, `stg_shopify__orders.sql`

### 2. Intermediate Layer

The intermediate layer contains purpose-built transformation steps:

- Contains models that sit between staging and marts
- Uses the naming convention `int_[entity]_[verb]`
- Serves specific purposes:
  - Builds reusable components needed by multiple downstream models
  - Reduces complexity by breaking complicated transformations into steps
  - Improves maintainability through modularity
- Examples: `int_payments_pivoted_to_orders.sql`, `int_customer_order_history_joined.sql`

### 3. Marts Layer

The marts layer presents business-defined entities for consumption:

- Organized by business domains or departments (finance, marketing, etc.)
- Contains wide tables that represent complete business entities
- Materialized as tables for query performance
- Designed for business user consumption
- Example: `finance/orders.sql`, `marketing/customers.sql`

This layered approach creates a clean progression from source-conformed data (shaped by external systems) to business-conformed data (shaped by internal definitions and needs).

## SQL Style Guidelines

Writing clean, consistent SQL is essential for maintainable dbt projects:

### General SQL Format

- Use 4 spaces for indentation
- Line up common SQL elements vertically
- Keep lines under 80 characters when possible
- Use trailing commas for cleaner diffs when adding columns
- Use lowercase for SQL functions and keywords
- Use snake_case for column and model names

### Example SQL Format

```sql
-- Good example
WITH customers_data AS (
    SELECT
        id,
        first_name,
        last_name,
        birthdate,
        status,
        amount
    FROM {{ ref('customers') }}
    WHERE status IS NOT null
)
SELECT
    id,
    first_name,
    last_name,
    CAST(birthdate AS date) AS birthdate,
    CASE
        WHEN status = 'active' THEN true
        ELSE false
    END AS is_active,
    SUM(amount) AS total_amount,  -- Trailing comma for easier addition later
FROM customers_data
GROUP BY 1, 2, 3, 4, 5
ORDER BY id
```

### CTEs

- Use CTEs (`with` statements) liberally to break up complex queries
- Name CTEs with clear, descriptive names
- Add comments above CTEs to explain complex logic
- Use CTEs instead of subqueries when possible

```sql
-- Good CTE example
WITH 

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customer_orders AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS total_amount
    FROM orders
    GROUP BY 1
),

final AS (
    SELECT
        customers.id,
        customers.name,
        customers.email,
        COALESCE(customer_orders.order_count, 0) AS order_count,
        COALESCE(customer_orders.total_amount, 0) AS total_amount
    FROM customers
    LEFT JOIN customer_orders ON customers.id = customer_orders.customer_id
)

SELECT * FROM final
```

## Jinja Templating Best Practices

Jinja is a powerful templating language that extends SQL in dbt:

### Jinja Style

- Use spaces inside Jinja delimiters: `{{ this }}` not `{{this}}`
- Use newlines to visually separate logical blocks of Jinja
- Indent 4 spaces within Jinja blocks
- Set variables at the top of models

```sql
{# Good Jinja example #}
{% set payment_methods = ["bank_transfer", "credit_card", "gift_card"] %}

SELECT
    order_id,
    {% for payment_method in payment_methods %}
    
        SUM(CASE WHEN payment_method = '{{ payment_method }}' THEN amount ELSE 0 END) 
            AS {{ payment_method }}_amount,
    
    {% endfor %}
    SUM(amount) AS total_amount
FROM {{ ref('stg_payments') }}
GROUP BY 1
```

### dbtonic Jinja

- Favor readability over DRY-ness - not everything needs to be a macro
- Use established macros from dbt-utils and other packages
- Avoid nesting curlies (e.g., `{{ {{ no }} }}`)
- Remember to quote column names properly: `{{ my_macro('column_name') }}`

## YAML Configuration Best Practices

dbt uses YAML files for configuration, documentation, and testing:

### YAML Style Guidelines

- Use 2 spaces for indentation
- Indent list items
- Keep lines under 80 characters
- Use the dbt JSON schema with a YAML formatter (like Prettier)
- Group related configuration in separate files with clear names

### YAML Organization by Model

Create separate YAML files for each model to improve maintainability and organization:

1. Create one YAML file per model or logical group of models
2. Name files descriptively: `models/schema/[model_name].yml`
3. Keep related models together (e.g., staging models for the same source)

Example directory structure:

### Configuration Organization

- Use separate YAML files for each schema/source
- Prefix YAML files with underscore: `_jaffle_shop__models.yml`
- Organize by business domain or data source
- Use YAML anchors for repeated configurations (when appropriate)

## Testing and Documentation

dbt validates your transformations with tests and provides comprehensive documentation:

### Testing Guidelines

- Add tests for all primary and foreign keys
- Write custom data tests for business logic validation
- Test at both the model and column level
- Use a combination of generic tests (unique, not_null) and custom tests
- Run tests automatically in CI/CD

```yaml
# Example of comprehensive testing
models:
  - name: orders
    tests:
      - dbt_utils.equal_rowcount:
          compare_model: ref('raw_orders')
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['placed', 'shipped', 'completed', 'returned']
```

### Documentation Best Practices

- Document all models and critical columns
- Include business context and definitions
- Use markdown for rich documentation
- Separate documentation into dedicated files for complex descriptions
- Generate and share documentation with stakeholders

```yaml
# Example of good documentation
models:
  - name: orders
    description: >
      One record per order. This table contains all orders placed on the
      Jaffle Shop website.
    columns:
      - name: order_id
        description: Primary key of the orders table
      - name: customer_id
        description: Foreign key to the customers table
      - name: order_date
        description: Date (UTC) when the order was placed
      - name: status
        description: >
          Current status of the order. One of 'placed', 'shipped', 
          'completed', or 'returned'.
```

## Materialization Strategies

dbt offers various materialization options to balance performance and freshness:

### Available Materializations

- **View**: SQL views that query source data directly
  - Pro: No storage needed, always up-to-date
  - Con: Can be slow for complex transformations
  - Ideal for: Staging models, simple transformations

- **Table**: Rebuilt from scratch with each run
  - Pro: Fast query performance
  - Con: Uses storage, complete rebuilds take time
  - Ideal for: Smaller mart models

- **Incremental**: Only processes new/changed data (Do not use if unneccesary)
  - Pro: Efficient for large tables with frequent updates
  - Con: More complex to set up
  - Ideal for: Fact tables, event data, large datasets

- **Ephemeral**: Not built in the database, just included in dependent models
  - Pro: No storage needed, reduces model count
  - Con: Can't be queried directly, can complicate debugging
  - Ideal for: Simple transformations used by only one downstream model

### Materialization Principles

1. **Start simple**: Begin with views for stg and tables for entities, fct, marts, and only optimize when needed
2. **Measure first**: Use query performance to guide materialization choices
3. **Follow the DAG**: More heavily-used, upstream models are better candidates for table materialization
4. **Consider data volume**: Larger datasets benefit more from incremental strategies
5. **Balance freshness vs. performance**: Choose materializations based on business requirements

```sql
-- Example incremental model
{{ config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge'
) }}

with events as (
    select * from {{ ref('stg_events') }}
    
    {% if is_incremental() %}
        -- Only get new records since last run
        where event_time > (select max(event_time) from {{ this }})
    {% endif %}
)

select
    event_id,
    event_time,
    event_type,
    user_id,
    -- Additional processing here
from events
```

## Workflow Best Practices

Effective dbt workflows incorporate proper version control, CI/CD, and environment management:

### Version Control

- Always use Git for your dbt projects
- Create feature branches for new development
- Use meaningful commit messages
- Review code changes via pull requests
- Never commit sensitive credentials

### Development Workflow

1. Pull latest changes from main
2. Create a feature branch
3. Make changes to models
4. Test locally: `dbt test -s my_model`
5. Run and verify: `dbt run -s my_model`
6. Commit and push changes
7. Create pull request
8. Review and merge after CI/CD passes

### Environment Management

- Use separate targets in your profiles.yml:
  - **dev**: Personal development environment
  - **ci**: Continuous integration testing
  - **prod**: Production environment

- Tailor configurations to each environment:
  ```yaml
  # In dbt_project.yml
  models:
    my_project:
      +materialized: view
      marts:
        +materialized: table
        # Override for production
        +schema: "{{ 'marts' if target.name == 'prod' else 'dev_marts' }}"
  ```

### Continuous Integration

- Run dbt tests on all PRs
- Validate SQL syntax and compilation
- Check for documentation coverage
- Ensure proper test coverage

### Promotion to Production

- Merge code to main only after review
- Use CI/CD to deploy to production
- Schedule regular production runs
- Monitor for failures and performance

By following these guidelines, your dbt projects will be maintainable, performant, and accessible to all stakeholders in your organization. 


## Available Tools

Your project includes several powerful tools in the `tools/` directory:

### LLM Integration
```python
from tools.llm_api import query_llm

# Use LLM for assistance
response = query_llm(
    "Your question here",
    provider="anthropic"  # Options: openai, anthropic, azure_openai, deepseek, gemini
)
print(response)
```

### Web Scraping
```python
from tools.web_scraper import scrape_urls

# Scrape web content
results = scrape_urls(["https://example.com"], max_concurrent=3)
```

### Search Engine
```python
from tools.search_engine import search

# Search the web
results = search("your search keywords")
```


### Screenshot Verification
```python
from tools.screenshot_utils import take_screenshot_sync
from tools.llm_api import query_llm

# Take and analyze screenshots
screenshot_path = take_screenshot_sync('https://example.com', 'screenshot.png')
analysis = query_llm(
    "Describe this webpage",
    provider="openai",
    image_path=screenshot_path
)
```

Note: When you first use the screenshot verification feature, Playwright browsers will be installed automatically.


## AI Assistant Configuration


This project uses `.cursorrules` to configure the AI assistant. The assistant can:
- Help with coding tasks
- Verify screenshots
- Perform web searches
- Analyze images and code


## Environment Variables

Configure these in your `.env` file:

- `LLM_API_KEY`: Your LLM API key (optional)
- `SILICONFLOW_API_KEY`: Siliconflow API key (optional)
Note: Basic functionality works without API keys. Advanced features (like multimodal analysis) require appropriate API keys.

## Development Tools
- `.vscode.example/`: Recommended VS Code settings
- `.github/`: CI/CD workflows

## Scratchpad


## License

MIT License