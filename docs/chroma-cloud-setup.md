# ChromaDB Cloud Setup Guide

This guide explains how to configure Check The Docs to use ChromaDB Cloud for scalable, persistent vector storage.

## Prerequisites

1. **ChromaDB Cloud Account**: Sign up at [ChromaDB Cloud](https://www.trychroma.com/)
2. **ChromaDB CLI**: Install the ChromaDB CLI for authentication
   ```bash
   pip install chromadb-cli
   ```

## Setup Steps

### Option 1: Using MCP Tools (Recommended)

The easiest way to configure ChromaDB Cloud is through the MCP tools:

```bash
# 1. Configure ChromaDB Cloud and switch to cloud mode
configure_chroma_cloud your-tenant-name your-database-name

# 2. Copy existing local data to cloud (optional)
copy_to_cloud your-tenant-name your-database-name

# 3. Verify cloud connection
chroma_status
```

### Option 2: Using Environment Variables

#### 1. Authenticate with ChromaDB Cloud

```bash
# Login to ChromaDB Cloud
chroma login

# Create a new tenant/database (if needed)
chroma create-tenant your-tenant-name
chroma create-database your-database-name
```

#### 2. Configure Environment Variables

Set the following environment variables to enable ChromaDB Cloud mode:

```bash
export CHROMA_CLOUD_TENANT="your-tenant-name"
export CHROMA_CLOUD_DATABASE="your-database-name"

# Optional: Set API key for programmatic access
export CHROMA_CLOUD_API_KEY="your-api-key"
```

#### 3. Copy Local Data to Cloud

If you have existing local ChromaDB collections, you can copy them to the cloud:

```bash
# Using the built-in copy tool
copy_to_cloud your-tenant-name your-database-name

# Or using ChromaDB CLI
chroma copy --from-local --to-cloud your-tenant-name/your-database-name
```

#### 4. Verify Cloud Connection

Check that the system is using ChromaDB Cloud:

```bash
# Check connection status
chroma_status
```

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CHROMA_CLOUD_TENANT` | Your ChromaDB Cloud tenant name | Yes |
| `CHROMA_CLOUD_DATABASE` | Your ChromaDB Cloud database name | Yes |
| `CHROMA_CLOUD_API_KEY` | API key for programmatic access | No* |

*Required only if not using CLI authentication

### Automatic Fallback

The system automatically falls back to local ChromaDB if:
- Cloud environment variables are not set
- Cloud connection fails
- Authentication is invalid

## Migration Workflow

### From Local to Cloud (Using MCP Tools)

1. **Backup Local Data** (optional):
   ```bash
   cp -r ./chroma_db ./chroma_db_backup
   ```

2. **Configure and Switch to Cloud**:
   ```bash
   configure_chroma_cloud your-tenant your-database
   ```

3. **Copy Collections**:
   ```bash
   copy_to_cloud your-tenant your-database
   ```

4. **Verify Migration**:
   ```bash
   chroma_status
   list_collections
   ```

### From Cloud to Local (Using MCP Tools)

1. **Copy Data from Cloud** (optional):
   ```bash
   copy_from_cloud your-tenant your-database
   ```

2. **Switch to Local**:
   ```bash
   switch_to_local
   ```

3. **Verify Switch**:
   ```bash
   chroma_status
   list_collections
   ```

### Manual Migration (Using Environment Variables)

#### From Local to Cloud

1. **Set Environment Variables**:
   ```bash
   export CHROMA_CLOUD_TENANT="your-tenant"
   export CHROMA_CLOUD_DATABASE="your-database"
   ```

2. **Copy Collections**:
   ```bash
   copy_to_cloud your-tenant your-database
   ```

#### From Cloud to Local

1. **Unset Environment Variables**:
   ```bash
   unset CHROMA_CLOUD_TENANT
   unset CHROMA_CLOUD_DATABASE
   ```

2. **Restart Server**: The system will automatically use local ChromaDB

## Best Practices

### Performance
- Use batch operations for large data uploads
- Monitor collection sizes and optimize chunking strategies
- Consider regional deployment for better latency

### Security
- Use API keys for production deployments
- Rotate API keys regularly
- Monitor access logs

### Cost Management
- Monitor storage usage in ChromaDB Cloud dashboard
- Optimize document chunking to reduce storage costs
- Clean up unused collections regularly

## Troubleshooting

### Common Issues

**Connection Failed**:
```bash
# Check authentication
chroma auth status

# Re-authenticate
chroma login
```

**Collections Not Found**:
```bash
# List available collections
chroma list-collections

# Check tenant/database names
chroma list-tenants
chroma list-databases
```

**Slow Performance**:
- Check network connectivity
- Verify regional settings
- Consider batch size optimization

### Error Messages

| Error | Solution |
|-------|----------|
| "CHROMA_CLOUD_TENANT must be set" | Set required environment variables |
| "Authentication failed" | Run `chroma login` again |
| "Collection already exists" | Use `get_collection()` instead of `create_collection()` |
| "Rate limit exceeded" | Implement retry logic with exponential backoff |

## Advanced Usage

### Multiple Environments

You can configure different environments for development, staging, and production:

```bash
# Development
export CHROMA_CLOUD_TENANT="dev-tenant"
export CHROMA_CLOUD_DATABASE="dev-database"

# Production
export CHROMA_CLOUD_TENANT="prod-tenant"
export CHROMA_CLOUD_DATABASE="prod-database"
```

### Custom Embedding Functions

ChromaDB Cloud supports the same embedding functions as local ChromaDB:

```python
# The system automatically uses Ollama embeddings
# No additional configuration needed
```

### Monitoring and Logging

Check ChromaDB Cloud usage through:
- ChromaDB Cloud dashboard
- Built-in `chroma_status` tool
- Collection metrics via `list_collections`

## Support

For ChromaDB Cloud-specific issues:
- [ChromaDB Cloud Documentation](https://docs.trychroma.com/)
- [ChromaDB Discord Community](https://discord.gg/MMeYNTmh3x)
- [ChromaDB GitHub Issues](https://github.com/chroma-core/chroma/issues)

For Check The Docs integration issues:
- Check server logs for error messages
- Verify environment variable configuration
- Test with local ChromaDB first