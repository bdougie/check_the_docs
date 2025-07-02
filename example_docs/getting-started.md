# Getting Started with Check Docs

Welcome to Check Docs! This guide will help you get up and running with document indexing and analysis.

## Installation

First, ensure you have Python 3.9+ and uv installed:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repository-url>
cd check_docs
uv sync
```

## Basic Usage

### Starting the Server

```bash
uv run python server.py
```

### Indexing Your First Documents

Once connected through Claude Desktop, you can index documentation:

```
Index the documentation in /path/to/docs
```

### Searching Documentation

Search for specific topics:

```
Search for "authentication implementation"
```

## Configuration

The server uses ChromaDB for vector storage and Ollama for embeddings. Make sure Ollama is running with the nomic-embed-text model.

## Next Steps

- Learn about [advanced features](./advanced-features.md)
- Set up [Git integration](./git-integration.md)
- Configure [custom embeddings](./embeddings.md)