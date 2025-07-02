# Building a FastMCP Python Server with ChromaDB for Document Indexing and Embedding

## FastMCP server implementation fundamentals

FastMCP 2.0 provides a high-level, Pythonic framework for building Model Context Protocol servers that can seamlessly integrate with vector databases for semantic search and document management. The framework uses decorators for defining tools and resources, making it ideal for document indexing services.

**Key architectural components:**
- **Tools** (`@mcp.tool()`) for document operations like indexing, searching, and updating
- **Resources** (`@mcp.resource()`) for data access endpoints and document retrieval
- **Context access** for progress reporting, logging, and server capabilities

**Basic server structure:**
```python
from fastmcp import FastMCP
mcp = FastMCP("Document Indexer Server")

@mcp.tool()
def add_document(content: str, metadata: dict = None) -> str:
    """Add a document to the index"""
    return "Document indexed successfully"

if __name__ == "__main__":
    mcp.run()
```

## ChromaDB integration best practices

ChromaDB emerges as the ideal vector database choice for this use case, offering both embedded and cloud deployment options. The official `chroma-mcp` server provides ready-to-use integration with essential tools like `chroma_create_collection`, `chroma_add_documents`, and `chroma_query_documents`.

**Integration architecture:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│  FastMCP Server │◄──►│   ChromaDB      │
│  (Claude/Continue)│    │                 │    │   Collections   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │  Ollama         │
                       │  Embeddings     │
                       └─────────────────┘
```

**Key implementation patterns:**
- Use persistent ChromaDB client for data retention
- Implement batch processing for large document sets
- Configure appropriate embedding functions
- Handle errors gracefully with context logging

## Ollama embedding model selection

After comprehensive analysis, **nomic-embed-text** emerges as the optimal choice for technical documentation embedding, offering:
- **8,192 token context length** (exceptional for long documents)
- **768 embedding dimensions** (good balance of detail and efficiency)
- **Task-specific prefixes** (`search_document:` for indexing, `search_query:` for retrieval)
- **274MB model size** (efficient resource usage)
- **Superior performance** compared to OpenAI models on MTEB benchmarks

**Implementation with ChromaDB:**
```python
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

ef = OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings"
)

collection = client.create_collection(
    name="tech_docs",
    embedding_function=ef
)
```

## Markdown parsing and chunking strategies

**Optimal chunking parameters:**
- **Chunk size**: 2000-4000 tokens for nomic-embed-text (leveraging long context)
- **Overlap**: 10-20% between chunks for context preservation
- **Splitting strategy**: Respect semantic boundaries (headers, paragraphs, code blocks)

**Recommended libraries:**
- **mistune**: Fastest pure Python implementation (3-5x faster than alternatives)
- **markdown-it-py**: Best for complex transformations with plugin ecosystem
- **LangChain text splitters**: Ideal for integration with RAG systems

**Implementation approach:**
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)
```

## Git diff analysis for documentation updates

The check_docs function should analyze Git diffs to identify documentation requiring updates based on code changes. **GitPython** is recommended for ease of use, while **pygit2** offers better performance for large repositories.

**Core analysis strategies:**
1. **Path-based analysis**: Identify changed code files and corresponding documentation
2. **Content-based analysis**: Use AST parsing to detect function/class changes
3. **Semantic analysis**: Map code changes to relevant documentation sections

**Implementation pattern:**
```python
class DocumentationChecker:
    def check_docs(self, commit_range=None, since_days=None):
        # Extract code changes
        code_changes = self._extract_code_changes(diff_index)
        
        # Find existing documentation
        existing_docs = self._find_existing_documentation()
        
        # Generate suggestions
        suggestions = []
        for change in code_changes:
            change_suggestions = self._analyze_code_change(change, existing_docs)
            suggestions.extend(change_suggestions)
        
        return self._prioritize_suggestions(suggestions)
```

## Complete implementation example

