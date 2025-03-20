#!/usr/bin/env python3
"""
Google BigQuery CLI Tool

A utility for interacting with Google BigQuery using a service account.
This tool provides read-only access to BigQuery datasets, tables, and data.

Features:
- List datasets in a project
- List tables/views in a dataset
- Get schema information for tables/views
- Run read-only queries with limited result output

Requirements:
- google-cloud-bigquery
- tabulate
- python-dotenv
"""

import argparse
import os
import sys
import re
from typing import List, Dict, Any, Optional, Union, Tuple

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import GoogleCloudError
    from tabulate import tabulate
    from dotenv import load_dotenv
except ImportError:
    print("Required dependencies not found. Please install them with:")
    print("pip install google-cloud-bigquery tabulate python-dotenv")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# Regular expressions for SQL validation
NON_READONLY_PATTERNS = [
    re.compile(r'\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|MERGE|TRUNCATE)\b', re.IGNORECASE),
    re.compile(r'\bGRANT\b.*\bTO\b', re.IGNORECASE),
    re.compile(r'\bREVOKE\b.*\bFROM\b', re.IGNORECASE),
]

class BigQueryTool:
    """Tool for interacting with Google BigQuery."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the BigQuery client.
        
        Args:
            project_id: Optional GCP project ID. If not provided, uses the default 
                        from the service account credentials.
        """
        try:
            self.client = bigquery.Client(project=project_id)
            if project_id:
                self.project_id = project_id
            else:
                self.project_id = self.client.project
                
            print(f"Connected to BigQuery project: {self.project_id}", file=sys.stderr)
        except GoogleCloudError as e:
            print(f"Error connecting to BigQuery: {e}")
            sys.exit(1)
            
    def list_datasets(self) -> List[Dict[str, str]]:
        """
        List all datasets in the project.
        
        Returns:
            List of dictionaries containing dataset information.
        """
        try:
            datasets = list(self.client.list_datasets())
            
            if not datasets:
                print(f"No datasets found in project {self.project_id}")
                return []
                
            result = []
            for dataset_list_item in datasets:
                # Get the full dataset to access description
                dataset_id = dataset_list_item.dataset_id
                dataset_ref = self.client.dataset(dataset_id)
                try:
                    dataset = self.client.get_dataset(dataset_ref)
                    description = dataset.description or ""
                except Exception:
                    # If we can't get the full dataset, just use an empty description
                    description = ""
                
                result.append({
                    "Dataset ID": dataset_id,
                    "Description": description
                })
                
            return result
        except GoogleCloudError as e:
            print(f"Error listing datasets: {e}")
            sys.exit(1)
            
    def list_tables(self, dataset_id: str) -> List[Dict[str, str]]:
        """
        List all tables and views in the specified dataset.
        
        Args:
            dataset_id: The ID of the dataset to list tables from.
            
        Returns:
            List of dictionaries containing table information.
        """
        try:
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            if not tables:
                print(f"No tables found in dataset {dataset_id}")
                return []
                
            result = []
            for table in tables:
                # Get full table to get the description and type
                full_table = self.client.get_table(table)
                table_type = "VIEW" if full_table.table_type == "VIEW" else "TABLE"
                
                result.append({
                    "Table ID": table.table_id,
                    "Type": table_type,
                    "Description": full_table.description or ""
                })
                
            return result
        except GoogleCloudError as e:
            print(f"Error listing tables in dataset {dataset_id}: {e}")
            sys.exit(1)
            
    def get_schema(self, dataset_id: str, table_id: str) -> List[Dict[str, str]]:
        """
        Get the schema of a specified table or view.
        
        Args:
            dataset_id: The ID of the dataset.
            table_id: The ID of the table or view.
            
        Returns:
            List of dictionaries containing column information.
        """
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            result = []
            for field in table.schema:
                result.append({
                    "Column Name": field.name,
                    "Data Type": field.field_type,
                    "Nullable": "YES" if field.is_nullable else "NO",
                    "Description": field.description or ""
                })
                
            return result
        except GoogleCloudError as e:
            print(f"Error getting schema for {dataset_id}.{table_id}: {e}")
            sys.exit(1)
            
    def is_readonly_query(self, query: str) -> bool:
        """
        Check if a query is read-only (no data modification).
        
        Args:
            query: The SQL query to check.
            
        Returns:
            True if the query is read-only, False otherwise.
        """
        for pattern in NON_READONLY_PATTERNS:
            if pattern.search(query):
                return False
        return True
            
    def run_query(self, query: str, dry_run: bool = False) -> Union[List[Dict[str, Any]], str]:
        """
        Run a read-only SQL query and return results (limited to 5 rows).
        
        Args:
            query: The SQL query to run.
            dry_run: If True, validate the query without running it.
            
        Returns:
            List of dictionaries containing query results, or error message.
        """
        # Check if query is read-only
        if not self.is_readonly_query(query):
            return "Error: Only read-only queries are allowed. Data modification operations detected."
            
        job_config = bigquery.QueryJobConfig(dry_run=dry_run)
        
        try:
            # Start the query
            query_job = self.client.query(query, job_config=job_config)
            
            if dry_run:
                # For dry runs, just return the estimated bytes processed
                bytes_processed = query_job.total_bytes_processed
                return f"Query validation successful. Estimated bytes processed: {bytes_processed} bytes."
                
            # Wait for the query to complete
            results = query_job.result(max_results=5)
            
            # Convert to list of dictionaries
            result_list = []
            schema = results.schema
            field_names = [field.name for field in schema]
            
            row_count = 0
            for row in results:
                row_dict = {}
                for i, field_name in enumerate(field_names):
                    row_dict[field_name] = row[i]
                result_list.append(row_dict)
                row_count += 1
                if row_count >= 5:
                    break
                    
            return result_list
        except GoogleCloudError as e:
            return f"Error executing query: {e}"

