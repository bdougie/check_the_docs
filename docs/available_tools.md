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

## `check_docs`
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