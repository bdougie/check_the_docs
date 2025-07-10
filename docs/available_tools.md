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