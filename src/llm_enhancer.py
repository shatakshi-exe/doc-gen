#!/usr/bin/env python3
"""LLM node to enhance and analyze query results with insights and summaries using LangChain."""

import os
import json
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.chat_models import AzureChatOpenAI

# Load environment variables
load_dotenv()

def llm_enhancer(question: str, cosmos_data: dict, search_results: str = None) -> str:
    """
    Enhance query results with LLM-powered analysis, insights, and natural language summaries using LangChain.
    
    Args:
        question: Original user question
        cosmos_data: Structured data from Cosmos DB.
        search_results: Optional results from Azure AI Search.
        
    Returns:
        Enhanced analysis with insights, summaries, and recommendations.
    """
    try:
        # Initialize Azure OpenAI client using LangChain
        llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            temperature=0.7,
            max_tokens=1000
        )
        
        # Build the system prompt
        system_prompt = """You are an AI assistant integrated into a document generation application.
        
        Your role is to:
        1. Analyze structured data from Cosmos DB and Azure AI Search.
        2. Format the data into a professional report with the following structure:
           OPCO QUARTER YEAR
           - Topic 1 (EU Common Questions) {majority and minority sentiment analysis for the topic}
           - Each of the 4 questions under Topic 1 {majority and minority sentiment analysis for each question}
           - Topic 2
           - Questions under Topic 2
           - Topic 3
           - Questions under Topic 3
        3. Provide actionable insights and summaries for each topic and question.
        
        Always ensure your responses are accurate and aligned with the application's goals."""
        
        # Build the user message with context
        user_message = f"""
        User Question: {question}
        
        Cosmos DB Data:
        {json.dumps(cosmos_data, indent=2)}
        
        AI Search Results:
        {search_results if search_results else "No AI Search results available."}
        
        Please generate the report in the specified format and include actionable insights.
        """
        
        # Create LangChain prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(user_message)
        ])
        
        # Generate enhanced response
        response = llm(prompt.format_prompt().to_messages())
        enhanced_analysis = response.content.strip()
        
        return enhanced_analysis
    except Exception as e:
        error_message = f"Error in LLM enhancement: {str(e)}"
        print(error_message)
        return f"Error generating enhanced analysis: {error_message}"
