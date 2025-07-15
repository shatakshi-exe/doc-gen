#!/usr/bin/env python3
"""Execute SQL queries against Azure Cosmos DB and return results."""

import os
import json
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

# Load environment variables when running locally
load_dotenv()

def cosmos_query_runner(sql_query: str) -> str:
    """
    Execute SQL query against Cosmos DB and return results.
    
    Args:
        sql_query: SQL query string to execute
        
    Returns:
        JSON string containing query results or error message
    """
    try:
        # Initialize Cosmos client
        client = CosmosClient(
            url=os.getenv('COSMOS_URI'),
            credential=os.getenv('COSMOS_KEY')
        )
        
        # Get database and container references
        database = client.get_database_client(os.getenv('COSMOS_DB'))
        container = database.get_container_client(os.getenv('COSMOS_CONTAINER'))
        
        # Execute query
        print(f"Executing query: {sql_query}")
        
        # Enable aggregate queries 
        items = list(container.query_items(
            query=sql_query,
            enable_cross_partition_query=True,
            populate_query_metrics=True,
            max_integrated_cache_staleness_in_ms=0
        ))
        
        # Format results
        if not items:
            return json.dumps({
                "status": "success",
                "message": "Query executed successfully but returned no results",
                "count": 0,
                "results": []
            }, indent=2)
        
        # For aggregation queries that return a single value
        if len(items) == 1 and isinstance(items[0], dict):
            # Check if it's an aggregation result
            keys = list(items[0].keys())
            if len(keys) == 1 and keys[0].startswith('$'):
                return json.dumps({
                    "status": "success",
                    "message": "Query executed successfully",
                    "count": 1,
                    "value": items[0][keys[0]],
                    "results": items
                }, indent=2)
        
        # For regular queries
        return json.dumps({
            "status": "success",
            "message": f"Query returned {len(items)} results",
            "count": len(items),
            "results": items[:100]  # Limit to first 100 results
        }, indent=2)
        
    except Exception as e:
        error_message = f"Error executing query: {str(e)}"
        print(error_message)
        
        return json.dumps({
            "status": "error",
            "message": error_message,
            "query": sql_query
        }, indent=2)

def format_cosmos_results(raw_results: str) -> dict:
    """
    Format raw Cosmos DB results into structured data for report generation.
    
    Args:
        raw_results: JSON string containing raw query results from Cosmos DB.
        
    Returns:
        Structured data as a dictionary.
    """
    try:
        results = json.loads(raw_results)
        if results.get("status") != "success":
            return {"error": results.get("message", "Unknown error")}
        
        formatted_results = {}
        for item in results.get("results", []):
            topic = item.get("topic", "Unknown Topic")
            if topic not in formatted_results:
                formatted_results[topic] = {"questions": []}
            
            formatted_results[topic]["questions"].append({
                "question": item.get("question", "Unknown Question"),
                "sentiment_majority": item.get("sentiment_majority", "Unknown"),
                "sentiment_minority": item.get("sentiment_minority", "Unknown")
            })
        
        return formatted_results
    except Exception as e:
        return {"error": f"Error formatting Cosmos DB results: {str(e)}"}
    
# For local testing
# if __name__ == "__main__":
#     test_queries = [
#         "SELECT COUNT(1) FROM c WHERE c.opco = 'ComEd' AND c.engagement_quarter = 'Q1' AND c.engagement_year = '2025'",
#         "SELECT TOP 5 c.opco, c.engagement_quarter, c.engagement_year FROM c ORDER BY c.engagement_year DESC",
#         "SELECT AVG(c.revenue) FROM c WHERE c.opco = 'PECO' AND c.engagement_quarter = 'Q3' AND c.engagement_year = '2024'"
#     ]
    
#     for query in test_queries:
#         print(f"Query: {query}")
#         result = cosmos_query_runner(query)
#         print(f"Result: {result}")
#         print("-" * 80)
