# Available Tools

## `index_documentation`
Index markdown documentation from a folder into ChromaDB.

**Parameters:**
- `folder_path` (str): Path to the documentation folder
- `collection_name` (str): Name for the ChromaDB collection (default: "documents")

## `search_documentation`
Search indexed documentation using semantic similarity.

**Parameters:**
- `query` (str): Natural language search query
- `collection_name` (str): Collection to search (default: "documents")
- `n_results` (int): Number of results to return (default: 5)

## `check_the_docs`
Analyze Git repository changes and suggest documentation updates.

**Parameters:**
- `repo_path` (str): Path to the Git repository
- `commit_range` (str, optional): Specific commit range to analyze
- `since_days` (int, optional): Analyze changes from last N days (default: 7)

## `list_collections`
List all available document collections in ChromaDB.

## `delete_collection`
Delete a specific document collection.

**Parameters:**
- `collection_name` (str): Name of collection to delete

## `index_git_diff`
Index git diff content in ChromaDB for enhanced documentation analysis.

**Parameters:**
- `repo_path` (str): Path to the Git repository
- `commit_range` (str, optional): Specific commit range to analyze (e.g., "abc123..def456")
- `since_days` (int, optional): Analyze changes from last N days (default: 7)
- `collection_name` (str, optional): ChromaDB collection name (default: "git_changes")

**Description:**
This tool captures actual git diff content, analyzes the significance of changes, and indexes them in ChromaDB. It identifies:
- Function/class additions and removals
- API endpoint changes
- Configuration modifications
- Significant code changes that require documentation updates

The indexed diff content can then be cross-referenced with existing documentation to identify gaps and suggest updates.

## `chroma_status`
Check ChromaDB connection status and configuration.

**Description:**
Returns information about the current ChromaDB client including:
- Client type (local or cloud)
- Version information
- Available collections
- Authentication status
- Connection details

## `copy_to_cloud`
Copy local ChromaDB collections to ChromaDB Cloud.

**Parameters:**
- `tenant` (str): ChromaDB Cloud tenant name
- `database` (str): ChromaDB Cloud database name
- `collection_names` (List[str], optional): Specific collections to copy (default: all collections)

**Description:**
Copies all or specified collections from local ChromaDB to ChromaDB Cloud. Handles batch uploads for large collections and provides progress updates during the copy process.

## `configure_chroma_cloud`
Configure ChromaDB Cloud settings and switch from local to cloud mode.

**Parameters:**
- `tenant` (str): ChromaDB Cloud tenant name
- `database` (str): ChromaDB Cloud database name
- `api_key` (str, optional): ChromaDB Cloud API key for programmatic access

**Description:**
Dynamically configures ChromaDB Cloud settings, sets environment variables, and reinitializes the ChromaDB manager to use cloud mode. Tests the connection and provides feedback on success or failure.

## `switch_to_local`
Switch from ChromaDB Cloud to local ChromaDB.

**Parameters:**
- `local_path` (str, optional): Path to local ChromaDB storage (default: "./chroma_db")

**Description:**
Switches from ChromaDB Cloud back to local ChromaDB, clears cloud environment variables, and reinitializes the ChromaDB manager with local settings.

## `copy_from_cloud`
Copy ChromaDB Cloud collections to local ChromaDB.

**Parameters:**
- `tenant` (str): ChromaDB Cloud tenant name
- `database` (str): ChromaDB Cloud database name
- `collection_names` (List[str], optional): Specific collections to copy (default: all collections)
- `local_path` (str, optional): Path to local ChromaDB storage (default: "./chroma_db")

**Description:**
Copies collections from ChromaDB Cloud to local ChromaDB storage. Useful for backing up cloud data locally or migrating from cloud to local setup.