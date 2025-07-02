# MCP Server Setup Guide

This guide shows how to configure the Check Docs MCP server with different AI coding assistants.

## Claude Code (Claude Desktop)

Add to your `.mcp.json` file:

```json
{
  "mcpServers": {
    "check_docs": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/path/to/your/check_docs"
    }
  }
}
```

Replace `/path/to/your/check_docs` with your actual project path.

## Continue.dev

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

## Usage

Once configured, you can use the MCP tools:

- `index_documentation`: Index markdown files from a folder
- `search_documents`: Search through indexed documentation
- `check_docs`: Analyze Git changes and suggest doc updates

## Testing the Setup

1. Start your AI assistant
2. Try indexing some docs:
   ```
   Index the documentation in ./example_docs
   ```
3. Search for content:
   ```
   Search docs for "git integration"
   ```

## Troubleshooting

- Ensure `uv` is installed and available in PATH
- Verify the server path is correct
- Check that Python dependencies are installed with `uv sync`
- Make sure Ollama is running for embeddings (default: `http://localhost:11434`)