def format_output(data: List[Dict[str, Any]], format_type: str = "table") -> str:
    """
    Format the output data as a table.
    
    Args:
        data: List of dictionaries containing the data to format.
        format_type: Output format (only "table" is currently supported).
        
    Returns:
        Formatted string representation of the data.
    """
    if not data:
        return "No data to display."
        
    if isinstance(data, str):
        return data
        
    if format_type == "table":
        return tabulate(data, headers="keys", tablefmt="pipe")
    else:
        return str(data)

def main():
    """Main entry point for the BigQuery tool."""
    parser = argparse.ArgumentParser(
        description="Google BigQuery CLI Tool - Interact with BigQuery using a service account",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List datasets command
    list_datasets_parser = subparsers.add_parser(
        "list-datasets", help="List all datasets in the project"
    )
    list_datasets_parser.add_argument(
        "--project", help="GCP project ID (uses default from service account if not provided)"
    )
    
    # List tables command
    list_tables_parser = subparsers.add_parser(
        "list-tables", help="List all tables in a dataset"
    )
    list_tables_parser.add_argument("dataset_id", help="Dataset ID")
    list_tables_parser.add_argument(
        "--project", help="GCP project ID (uses default from service account if not provided)"
    )
    
    # Get schema command
    get_schema_parser = subparsers.add_parser(
        "get-schema", help="Get the schema of a table or view"
    )
    get_schema_parser.add_argument("dataset_id", help="Dataset ID")
    get_schema_parser.add_argument("table_id", help="Table or view ID")
    get_schema_parser.add_argument(
        "--project", help="GCP project ID (uses default from service account if not provided)"
    )
    
    # Run query command
    run_query_parser = subparsers.add_parser(
        "run-query", help="Run a read-only SQL query"
    )
    run_query_parser.add_argument("query", help="SQL query to execute")
    run_query_parser.add_argument(
        "--project", help="GCP project ID (uses default from service account if not provided)"
    )
    run_query_parser.add_argument(
        "--dry-run", action="store_true", help="Validate the query without executing it"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # Check if GOOGLE_APPLICATION_CREDENTIALS is set
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        print("Set it in your .env file to the path of your service account key file:")
        print("GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key-file.json")
        print("Continuing with default authentication...")
    else:
        print(f"Using service account key: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}", file=sys.stderr)
        
    # Initialize BigQuery client
    bq = BigQueryTool(project_id=args.project if hasattr(args, "project") else None)
    
    # Execute the requested command
    if args.command == "list-datasets":
        result = bq.list_datasets()
        print(format_output(result))
    elif args.command == "list-tables":
        result = bq.list_tables(args.dataset_id)
        print(format_output(result))
    elif args.command == "get-schema":
        result = bq.get_schema(args.dataset_id, args.table_id)
        print(format_output(result))
    elif args.command == "run-query":
        result = bq.run_query(args.query, args.dry_run)
        print(format_output(result))

if __name__ == "__main__":
    main() 