```python
import asyncio
import chromadb
from fastmcp import FastMCP, Context
from pathlib import Path
import git
from typing import List, Dict, Optional
from pydantic import BaseModel

class DocumentInput(BaseModel):
    content: str
    file_path: str
    metadata: Optional[Dict] = None

class CheckDocsRequest(BaseModel):
    repo_path: str
    commit_range: Optional[str] = None
    since_days: Optional[int] = 7

# Initialize FastMCP server
mcp = FastMCP(
    name="ChromaDB Document Server",
    description="Document indexing with Git diff analysis"
)

# ChromaDB manager
class ChromaDBManager:
    def __init__(self, persist_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.ef = self._get_ollama_embedding_function()
    
    def _get_ollama_embedding_function(self):
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
        return OllamaEmbeddingFunction(
            model_name="nomic-embed-text",
            url="http://localhost:11434/api/embeddings"
        )
    
    def get_or_create_collection(self, name="documents"):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.ef
        )

# Document processor
class DocumentProcessor:
    def __init__(self, chunk_size=2000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_markdown(self, content: str, file_path: str):
        # Add task prefix for nomic-embed-text
        prefixed_content = f"search_document: {content}"
        
        # Chunk with LangChain
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = splitter.split_text(prefixed_content)
        return [
            {
                "content": chunk,
                "metadata": {
                    "file_path": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            for i, chunk in enumerate(chunks)
        ]

# Initialize managers
chroma_manager = ChromaDBManager()
doc_processor = DocumentProcessor()

@mcp.tool()
async def index_documentation(
    folder_path: str,
    collection_name: str = "documents",
    ctx: Context = None
) -> str:
    """Index markdown documentation from a folder"""
    try:
        await ctx.info(f"Indexing documentation from {folder_path}")
        
        collection = chroma_manager.get_or_create_collection(collection_name)
        docs_path = Path(folder_path)
        
        if not docs_path.exists():
            raise ValueError(f"Path {folder_path} does not exist")
        
        # Find all markdown files
        md_files = list(docs_path.rglob("*.md"))
        await ctx.info(f"Found {len(md_files)} markdown files")
        
        total_chunks = 0
        for i, md_file in enumerate(md_files):
            content = md_file.read_text(encoding='utf-8')
            chunks = doc_processor.process_markdown(
                content, 
                str(md_file.relative_to(docs_path))
            )
            
            # Add to ChromaDB
            collection.add(
                documents=[c["content"] for c in chunks],
                metadatas=[c["metadata"] for c in chunks],
                ids=[f"{md_file.stem}_{j}" for j in range(len(chunks))]
            )
            
            total_chunks += len(chunks)
            await ctx.report_progress(i + 1, len(md_files))
        
        await ctx.info(f"Indexed {total_chunks} chunks from {len(md_files)} files")
        return f"Successfully indexed {len(md_files)} documents"
        
    except Exception as e:
        await ctx.error(f"Indexing failed: {str(e)}")
        raise

@mcp.tool()
async def check_docs(
    request: CheckDocsRequest,
    ctx: Context = None
) -> Dict:
    """Analyze Git diffs to identify documentation needing updates"""
    try:
        await ctx.info(f"Analyzing repository: {request.repo_path}")
        
        repo = git.Repo(request.repo_path)
        collection = chroma_manager.get_or_create_collection()
        
        # Get diffs
        if request.commit_range:
            diffs = repo.git.diff(request.commit_range, name_only=True).split('\n')
        else:
            # Get changes from last N days
            since_date = f"--since={request.since_days}.days.ago"
            commits = list(repo.iter_commits(since=since_date))
            
            changed_files = set()
            for commit in commits:
                for item in commit.stats.files:
                    changed_files.add(item)
            
            diffs = list(changed_files)
        
        # Filter for code files
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h'}
        code_changes = [
            f for f in diffs 
            if any(f.endswith(ext) for ext in code_extensions)
        ]
        
        await ctx.info(f"Found {len(code_changes)} code changes")
        
        # Search for related documentation
        suggestions = []
        for code_file in code_changes:
            # Query ChromaDB for related docs
            query = f"search_query: {code_file} implementation details functions classes"
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    suggestions.append({
                        'code_file': code_file,
                        'related_doc': results['metadatas'][0][i]['file_path'],
                        'relevance_score': 1 - results['distances'][0][i],
                        'suggestion': f"Update documentation for changes in {code_file}"
                    })
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            'total_code_changes': len(code_changes),
            'documentation_suggestions': suggestions[:10],  # Top 10
            'summary': f"Found {len(suggestions)} documentation items that may need updates"
        }
        
    except Exception as e:
        await ctx.error(f"Analysis failed: {str(e)}")
        raise

@mcp.tool()
async def search_documentation(
    query: str,
    collection_name: str = "documents",
    n_results: int = 5,
    ctx: Context = None
) -> Dict:
    """Search documentation using semantic similarity"""
    try:
        collection = chroma_manager.get_or_create_collection(collection_name)
        
        # Add query prefix for nomic-embed-text
        prefixed_query = f"search_query: {query}"
        
        results = collection.query(
            query_texts=[prefixed_query],
            n_results=n_results
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'relevance_score': 1 - results['distances'][0][i]
            })
        
        return {
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results)
        }
        
    except Exception as e:
        await ctx.error(f"Search failed: {str(e)}")
        raise

if __name__ == "__main__":
    mcp.run()
```

## Architecture recommendations

**Recommended stack:**
- **Language**: Python for better ML/embedding ecosystem
- **Vector DB**: ChromaDB (embedded) for simplicity, Qdrant for scaling
- **Embeddings**: Ollama with nomic-embed-text model
- **Git operations**: GitPython for ease of use
- **Markdown parsing**: mistune for performance

**Key design decisions:**
1. Use task prefixes with nomic-embed-text for optimal retrieval
2. Implement hierarchical chunking preserving document structure
3. Cache embeddings aggressively to avoid recomputation
4. Use AST parsing for accurate code change detection
5. Prioritize documentation suggestions by relevance score

This architecture provides a robust foundation for building a documentation analysis system that automatically identifies when code changes require corresponding documentation updates, leveraging the power of semantic search and modern embedding models.