# Postgres Agent

Uses SmolAgents to interact with a Postgres DB. Incredibly fast with Groq's models, and quite intelligent at extracting information with Anthropics Claude models(Accessed here through Openrouter so it will cost ~10% more).

## Prerequisites
- Python 3.8 or higher
- uv package manager
- PostgreSQL database

## Running the Project

To install UV:

```bash
pip install uv
```

To run the agent:

```bash
uv run sfa_postgres.py
```

## Command Line Arguments

The tool supports several command line arguments to customize the LLM model used for queries:

```bash
uv run sfa_postgres.py [query] [-a ALIAS] [-p PROVIDER] [-m MODEL]
```

Arguments:
- `query`: Natural language query to execute (optional, defaults to listing schemas and tables)
- `-a, --alias`: Use a predefined model alias. Available aliases:
  - `groq/llama`: Groq's Llama-3.3-70b
  - `groq/deepseek`: Groq's DeepSeek R1
  - `openai/o1-mini`: OpenAI's O1-mini model
  - `openai/4o-mini`: OpenAI's GPT-4o-mini
  - `openrouter/4o-mini`: OpenRouter's GPT-4o-mini
  - `openrouter/sonnet`: OpenRouter's Claude 3.5 Sonnet
- `-p, --provider`: Specify provider directly (groq, openai, or openrouter)
- `-m, --model`: Specify model ID directly when using provider

Examples:

```bash
# Use default model
uv run sfa_postgres.py "Show all users in the database"

# Use specific alias
uv run sfa_postgres.py -a groq/llama "List all tables"

# Use specific provider and model
uv run sfa_postgres.py -p openai -m gpt-4 "Count records in users table"
```
