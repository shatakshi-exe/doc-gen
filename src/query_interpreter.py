#!/usr/bin/env python3
"""Convert natural language questions to Cosmos DB SQL queries using LangChain."""

import os
import json
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.chat_models import AzureChatOpenAI

# Load environment variables when running locally
load_dotenv()

def query_interpreter(question: str, opco_name: str, quarter: str, year: str) -> str:
    """
    Convert natural language question to Cosmos DB SQL query using LangChain.
    
    Args:
        question: Natural language question about data
        opco_name: Name of the operating company to filter
        quarter: Engagement quarter to filter (e.g., "Q1", "Q2")
        year: Engagement year to filter (e.g., "2025")
        
    Returns:
        SQL query string for Cosmos DB
    """
    # Initialize Azure OpenAI client using LangChain
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.1,
        max_tokens=200
    )
    
    # Build dynamic system prompt
    system_prompt = f"""You are a SQL query generator for Azure Cosmos DB. 
Convert natural language questions into valid Cosmos DB SQL queries.

The database schema includes these fields:
- id: string (unique identifier)
- opco: string (operating company name, e.g., "ComEd", "PECO", "BGE", "PHI")
- engagement_quarter: string (quarter, e.g., "Q1", "Q2")
- engagement_year: string (year, e.g., "2025")
- Other relevant fields...

Important Cosmos DB SQL notes:
- Use SELECT * or SELECT specific fields FROM c
- The collection alias is 'c'
- Use WHERE clauses to filter by opco, engagement_quarter, and engagement_year:
  WHERE c.opco = "OpcoName" AND c.engagement_quarter = "Quarter" AND c.engagement_year = "Year"
- For aggregations with numeric fields, use StringToNumber: SELECT VALUE SUM(StringToNumber(c.SomeField))
- All aggregate queries must use VALUE keyword
- CRITICAL: DO NOT use ORDER BY clauses - they cause syntax errors
- CRITICAL: Use TOP N instead of LIMIT for restricting results

Return ONLY the SQL query without any explanation or markdown formatting."""

    # Build user prompt
    user_prompt = f"""Convert this question to a Cosmos DB SQL query:
    Question: {question}
    Opco: {opco_name}
    Engagement Quarter: {quarter}
    Engagement Year: {year}"""

    # Create LangChain prompt template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(user_prompt)
    ])
    
    # Generate SQL query
    response = llm(prompt.format_prompt().to_messages())
    sql_query = response.content.strip()
    
    # Remove any markdown code blocks if present
    if sql_query.startswith("```"):
        sql_query = sql_query.split("\n", 1)[1].rsplit("\n", 1)[0]
    
    return sql_query


# For local testing
if __name__ == "__main__":
    test_questions = [
        "What is the total revenue for ComEd in Q1 2025?",
        "Show me all transactions for PECO in Q3 2024",
        "How many entries exist for BGE in Q4 2023?"
    ]
    
    for q in test_questions:
        print(f"Question: {q}")
        print(f"SQL: {query_interpreter(q, 'ComEd', 'Q1', '2025')}")
        print("-" * 50)