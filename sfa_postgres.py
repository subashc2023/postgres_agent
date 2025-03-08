# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "argparse",
#     "dotenv",
#     "litellm",
#     "psycopg2",
#     "psycopg2-binary",
#     "smolagents",
#     "sqlalchemy",
# ]
# ///

# =============================================================================
# Configuration Settings
# =============================================================================

# Database Configuration
POSTGRES_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "postgres",
    "database": "practice",
}
DB_URL = f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}/{POSTGRES_CONFIG['database']}"

# LLM Model Configuration
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "openai/gpt-4o"

# Database Schema Configuration
SYSTEM_SCHEMAS = ['information_schema', 'pg_catalog', 'pg_toast']

# Model Provider Configuration
MODEL_ALIASES = {
    "groq/llama": {"provider": "groq", "model_id": "groq/llama-3.3-70b-versatile"},
    "groq/deepseek": {"provider": "groq", "model_id": "groq/deepseek-r1-distill-llama-70b"},
    "openai/o1-mini": {"provider": "openai", "model_id": "openai/o1-mini"},
    "openai/4o-mini": {"provider": "openai", "model_id": "openai/gpt-4o-mini"},
    "openrouter/4o-mini": {"provider": "openrouter", "model_id": "openrouter/openai/gpt-4o-mini"},
    "openrouter/sonnet": {"provider": "openrouter", "model_id": "openrouter/anthropic/claude-3.5-sonnet"},
}

# =============================================================================
# Code Implementation
# =============================================================================

import os
import argparse
from smolagents import CodeAgent, LiteLLMModel, tool
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment variables
load_dotenv()

# API key mapping
API_KEYS = {
    "groq": os.environ.get("GROQ_API_KEY"),
    "openai": os.environ.get("OPENAI_API_KEY"),
    "openrouter": os.environ.get("OPENROUTER_API_KEY"),
}

# Set up PostgreSQL connection
engine = create_engine(DB_URL)

# Get database schema information
inspector = inspect(engine)
table_descriptions = ""

# Define system schemas to exclude
SYSTEM_SCHEMAS = ['information_schema', 'pg_catalog', 'pg_toast']

# Modify how schemas are collected
schemas = [schema for schema in inspector.get_schema_names() 
           if schema not in SYSTEM_SCHEMAS]

# Only iterate through tables in non-system schemas
for schema in schemas:
    for table_name in inspector.get_table_names(schema=schema):
        columns_info = [(col["name"], col["type"]) 
                        for col in inspector.get_columns(table_name, schema=schema)]
        table_description = f"Table '{schema}.{table_name}':\n"
        table_description += "Columns:\n" + "\n".join(
            [f"  - {name}: {col_type}" for name, col_type in columns_info])
        table_descriptions += "\n\n" + table_description

# Create the tool docstring first
tool_docstring = f"""
Allows you to perform SQL queries on the PostgreSQL database named 'practice'.
Returns a string representation of the result.

Important: Only query user tables in the 'public' schema. DO NOT query internal PostgreSQL schemas 
(information_schema, pg_catalog, pg_toast) unless explicitly requested for administration purposes.

The relevant database schema is as follows:
{table_descriptions}

Args:
    query: The query to perform. This should be correct SQL.
"""

# Define the SQL tool with explicit docstring
@tool
def sql_engine(query: str) -> str:
    """
    Allows you to perform SQL queries on the PostgreSQL database.
    Returns a string representation of the result.
    
    Important: Only query user tables in the 'public' schema. DO NOT query internal PostgreSQL schemas 
    (information_schema, pg_catalog, pg_toast) unless explicitly requested for administration purposes.
    
    The relevant database schema is as follows:
    {table_descriptions}

    Args:
        query: The query to perform. This should be correct SQL.
    """
    # Filter queries that try to access system schemas
    system_schemas = ['information_schema', 'pg_catalog', 'pg_toast']
    schema_filter = " AND ".join([f"table_schema != '{schema}'" for schema in system_schemas])
    
    # Replace common schema/table listing queries with filtered versions
    if "information_schema.schemata" in query and "schema_name" in query:
        query = f"SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');"
    
    if "information_schema.tables" in query:
        if "WHERE" in query.upper():
            query = query.replace("WHERE", f"WHERE {schema_filter} AND")
        else:
            query = query.replace(";", f" WHERE {schema_filter};")
    
    # Execute the query
    output = ""
    try:
        with engine.connect() as con:
            rows = con.execute(text(query))
            for row in rows:
                output += "\n" + str(row)
            
            if not output:
                output = "Query executed successfully, but returned no results."
    except Exception as e:
        output = f"Error executing query: {str(e)}"
    
    return output

def get_model(alias=None, provider=None, model_id=None):
    if alias and alias in MODEL_ALIASES:
        config = MODEL_ALIASES[alias]
        provider = config["provider"]
        model_id = config["model_id"]
    elif not (provider and model_id):
        provider = DEFAULT_PROVIDER
        model_id = DEFAULT_MODEL
        print(f"Using default model: {model_id}")
    api_key = API_KEYS.get(provider)
    if not api_key:
        raise ValueError(f"API key for provider '{provider}' not found in environment variables")
    return LiteLLMModel(model_id=model_id, api_key=api_key)

def run_text_to_sql_query(query, agent):
    print(f"Processing query: {query}")
    result = agent.run(query)
    print("\nQuery completed.\n")
    return result

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run text-to-SQL queries with different LLM providers")
    parser.add_argument("query", nargs="?", default="List all schemas and tables in the database.",
                        help="Natural language query to execute")
    parser.add_argument("-a", "--alias", choices=list(MODEL_ALIASES.keys()),
                        help=f"Model alias to use (one of: {', '.join(MODEL_ALIASES.keys())})")
    parser.add_argument("-p", "--provider", choices=["groq", "openai", "openrouter"],
                        help="Provider to use if not using an alias")
    parser.add_argument("-m", "--model", help="Model ID if not using an alias")
    return parser.parse_args()

def main():
    args = parse_arguments()
    model = get_model(alias=args.alias, provider=args.provider, model_id=args.model)
    agent = CodeAgent(
        tools=[sql_engine],
        model=model, 
        additional_authorized_imports=[
            'random',
            'unicodedata', 
            'time', 
            'statistics', 
            'queue', 
            'datetime', 
            'itertools', 
            'collections', 
            'math', 
            'stat', 
            're'])
    result = run_text_to_sql_query(args.query, agent)
    print(result)

if __name__ == "__main__":
    main()