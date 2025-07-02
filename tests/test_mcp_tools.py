import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from server import CheckDocsRequest, chroma_manager, doc_processor
import git


# Create wrapper functions to test the MCP tool logic
async def _index_documentation_impl(folder_path: str, collection_name: str = "documents", ctx=None):
    """Implementation logic for index_documentation tool"""
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


async def _search_documentation_impl(query: str, collection_name: str = "documents", n_results: int = 5, ctx=None):
    """Implementation logic for search_documentation tool"""
    await ctx.info(f"Searching for: {query}")
    
    collection = chroma_manager.get_or_create_collection(collection_name)
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    formatted_results = []
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0], 
        results['metadatas'][0], 
        results['distances'][0]
    )):
        formatted_results.append({
            "content": doc,
            "metadata": metadata,
            "similarity_score": 1 - distance,
            "rank": i + 1
        })
    
    await ctx.info(f"Found {len(formatted_results)} results")
    return {"query": query, "results": formatted_results}


async def _check_docs_impl(request: CheckDocsRequest, ctx=None):
    """Implementation logic for check_docs tool"""
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
        commits = repo.git.log(since_date, name_only=True, pretty="format:").split('\n')
        diffs = [f for f in commits if f.strip()]
    
    # Filter for code files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php'}
    code_changes = [f for f in diffs if any(f.endswith(ext) for ext in code_extensions)]
    
    suggestions = []
    for changed_file in code_changes:
        # Search for related documentation
        search_query = f"documentation for {Path(changed_file).stem}"
        
        results = collection.query(
            query_texts=[search_query],
            n_results=3
        )
        
        if results['documents'][0]:  # If we found related docs
            suggestions.append({
                "changed_file": changed_file,
                "related_docs": [
                    {
                        "file": meta.get('file_path', 'unknown'),
                        "relevance": 1 - dist
                    }
                    for meta, dist in zip(results['metadatas'][0], results['distances'][0])
                ]
            })
    
    await ctx.info(f"Found {len(suggestions)} documentation update suggestions")
    return {"suggestions": suggestions, "analyzed_files": len(code_changes)}


class TestMCPTools:
    """Test MCP tool functions"""
    
    @pytest.mark.asyncio
    async def test_index_documentation_success(self, sample_markdown_files):
        """Test successful documentation indexing"""
        mock_ctx = AsyncMock()
        
        with patch.object(chroma_manager, 'get_or_create_collection') as mock_get_collection, \
             patch.object(doc_processor, 'process_markdown') as mock_process:
            
            mock_collection = Mock()
            mock_get_collection.return_value = mock_collection
            mock_process.return_value = [
                {"content": "chunk1", "metadata": {"file_path": "doc1.md", "chunk_index": 0}},
                {"content": "chunk2", "metadata": {"file_path": "doc1.md", "chunk_index": 1}}
            ]
            
            result = await _index_documentation_impl(
                folder_path=str(sample_markdown_files),
                collection_name="test_collection",
                ctx=mock_ctx
            )
            
            # Verify calls
            mock_ctx.info.assert_called()
            mock_get_collection.assert_called_with("test_collection")
            assert "Successfully indexed" in result
    
    @pytest.mark.asyncio
    async def test_index_documentation_invalid_path(self):
        """Test indexing with invalid path"""
        mock_ctx = AsyncMock()
        
        with pytest.raises(ValueError, match="does not exist"):
            await _index_documentation_impl(
                folder_path="/nonexistent/path",
                collection_name="test",
                ctx=mock_ctx
            )
    
    @pytest.mark.asyncio
    async def test_search_documentation(self):
        """Test document search functionality"""
        mock_ctx = AsyncMock()
        
        # Mock search results
        mock_results = {
            'documents': [['doc1 content', 'doc2 content']],
            'metadatas': [[{'file_path': 'doc1.md'}, {'file_path': 'doc2.md'}]],
            'distances': [[0.1, 0.2]]
        }
        
        with patch.object(chroma_manager, 'get_or_create_collection') as mock_get_collection:
            mock_collection = Mock()
            mock_collection.query.return_value = mock_results
            mock_get_collection.return_value = mock_collection
            
            result = await _search_documentation_impl(
                query="test search",
                collection_name="docs",
                n_results=2,
                ctx=mock_ctx
            )
            
            mock_collection.query.assert_called_once_with(
                query_texts=["test search"],
                n_results=2
            )
            
            assert "results" in result
            assert len(result["results"]) == 2
    
    @pytest.mark.asyncio
    async def test_check_docs_with_commit_range(self):
        """Test check_docs with specific commit range"""
        mock_ctx = AsyncMock()
        
        request = CheckDocsRequest(
            repo_path="/test/repo",
            commit_range="main..feature"
        )
        
        with patch('server.chroma_manager') as mock_manager, \
             patch('git.Repo') as mock_repo_class:
            
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.git.diff.return_value = "file1.py\nfile2.js\nREADME.md"
            
            mock_collection = Mock()
            mock_collection.query.return_value = {
                'documents': [['related doc']],
                'metadatas': [[{'file_path': 'doc.md'}]],
                'distances': [[0.3]]
            }
            mock_manager.get_or_create_collection.return_value = mock_collection
            
            result = await _check_docs_impl(request, ctx=mock_ctx)
            
            mock_repo.git.diff.assert_called_with("main..feature", name_only=True)
            assert "suggestions" in result
    
    @pytest.mark.asyncio
    async def test_check_docs_with_since_days(self):
        """Test check_docs with since_days parameter"""
        mock_ctx = AsyncMock()
        
        request = CheckDocsRequest(
            repo_path="/test/repo",
            since_days=14
        )
        
        with patch('server.chroma_manager') as mock_manager, \
             patch('git.Repo') as mock_repo_class:
            
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.git.log.return_value = "file1.py\nfile2.js"
            
            mock_collection = Mock()
            mock_collection.query.return_value = {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }
            mock_manager.get_or_create_collection.return_value = mock_collection
            
            result = await _check_docs_impl(request, ctx=mock_ctx)
            
            # Should use git log with since parameter
            mock_repo.git.log.assert_called()
            assert "suggestions" in result


class TestCheckDocsRequest:
    """Test CheckDocsRequest model"""
    
    def test_valid_request(self):
        """Test valid CheckDocsRequest creation"""
        request = CheckDocsRequest(repo_path="/test/repo")
        
        assert request.repo_path == "/test/repo"
        assert request.commit_range is None
        assert request.since_days == 7
    
    def test_request_with_commit_range(self):
        """Test CheckDocsRequest with commit range"""
        request = CheckDocsRequest(
            repo_path="/test/repo",
            commit_range="main..feature",
            since_days=14
        )
        
        assert request.repo_path == "/test/repo"
        assert request.commit_range == "main..feature"
        assert request.since_days == 14