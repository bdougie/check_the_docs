import asyncio
import chromadb
from fastmcp import FastMCP, Context
from pathlib import Path
import git
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import json

class DocumentInput(BaseModel):
    content: str
    file_path: str
    metadata: Optional[Dict] = None

class CheckDocsRequest(BaseModel):
    repo_path: str
    commit_range: Optional[str] = None
    since_days: Optional[int] = 7

# Initialize FastMCP server
mcp = FastMCP("ChromaDB Document Server")

# ChromaDB manager
class ChromaDBManager:
    def __init__(self, persist_path="./chroma_db"):
        self.persist_path = persist_path
        self.client = chromadb.PersistentClient(path=persist_path)
        self.ef = self._get_ollama_embedding_function()
    
    def _get_ollama_embedding_function(self):
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
        return OllamaEmbeddingFunction(
            model_name="nomic-embed-text",
            url="http://localhost:11434/api/embeddings"
        )
    
    def get_or_create_collection(self, name="documents"):
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
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
        
        # Simple chunking implementation
        chunks = self._chunk_text(prefixed_content)
        
        return [
            {
                "content": chunk,
                "metadata": {
                    "file_path": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "indexed_at": datetime.now().isoformat()
                }
            }
            for i, chunk in enumerate(chunks)
        ]
    
    def _chunk_text(self, text: str) -> List[str]:
        """Simple text chunking with overlap"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Try to find a good breaking point
            if end < text_length:
                # Look for paragraph break
                break_point = text.rfind('\n\n', start, end)
                if break_point == -1:
                    # Look for sentence break
                    break_point = text.rfind('. ', start, end)
                if break_point == -1:
                    # Look for any newline
                    break_point = text.rfind('\n', start, end)
                if break_point != -1 and break_point > start:
                    end = break_point + 1
            
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
            
            # Avoid infinite loop
            if start >= text_length - 1:
                break
        
        return chunks

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
            try:
                content = md_file.read_text(encoding='utf-8')
                chunks = doc_processor.process_markdown(
                    content, 
                    str(md_file.relative_to(docs_path))
                )
                
                # Generate unique IDs for each chunk
                chunk_ids = [f"{md_file.stem}_{j}_{hash(chunk['content'])}" for j, chunk in enumerate(chunks)]
                
                # Add to ChromaDB
                collection.add(
                    documents=[c["content"] for c in chunks],
                    metadatas=[c["metadata"] for c in chunks],
                    ids=chunk_ids
                )
                
                total_chunks += len(chunks)
                await ctx.report_progress(i + 1, len(md_files))
            except Exception as e:
                await ctx.warning(f"Failed to index {md_file}: {str(e)}")
                continue
        
        await ctx.info(f"Indexed {total_chunks} chunks from {len(md_files)} files")
        return f"Successfully indexed {len(md_files)} documents with {total_chunks} chunks"
        
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
            # Get diff for specific commit range
            diffs = repo.git.diff(request.commit_range, name_only=True).split('\n')
        else:
            # Get changes from last N days
            since_date = f"--since={request.since_days}.days.ago"
            commits = list(repo.iter_commits('HEAD', since=since_date))
            
            changed_files = set()
            for commit in commits:
                for item in commit.stats.files:
                    changed_files.add(item)
            
            diffs = list(changed_files)
        
        # Filter for code files
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs'}
        code_changes = [
            f for f in diffs 
            if any(f.endswith(ext) for ext in code_extensions) and f
        ]
        
        await ctx.info(f"Found {len(code_changes)} code changes")
        
        # Search for related documentation
        suggestions = []
        for code_file in code_changes:
            # Extract meaningful terms from file path
            file_parts = Path(code_file).parts
            file_name = Path(code_file).stem
            
            # Query ChromaDB for related docs
            query = f"search_query: {code_file} {file_name} implementation details functions classes methods"
            try:
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
                            'suggestion': f"Update documentation for changes in {code_file}",
                            'doc_preview': doc[:200] + "..." if len(doc) > 200 else doc
                        })
            except Exception as e:
                await ctx.warning(f"Failed to query for {code_file}: {str(e)}")
                continue
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Group suggestions by documentation file
        doc_groups = {}
        for suggestion in suggestions:
            doc_file = suggestion['related_doc']
            if doc_file not in doc_groups:
                doc_groups[doc_file] = []
            doc_groups[doc_file].append(suggestion)
        
        return {
            'total_code_changes': len(code_changes),
            'documentation_suggestions': suggestions[:10],  # Top 10
            'affected_docs': list(doc_groups.keys()),
            'summary': f"Found {len(suggestions)} documentation items that may need updates across {len(doc_groups)} files"
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
        if results['ids'][0]:
            for i in range(len(results['ids'][0])):
                # Clean up the document content by removing the prefix
                doc_content = results['documents'][0][i]
                if doc_content.startswith("search_document: "):
                    doc_content = doc_content[len("search_document: "):]
                
                formatted_results.append({
                    'document': doc_content[:500] + "..." if len(doc_content) > 500 else doc_content,
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

@mcp.tool()
async def list_collections(ctx: Context = None) -> List[str]:
    """List all available document collections"""
    try:
        collections = chroma_manager.client.list_collections()
        collection_names = [col.name for col in collections]
        await ctx.info(f"Found {len(collection_names)} collections")
        return collection_names
    except Exception as e:
        await ctx.error(f"Failed to list collections: {str(e)}")
        raise

@mcp.tool()
async def delete_collection(
    collection_name: str,
    ctx: Context = None
) -> str:
    """Delete a document collection"""
    try:
        chroma_manager.client.delete_collection(name=collection_name)
        await ctx.info(f"Deleted collection: {collection_name}")
        return f"Successfully deleted collection: {collection_name}"
    except Exception as e:
        await ctx.error(f"Failed to delete collection: {str(e)}")
        raise

def main():
    """Main entry point for the server"""
    mcp.run()

if __name__ == "__main__":
    main()