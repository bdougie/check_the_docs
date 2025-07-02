# Advanced Features

This guide covers advanced features of the Check Docs server.

## Custom Chunking Strategies

The default chunking strategy splits documents into 2000-character chunks with 200-character overlap. You can customize this by modifying the `DocumentProcessor` class.

### Example: Header-Based Chunking

```python
def chunk_by_headers(content: str):
    sections = content.split('\n#')
    return ['#' + section for section in sections if section]
```

## Batch Processing

For large documentation sets, process files in batches to manage memory:

```python
async def batch_index(folder_path: str, batch_size: int = 10):
    files = list(Path(folder_path).rglob("*.md"))
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        await process_batch(batch)
```

## Git Integration

The `check_docs` tool analyzes Git repositories to identify documentation that needs updates.

### Analyzing Specific Branches

```python
suggestions = await check_docs({
    "repo_path": "/path/to/repo",
    "commit_range": "develop..feature/new-api"
})
```

### Custom Code Extensions

Add support for additional file types by modifying the `code_extensions` set in the `check_docs` function.

## Performance Optimization

### Caching Embeddings

ChromaDB automatically caches embeddings, but you can implement additional caching:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text: str):
    return embedding_function(text)
```

### Parallel Processing

Use asyncio for parallel document processing:

```python
async def parallel_index(files: List[Path]):
    tasks = [index_file(file) for file in files]
    await asyncio.gather(*tasks)
```

## Monitoring and Logging

The server uses FastMCP's context for logging:

- `ctx.info()`: Informational messages
- `ctx.warning()`: Warning messages
- `ctx.error()`: Error messages
- `ctx.report_progress()`: Progress updates

## Security Considerations

1. **API Keys**: Store sensitive keys in environment variables
2. **File Access**: Validate file paths before processing
3. **Input Sanitization**: Always validate user inputs
4. **Rate Limiting**: Implement rate limiting for public deployments