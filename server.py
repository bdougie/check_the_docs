import asyncio
import chromadb
from fastmcp import FastMCP, Context
from pathlib import Path
import git
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import re

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

# Helper functions for diff analysis
def _analyze_diff_significance(added_lines: List[str], removed_lines: List[str], file_path: str) -> Dict:
    """Analyze if diff changes are significant enough to require documentation updates"""
    
    # Keywords that indicate significant changes requiring documentation
    significant_keywords = {
        'function', 'def', 'class', 'interface', 'api', 'endpoint', 'route', 
        'export', 'import', 'async', 'await', 'public', 'private', 'protected',
        'config', 'settings', 'env', 'param', 'return', 'throw', 'error',
        'deprecated', 'todo', 'fixme', 'hack', 'note', 'warning'
    }
    
    # File types that are more likely to need documentation
    high_priority_files = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs'}
    
    added_text = ' '.join(added_lines).lower()
    removed_text = ' '.join(removed_lines).lower()
    
    # Check for significant keywords
    added_keywords = [kw for kw in significant_keywords if kw in added_text]
    removed_keywords = [kw for kw in significant_keywords if kw in removed_text]
    
    # Check for new function/class definitions
    new_functions = len(re.findall(r'^\s*def\s+\w+|^\s*function\s+\w+|^\s*class\s+\w+', '\n'.join(added_lines), re.MULTILINE))
    removed_functions = len(re.findall(r'^\s*def\s+\w+|^\s*function\s+\w+|^\s*class\s+\w+', '\n'.join(removed_lines), re.MULTILINE))
    
    # Check for API changes (routes, endpoints)
    api_changes = bool(re.search(r'@app\.|@router\.|@route|\.route\(|\.get\(|\.post\(|\.put\(|\.delete\(', added_text))
    
    # Check for configuration changes
    config_changes = bool(re.search(r'config|settings|env|environment', added_text))
    
    # Calculate significance score
    significance_score = 0
    reasons = []
    
    if new_functions > 0:
        significance_score += new_functions * 3
        reasons.append(f"Added {new_functions} new function/class definitions")
    
    if removed_functions > 0:
        significance_score += removed_functions * 2
        reasons.append(f"Removed {removed_functions} function/class definitions")
    
    if api_changes:
        significance_score += 5
        reasons.append("API endpoint changes detected")
    
    if config_changes:
        significance_score += 3
        reasons.append("Configuration changes detected")
    
    if added_keywords:
        significance_score += len(added_keywords)
        reasons.append(f"Significant keywords found: {', '.join(added_keywords[:3])}")
    
    # File type bonus
    if any(file_path.endswith(ext) for ext in high_priority_files):
        significance_score += 1
    
    # Large changes (many lines added/removed)
    if len(added_lines) > 20 or len(removed_lines) > 20:
        significance_score += 2
        reasons.append("Large code changes detected")
    
    requires_documentation = significance_score >= 3
    
    change_type = "minor"
    if significance_score >= 8:
        change_type = "major"
    elif significance_score >= 5:
        change_type = "moderate"
    
    return {
        'requires_documentation': requires_documentation,
        'significance_score': significance_score,
        'reason': '; '.join(reasons) if reasons else "Minor code changes",
        'summary': f"Score: {significance_score}, {len(added_lines)} lines added, {len(removed_lines)} lines removed",
        'change_type': change_type,
        'new_functions': new_functions,
        'api_changes': api_changes,
        'config_changes': config_changes
    }

