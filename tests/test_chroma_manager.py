import pytest
from unittest.mock import Mock, patch, MagicMock
from server import ChromaDBManager


class TestChromaDBManager:
    """Test ChromaDBManager class"""
    
    def test_init(self, temp_dir, mock_chroma_client, mock_ollama_embedding):
        """Test ChromaDBManager initialization"""
        manager = ChromaDBManager(persist_path=str(temp_dir))
        
        assert manager.persist_path == str(temp_dir)
        mock_chroma_client.assert_called_once_with(path=str(temp_dir))
        mock_ollama_embedding.assert_called_once()
    
    def test_get_ollama_embedding_function(self, mock_ollama_embedding):
        """Test _get_ollama_embedding_function"""
        manager = ChromaDBManager()
        
        mock_ollama_embedding.assert_called_with(
            model_name="nomic-embed-text",
            url="http://localhost:11434/api/embeddings"
        )
    
    def test_get_existing_collection(self, chroma_manager):
        """Test getting an existing collection"""
        # Mock that collection exists
        mock_collection = Mock()
        chroma_manager.client.get_collection.return_value = mock_collection
        
        result = chroma_manager.get_or_create_collection("test_collection")
        
        chroma_manager.client.get_collection.assert_called_once_with(name="test_collection")
        assert result == mock_collection
    
    def test_create_new_collection(self, chroma_manager):
        """Test creating a new collection when it doesn't exist"""
        # Mock that collection doesn't exist (raises exception)
        chroma_manager.client.get_collection.side_effect = Exception("Collection not found")
        
        mock_collection = Mock()
        chroma_manager.client.create_collection.return_value = mock_collection
        
        result = chroma_manager.get_or_create_collection("new_collection")
        
        chroma_manager.client.get_collection.assert_called_once_with(name="new_collection")
        chroma_manager.client.create_collection.assert_called_once_with(
            name="new_collection",
            embedding_function=chroma_manager.ef
        )
        assert result == mock_collection
    
    def test_get_or_create_collection_default_name(self, chroma_manager):
        """Test get_or_create_collection with default name"""
        mock_collection = Mock()
        chroma_manager.client.get_collection.return_value = mock_collection
        
        result = chroma_manager.get_or_create_collection()
        
        chroma_manager.client.get_collection.assert_called_once_with(name="documents")
        assert result == mock_collection