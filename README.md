# Check Docs - FastMCP Document Indexing Server

A FastMCP server that uses ChromaDB for semantic document indexing and Git diff analysis to identify documentation that needs updates when code changes.

## Features

- 📚 **Document Indexing**: Index markdown documentation with semantic search capabilities
- 🔍 **Semantic Search**: Search documentation using natural language queries
- 📝 **Git Diff Analysis**: Automatically identify documentation that needs updates based on code changes
- 🚀 **Fast Embeddings**: Uses Ollama's nomic-embed-text model for high-quality embeddings
- 💾 **Persistent Storage**: ChromaDB for reliable vector storage

## Prerequisites

1. **Python 3.9+**
2. **uv** (Python package manager)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Ollama** with nomic-embed-text model
   ```bash
   # Install Ollama (macOS)
   brew install ollama
   
   # Start Ollama service
   ollama serve
   
   # Pull the embedding model
   ollama pull nomic-embed-text
   ```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd check_docs

# Install dependencies with uv
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### 2. Configure Continue

Create a YAML configuration file at `.continue/mcpServers/mcp-server.yaml`:

```yaml
name: Check Docs MCP server
version: 0.0.1
schema: v1
mcpServers:
  - name: check_docs
    command: uv
    args:
      - --directory
      - /path/to/your/check_docs
      - run
      - python
      - server.py
```

Replace `/path/to/your/check_docs` with your actual project path.

## Usage Examples

### Index Documentation

In Continue Agent, ask to index the example docs:
```
index_docs ./docs # or  path to your docs folder
```

### Search Documentation

Search through indexed documentation:
```
Search docs for "git integration"
```

### Analyze Code Changes

Check which docs need updates based on code changes:
```
Check what documentation needs updating based on recent Git changes
```

### Self-Documentation Check

Use the project on itself to ensure all features are documented:

1. First, index the project's own documentation:
   ```
   index_docs ./
   ```

2. Then check if all code features are covered:
   ```
   Check docs to see if all features in server.py are covered in the documentation
   ```

This will analyze the codebase and suggest any missing documentation for new features or tools.

For detailed information about available MCP tools, see [available_tools.md](available_tools.md).

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest
```

### Project Structure

```
check_docs/
├── server.py          # Main FastMCP server implementation
├── pyproject.toml     # Project configuration
├── README.md          # This file
├── example.md         # Implementation guide
├── chroma_db/         # ChromaDB storage (auto-created)
└── example_docs/      # Example documentation (optional)
```

### Environment Variables

- `OLLAMA_HOST`: Ollama API endpoint (default: http://localhost:11434)
- `CHROMA_DB_PATH`: ChromaDB storage path (default: ./chroma_db)

## Architecture

The server uses:
- **FastMCP** for the MCP protocol implementation
- **ChromaDB** for vector storage and similarity search
- **Ollama** with nomic-embed-text for generating embeddings
- **GitPython** for repository analysis
- **Pydantic** for request/response validation

## Troubleshooting

### Ollama Connection Error
If you see "connection refused" errors:
```bash
# Check if Ollama is running
ollama list

# Start Ollama if needed
ollama serve
```

### ChromaDB Persistence
The database is stored in `./chroma_db` by default. To reset:
```bash
rm -rf chroma_db/
```

### Memory Issues
For large documentation sets, you may need to:
- Increase chunk size to reduce total chunks
- Process files in batches
- Use a cloud ChromaDB instance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests with `uv run pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details