def _extract_terms_from_diff(added_lines: List[str], removed_lines: List[str], file_path: str) -> List[str]:
    """Extract meaningful terms from diff content for documentation search"""
    
    all_lines = added_lines + removed_lines
    text = ' '.join(all_lines)
    
    # Extract function/class names
    function_names = re.findall(r'(?:def|function|class)\s+(\w+)', text, re.IGNORECASE)
    
    # Extract variable names (simple heuristic)
    variable_names = re.findall(r'^\s*(\w+)\s*=', text, re.MULTILINE)
    
    # Extract API routes
    routes = re.findall(r'["\']([/\w\-\.]+)["\']', text)
    api_routes = [r for r in routes if r.startswith('/') and len(r) > 1]
    
    # Extract import statements
    imports = re.findall(r'(?:import|from)\s+(\w+)', text)
    
    # Extract file name components
    file_parts = Path(file_path).parts
    file_name = Path(file_path).stem
    
    # Combine all terms
    terms = function_names + variable_names + api_routes + imports + [file_name] + list(file_parts)
    
    # Clean and filter terms
    terms = [term.lower() for term in terms if term and len(term) > 2 and term.isalnum()]
    
    # Remove duplicates while preserving order
    unique_terms = []
    seen = set()
    for term in terms:
        if term not in seen:
            unique_terms.append(term)
            seen.add(term)
    
    return unique_terms[:10]  # Return top 10 most relevant terms

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
        
        # Get detailed diff information
        diff_data = []
        if request.commit_range:
            # Get diff for specific commit range with actual content
            diff_output = repo.git.diff(request.commit_range, name_only=True).split('\n')
            diff_content = repo.git.diff(request.commit_range)
            
            # Parse diff content to extract changes
            for file_name in diff_output:
                if file_name.strip():
                    file_diff = repo.git.diff(request.commit_range, file_name)
                    diff_data.append({
                        'file_path': file_name,
                        'diff_content': file_diff,
                        'commit_range': request.commit_range
                    })
        else:
            # Get changes from last N days with diff content
            since_date = f"--since={request.since_days}.days.ago"
            commits = list(repo.iter_commits('HEAD', since=since_date))
            
            changed_files = set()
            for commit in commits:
                for item in commit.stats.files:
                    changed_files.add(item)
            
            # Get diff content for each changed file
            if commits:
                # Compare with the commit before the earliest one
                earliest_commit = commits[-1]
                if earliest_commit.parents:
                    base_commit = earliest_commit.parents[0]
                    for file_name in changed_files:
                        try:
                            file_diff = repo.git.diff(f"{base_commit.hexsha}..HEAD", file_name)
                            diff_data.append({
                                'file_path': file_name,
                                'diff_content': file_diff,
                                'commit_range': f"{base_commit.hexsha[:8]}..HEAD"
                            })
                        except Exception as e:
                            await ctx.warning(f"Failed to get diff for {file_name}: {str(e)}")
        
        # Filter for code files and extract meaningful changes
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php'}
        code_changes = [
            diff for diff in diff_data
            if any(diff['file_path'].endswith(ext) for ext in code_extensions) and diff['file_path']
        ]
        
        await ctx.info(f"Found {len(code_changes)} code changes with diff content")
        
        # Analyze diff content for documentation relevance
        suggestions = []
        docs_path = Path(request.repo_path) / 'docs'
        
        for diff_item in code_changes:
            code_file = diff_item['file_path']
            diff_content = diff_item['diff_content']
            
            # Extract added/modified lines (lines starting with +)
            added_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('+') and not line.startswith('+++')]
            removed_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('-') and not line.startswith('---')]
            
            # Analyze if changes are significant enough to need documentation
            needs_docs = _analyze_diff_significance(added_lines, removed_lines, code_file)
            
            if needs_docs['requires_documentation']:
                # Extract meaningful terms from diff content
                diff_terms = _extract_terms_from_diff(added_lines, removed_lines, code_file)
                
                # Query ChromaDB for related docs
                query = f"search_query: {' '.join(diff_terms)} {code_file} implementation"
                try:
                    results = collection.query(
                        query_texts=[query],
                        n_results=5
                    )
                    
                    # Check if there are docs in /docs directory that might be related
                    doc_files_in_docs = []
                    if docs_path.exists():
                        for doc_file in docs_path.rglob("*.md"):
                            doc_rel_path = str(doc_file.relative_to(Path(request.repo_path)))
                            doc_files_in_docs.append(doc_rel_path)
                    
                    if results['documents'][0]:
                        for i, doc in enumerate(results['documents'][0]):
                            doc_path = results['metadatas'][0][i]['file_path']
                            is_in_docs_dir = any(doc_path.startswith(d) for d in doc_files_in_docs) or doc_path.startswith('docs/')
                            
                            suggestions.append({
                                'code_file': code_file,
                                'related_doc': doc_path,
                                'relevance_score': 1 - results['distances'][0][i],
                                'suggestion': needs_docs['reason'],
                                'doc_preview': doc[:200] + "..." if len(doc) > 200 else doc,
                                'diff_summary': needs_docs['summary'],
                                'is_in_docs_directory': is_in_docs_dir,
                                'commit_range': diff_item['commit_range'],
                                'change_type': needs_docs['change_type']
                            })
                    else:
                        # No existing docs found, suggest creating new documentation
                        suggestions.append({
                            'code_file': code_file,
                            'related_doc': None,
                            'relevance_score': 1.0,
                            'suggestion': f"Create new documentation for {needs_docs['reason']}",
                            'doc_preview': None,
                            'diff_summary': needs_docs['summary'],
                            'is_in_docs_directory': False,
                            'commit_range': diff_item['commit_range'],
                            'change_type': needs_docs['change_type']
                        })
                        
                except Exception as e:
                    await ctx.warning(f"Failed to query for {code_file}: {str(e)}")
                    continue
        
        # Sort by relevance and prioritize docs directory items
        suggestions.sort(key=lambda x: (x['is_in_docs_directory'], x['relevance_score']), reverse=True)
        
        # Group suggestions by documentation file
        doc_groups = {}
        for suggestion in suggestions:
            doc_file = suggestion['related_doc'] or 'New Documentation Needed'
            if doc_file not in doc_groups:
                doc_groups[doc_file] = []
            doc_groups[doc_file].append(suggestion)
        
        return {
            'total_code_changes': len(code_changes),
            'documentation_suggestions': suggestions[:15],  # Top 15
            'affected_docs': list(doc_groups.keys()),
            'docs_directory_suggestions': [s for s in suggestions if s['is_in_docs_directory']][:5],
            'new_docs_needed': [s for s in suggestions if not s['related_doc']][:5],
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

@mcp.tool()
async def index_git_diff(
    repo_path: str,
    commit_range: Optional[str] = None,
    since_days: Optional[int] = 7,
    collection_name: str = "git_changes",
    ctx: Context = None
) -> str:
    """Index git diff content in ChromaDB for better documentation analysis"""
    try:
        await ctx.info(f"Indexing git diff content from {repo_path}")
        
        repo = git.Repo(repo_path)
        collection = chroma_manager.get_or_create_collection(collection_name)
        
        # Get detailed diff information
        diff_data = []
        if commit_range:
            # Get diff for specific commit range with actual content
            diff_output = repo.git.diff(commit_range, name_only=True).split('\n')
            
            # Parse diff content to extract changes
            for file_name in diff_output:
                if file_name.strip():
                    file_diff = repo.git.diff(commit_range, file_name)
                    if file_diff:  # Only process non-empty diffs
                        diff_data.append({
                            'file_path': file_name,
                            'diff_content': file_diff,
                            'commit_range': commit_range
                        })
        else:
            # Get changes from last N days with diff content
            since_date = f"--since={since_days}.days.ago"
            commits = list(repo.iter_commits('HEAD', since=since_date))
            
            changed_files = set()
            for commit in commits:
                for item in commit.stats.files:
                    changed_files.add(item)
            
            # Get diff content for each changed file
            if commits:
                # Compare with the commit before the earliest one
                earliest_commit = commits[-1]
                if earliest_commit.parents:
                    base_commit = earliest_commit.parents[0]
                    for file_name in changed_files:
                        try:
                            file_diff = repo.git.diff(f"{base_commit.hexsha}..HEAD", file_name)
                            if file_diff:
                                diff_data.append({
                                    'file_path': file_name,
                                    'diff_content': file_diff,
                                    'commit_range': f"{base_commit.hexsha[:8]}..HEAD"
                                })
                        except Exception as e:
                            await ctx.warning(f"Failed to get diff for {file_name}: {str(e)}")
        
        # Filter for code files
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php'}
        code_diffs = [
            diff for diff in diff_data
            if any(diff['file_path'].endswith(ext) for ext in code_extensions) and diff['file_path']
        ]
        
        await ctx.info(f"Found {len(code_diffs)} code file diffs to index")
        
        # Process and index each diff
        indexed_count = 0
        for diff_item in code_diffs:
            try:
                code_file = diff_item['file_path']
                diff_content = diff_item['diff_content']
                
                # Extract added/modified lines
                added_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('+') and not line.startswith('+++')]
                removed_lines = [line[1:] for line in diff_content.split('\n') if line.startswith('-') and not line.startswith('---')]
                
                # Analyze significance
                significance = _analyze_diff_significance(added_lines, removed_lines, code_file)
                
                if significance['requires_documentation']:
                    # Extract terms for better searchability
                    terms = _extract_terms_from_diff(added_lines, removed_lines, code_file)
                    
                    # Create a searchable summary of the diff
                    diff_summary = f"Code changes in {code_file}: {significance['reason']}"
                    if terms:
                        diff_summary += f" Related to: {', '.join(terms[:5])}"
                    
                    # Add context from the diff
                    context_lines = []
                    for line in diff_content.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            context_lines.append(f"Added: {line[1:].strip()}")
                        elif line.startswith('-') and not line.startswith('---'):
                            context_lines.append(f"Removed: {line[1:].strip()}")
                    
                    # Create the document content for indexing
                    document_content = f"search_document: {diff_summary}\n\nChanges:\n" + '\n'.join(context_lines[:20])
                    
                    # Generate unique ID for this diff
                    diff_id = f"{code_file}_{diff_item['commit_range']}_{hash(diff_content)}"
                    
                    # Add to ChromaDB
                    collection.add(
                        documents=[document_content],
                        metadatas=[{
                            'file_path': code_file,
                            'commit_range': diff_item['commit_range'],
                            'change_type': significance['change_type'],
                            'significance_score': significance['significance_score'],
                            'indexed_at': datetime.now().isoformat(),
                            'content_type': 'git_diff',
                            'terms': ','.join(terms[:10]),
                            'summary': significance['summary']
                        }],
                        ids=[diff_id]
                    )
                    
                    indexed_count += 1
                    await ctx.report_progress(indexed_count, len(code_diffs))
                    
            except Exception as e:
                await ctx.warning(f"Failed to index diff for {diff_item['file_path']}: {str(e)}")
                continue
        
        await ctx.info(f"Successfully indexed {indexed_count} significant git diffs")
        return f"Indexed {indexed_count} git diff entries from {len(code_diffs)} total code changes"
        
    except Exception as e:
        await ctx.error(f"Git diff indexing failed: {str(e)}")
        raise

def main():
    """Main entry point for the server"""
    mcp.run()

if __name__ == "__main__":
    main()