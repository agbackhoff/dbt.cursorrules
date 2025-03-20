# GCP BigQuery Tool Guide

A command-line utility for interacting with Google BigQuery using a service account. This tool allows you to explore and query BigQuery datasets securely with read-only permissions.

## Table of Contents

- [Requirements](#requirements)
- [Service Account Setup](#service-account-setup)
- [Installation](#installation)
- [Usage](#usage)
- [Command Reference](#command-reference)
- [Examples](#examples)
- [Output Formats](#output-formats)
- [Troubleshooting](#troubleshooting)

## Requirements

- Python 3.7+
- A Google Cloud Platform project with BigQuery enabled
- A service account with appropriate permissions
- The `google-cloud-bigquery` Python package

## Service Account Setup

### Required Permissions

Your service account needs the following IAM roles:

1. **BigQuery Data Viewer** (`roles/bigquery.dataViewer`)
   - Provides read-only access to data stored in BigQuery tables and views

2. **BigQuery Metadata Viewer** (`roles/bigquery.metadataViewer`)
   - Allows viewing dataset metadata, table schemas, and other metadata

3. **BigQuery Job User** (`roles/bigquery.jobUser`)
   - Allows running BigQuery jobs (queries)

### Creating a Service Account

1. Navigate to the [GCP Console IAM & Admin page](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select your project and click "Create Service Account"
3. Name your service account (e.g., "bigquery-readonly-user")
4. Add the required roles: BigQuery Data Viewer, BigQuery Metadata Viewer, and BigQuery Job User
5. Create a key for the service account (JSON format)
6. Download and securely store the JSON key file

## Installation

1. Ensure Python 3.7+ is installed
2. Activate your virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install google-cloud-bigquery tabulate
   ```
4. Set the environment variable in .env to your service account key file:
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
   ```

## Usage

The tool can be run with various commands to interact with BigQuery:

```bash
venv/bin/python3 tools/gcp_bigquery.py [command] [options]
```

## Command Reference

### List Datasets

```bash
venv/bin/python3 tools/gcp_bigquery.py list-datasets [--project PROJECT_ID]
```

**Parameters:**
- `--project PROJECT_ID` (optional): Specify a GCP project ID. If not provided, uses the default project from the service account.

**Output:**
A table listing all datasets in the project with their IDs and descriptions.

### List Tables

```bash
venv/bin/python3 tools/gcp_bigquery.py list-tables DATASET_ID [--project PROJECT_ID]
```

**Parameters:**
- `DATASET_ID`: ID of the dataset to list tables from.
- `--project PROJECT_ID` (optional): Specify a GCP project ID.

**Output:**
A table listing all tables and views in the dataset with their names, types (TABLE or VIEW), and descriptions.

### Get Schema

```bash
venv/bin/python3 tools/gcp_bigquery.py get-schema DATASET_ID TABLE_ID [--project PROJECT_ID]
```

**Parameters:**
- `DATASET_ID`: ID of the dataset.
- `TABLE_ID`: ID of the table or view.
- `--project PROJECT_ID` (optional): Specify a GCP project ID.

**Output:**
A table showing the schema of the specified table or view, including column names, data types, whether they're nullable, and descriptions.

### Run Query

```bash
venv/bin/python3 tools/gcp_bigquery.py run-query "SQL_QUERY" [--project PROJECT_ID] [--dry-run]
```

**Parameters:**
- `SQL_QUERY`: The SQL query to execute (must be enclosed in quotes).
- `--project PROJECT_ID` (optional): Specify a GCP project ID.
- `--dry-run` (optional): Validate the query without executing it.

**Output:**
For successful queries, outputs the first 5 rows of results in tabular format.
For errors, displays the error message from BigQuery.

## Examples

### List all datasets in a project

```bash
venv/bin/python3 tools/gcp_bigquery.py list-datasets --project my-analytics-project
```

Example output:
```
Dataset ID              | Description
------------------------|---------------------------------
customer_data           | Customer information and profiles
sales_data              | Raw sales transactions
marketing_analytics     | Marketing campaign performance data
```

### List all tables in a dataset

```bash
venv/bin/python3 tools/gcp_bigquery.py list-tables sales_data
```

Example output:
```
Table ID                | Type  | Description
------------------------| ----- | ---------------------------------
transactions            | TABLE | All sales transactions
monthly_summary         | VIEW  | Monthly aggregated sales by product
customer_purchases      | TABLE | Customer purchase history
```

### Get schema for a table

```bash
venv/bin/python3 tools/gcp_bigquery.py get-schema sales_data transactions
```

Example output:
```
Column Name    | Data Type     | Nullable | Description
---------------|---------------|----------|-------------------------------------
transaction_id | STRING        | NO       | Unique transaction identifier
customer_id    | STRING        | NO       | Customer identifier
product_id     | STRING        | NO       | Product identifier
quantity       | INTEGER       | NO       | Number of units purchased
price          | NUMERIC       | NO       | Price per unit
timestamp      | TIMESTAMP     | NO       | Transaction timestamp
store_id       | STRING        | YES      | Store identifier where purchase made
```

### Run a simple query

```bash
venv/bin/python3 tools/gcp_bigquery.py run-query "SELECT product_id, SUM(quantity) as total_sold FROM sales_data.transactions GROUP BY product_id ORDER BY total_sold DESC LIMIT 5"
```

Example output:
```
product_id     | total_sold
---------------|------------
P-10392        | 43829
P-39281        | 38291
P-56832        | 37281
P-11892        | 34776
P-98275        | 31092
```

## Output Formats

All outputs are formatted as tables with clear headers and properly aligned columns for easy reading in the terminal.

## Troubleshooting

### Authentication Issues

- Ensure the `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly
- Verify your service account has the necessary permissions
- Check that the service account key file is valid and not expired

### Query Errors

- The tool will display any error messages returned by BigQuery
- Common issues include:
  - Syntax errors in SQL queries
  - References to non-existent tables or columns
  - Attempting to execute DML or DDL statements (not supported)

### Permission Errors

- If you encounter permission errors, ensure your service account has:
  - `bigquery.datasets.get` permission for listing datasets
  - `bigquery.tables.list` permission for listing tables
  - `bigquery.tables.get` permission for getting schemas
  - `bigquery.jobs.create` permission for running queries 