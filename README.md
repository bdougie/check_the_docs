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

### 2. Start the Server

```bash
# Run the FastMCP server
uv run python server.py
```

The server will start on the default FastMCP port and be ready to accept connections.

### 3. Connect with Claude Desktop

Add the server to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "check-docs": {
      "command": "uv",
      "args": ["run", "python", "/path/to/check_docs/server.py"],
      "cwd": "/path/to/check_docs"
    }
  }
}
```

Restart Claude Desktop to load the server.

## Usage Examples

### Index Documentation

```python
# Index all markdown files in a directory
await index_documentation(
    folder_path="/path/to/docs",
    collection_name="my_project_docs"
)
```

### Search Documentation

```python
# Search for relevant documentation
results = await search_documentation(
    query="how to implement authentication",
    collection_name="my_project_docs",
    n_results=5
)
```

### Analyze Code Changes

```python
# Check which docs need updates based on recent code changes
suggestions = await check_docs({
    "repo_path": "/path/to/repo",
    "since_days": 7  # Check changes from last 7 days
})

# Or check specific commit range
suggestions = await check_docs({
    "repo_path": "/path/to/repo",
    "commit_range": "main..feature-branch"
})
```

## Available Tools

### `index_documentation`
Index markdown documentation from a folder into ChromaDB.

**Parameters:**
- `folder_path` (str): Path to the documentation folder
- `collection_name` (str): Name for the ChromaDB collection (default: "documents")

### `search_documentation`
Search indexed documentation using semantic similarity.

**Parameters:**
- `query` (str): Natural language search query
- `collection_name` (str): Collection to search (default: "documents")
- `n_results` (int): Number of results to return (default: 5)

### `check_docs`
Analyze Git repository changes and suggest documentation updates.

**Parameters:**
- `repo_path` (str): Path to the Git repository
- `commit_range` (str, optional): Specific commit range to analyze
- `since_days` (int, optional): Analyze changes from last N days (default: 7)

### `list_collections`
List all available document collections in ChromaDB.

### `delete_collection`
Delete a specific document collection.

**Parameters:**
- `collection_name` (str): Name of collection to delete

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