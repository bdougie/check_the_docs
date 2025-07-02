import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from server import index_documentation, search_documentation, check_docs, list_collections, delete_collection
from server import CheckDocsRequest


class TestMCPTools:
    """Test MCP tool functions"""
    
    @pytest.mark.asyncio
    async def test_index_documentation_success(self, sample_markdown_files, mock_chroma_client):
        """Test successful documentation indexing"""
        # Mock context
        mock_ctx = AsyncMock()
        
        # Mock collection
        mock_collection = Mock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection
        
        with patch('server.chroma_manager') as mock_manager, \
             patch('server.doc_processor') as mock_processor:
            
            mock_manager.get_or_create_collection.return_value = mock_collection
            mock_processor.process_markdown.return_value = [
                {"content": "chunk1", "metadata": {"file_path": "doc1.md", "chunk_index": 0}},
                {"content": "chunk2", "metadata": {"file_path": "doc1.md", "chunk_index": 1}}
            ]
            
            result = await index_documentation(
                folder_path=str(sample_markdown_files),
                collection_name="test_collection",
                ctx=mock_ctx
            )
            
            # Verify calls
            mock_ctx.info.assert_called()
            mock_manager.get_or_create_collection.assert_called_with("test_collection")
            assert "Successfully indexed" in result
    
    @pytest.mark.asyncio
    async def test_index_documentation_invalid_path(self):
        """Test indexing with invalid path"""
        mock_ctx = AsyncMock()
        
        with pytest.raises(ValueError, match="does not exist"):
            await index_documentation(
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
        
        with patch('server.chroma_manager') as mock_manager:
            mock_collection = Mock()
            mock_collection.query.return_value = mock_results
            mock_manager.get_or_create_collection.return_value = mock_collection
            
            result = await search_documentation(
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
    async def test_check_docs_with_commit_range(self, mock_git_repo):
        """Test check_docs with specific commit range"""
        mock_ctx = AsyncMock()
        
        request = CheckDocsRequest(
            repo_path="/test/repo",
            commit_range="main..feature"
        )
        
        with patch('server.chroma_manager') as mock_manager, \
             patch('git.Repo', return_value=mock_git_repo):
            
            mock_collection = Mock()
            mock_collection.query.return_value = {
                'documents': [['related doc']],
                'metadatas': [[{'file_path': 'doc.md'}]],
                'distances': [[0.3]]
            }
            mock_manager.get_or_create_collection.return_value = mock_collection
            
            result = await check_docs(request, ctx=mock_ctx)
            
            mock_git_repo.git.diff.assert_called_with("main..feature", name_only=True)
            assert "suggestions" in result
    
    @pytest.mark.asyncio
    async def test_check_docs_with_since_days(self, mock_git_repo):
        """Test check_docs with since_days parameter"""
        mock_ctx = AsyncMock()
        
        request = CheckDocsRequest(
            repo_path="/test/repo",
            since_days=14
        )
        
        with patch('server.chroma_manager') as mock_manager, \
             patch('git.Repo', return_value=mock_git_repo):
            
            mock_collection = Mock()
            mock_collection.query.return_value = {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }
            mock_manager.get_or_create_collection.return_value = mock_collection
            
            result = await check_docs(request, ctx=mock_ctx)
            
            # Should use git log with since parameter
            mock_git_repo.git.log.assert_called()
            assert "suggestions" in result
    
    @pytest.mark.asyncio
    async def test_list_collections(self):
        """Test listing collections"""
        mock_ctx = AsyncMock()
        
        with patch('server.chroma_manager') as mock_manager:
            mock_manager.client.list_collections.return_value = [
                Mock(name="collection1"),
                Mock(name="collection2")
            ]
            
            result = await list_collections(ctx=mock_ctx)
            
            assert "collections" in result
            assert len(result["collections"]) == 2
    
    @pytest.mark.asyncio
    async def test_delete_collection_success(self):
        """Test successful collection deletion"""
        mock_ctx = AsyncMock()
        
        with patch('server.chroma_manager') as mock_manager:
            mock_manager.client.delete_collection.return_value = None
            
            result = await delete_collection("test_collection", ctx=mock_ctx)
            
            mock_manager.client.delete_collection.assert_called_once_with(name="test_collection")
            assert "successfully deleted" in result.lower()
    
    @pytest.mark.asyncio
    async def test_delete_collection_not_found(self):
        """Test deleting non-existent collection"""
        mock_ctx = AsyncMock()
        
        with patch('server.chroma_manager') as mock_manager:
            mock_manager.client.delete_collection.side_effect = Exception("Collection not found")
            
            with pytest.raises(Exception):
                await delete_collection("nonexistent", ctx=mock_ctx)


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