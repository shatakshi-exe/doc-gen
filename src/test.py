import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env in the current folder
load_dotenv(dotenv_path='.env')

# Chat endpoint variables
RESOURCE = os.getenv('AZURE_OPENAI_RESOURCE')
MODEL = os.getenv('AZURE_OPENAI_MODEL')
KEY = os.getenv('AZURE_OPENAI_KEY')
MODEL_NAME = os.getenv('AZURE_OPENAI_MODEL_NAME')
ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')

# Embedding endpoint variables
EMBEDDING_NAME = os.getenv('AZURE_OPENAI_EMBEDDING_NAME')
EMBEDDING_ENDPOINT = os.getenv('AZURE_OPENAI_EMBEDDING_ENDPOINT')
EMBEDDING_KEY = os.getenv('AZURE_OPENAI_EMBEDDING_KEY')

# Test chat endpoint
print('Testing Azure OpenAI Chat Endpoint (v2)...')
chat_url = f"{ENDPOINT}/openai/deployments/{MODEL_NAME}/chat/completions?api-version=2024-02-15-preview"
chat_headers = {
    'Content-Type': 'application/json',
    'api-key': KEY
}
chat_payload = {
    'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Hello!'}
    ],
    'max_tokens': 50
}
try:
    chat_response = requests.post(chat_url, headers=chat_headers, json=chat_payload)
    print('Chat Endpoint Response:', chat_response.status_code)
    print(chat_response.json())
except Exception as e:
    print('Chat Endpoint Error:', e)

# Test embedding endpoint
print('\nTesting Azure OpenAI Embedding Endpoint (v2)...')
embedding_url = f"{EMBEDDING_ENDPOINT}/openai/deployments/{EMBEDDING_NAME}/embeddings?api-version=2023-05-15"
embedding_headers = {
    'Content-Type': 'application/json',
    'api-key': EMBEDDING_KEY
}
embedding_payload = {
    'input': ['This is a test sentence for embedding.']
}
try:
    embedding_response = requests.post(embedding_url, headers=embedding_headers, json=embedding_payload)
    print('Embedding Endpoint Response:', embedding_response.status_code)
    print(embedding_response.json())
except Exception as e:
    print('Embedding Endpoint Error:', e)
 