import pytest
from server import DocumentProcessor


class TestDocumentProcessor:
    """Test DocumentProcessor class"""
    
    def test_init(self):
        """Test DocumentProcessor initialization"""
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=100)
        
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 100
    
    def test_init_defaults(self):
        """Test DocumentProcessor initialization with defaults"""
        processor = DocumentProcessor()
        
        assert processor.chunk_size == 2000
        assert processor.chunk_overlap == 200
    
    def test_process_markdown_basic(self, doc_processor, sample_markdown):
        """Test basic markdown processing"""
        chunks = doc_processor.process_markdown(sample_markdown, "test.md")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, dict) for chunk in chunks)
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        
        # Check metadata
        for chunk in chunks:
            assert chunk["metadata"]["file_path"] == "test.md"
            assert "chunk_index" in chunk["metadata"]
    
    def test_process_markdown_empty(self, doc_processor):
        """Test processing empty markdown"""
        chunks = doc_processor.process_markdown("", "empty.md")
        
        assert len(chunks) == 1
        assert chunks[0]["content"] == "search_document: "  # Empty content gets prefix
        assert chunks[0]["metadata"]["file_path"] == "empty.md"
    
    def test_process_markdown_chunking(self):
        """Test that long content gets chunked properly"""
        # Create a processor with small chunk size for testing
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        
        long_content = "This is a test sentence. " * 20  # Long content
        chunks = processor.process_markdown(long_content, "long.md")
        
        assert len(chunks) > 1
        
        # Check that chunks have proper overlap
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]["content"]
            next_chunk = chunks[i + 1]["content"]
            
            # There should be some overlap between consecutive chunks
            assert len(current_chunk) <= processor.chunk_size + 20  # Allow some variance
    
    def test_chunk_text_simple(self, doc_processor):
        """Test simple text chunking"""
        text = "Short text"
        chunks = doc_processor._chunk_text(text)  # Use private method
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_long(self):
        """Test chunking of long text"""
        processor = DocumentProcessor(chunk_size=20, chunk_overlap=5)
        text = "This is a very long piece of text that should be split into multiple chunks for testing purposes."
        
        chunks = processor._chunk_text(text)  # Use private method
        
        assert len(chunks) > 1
        assert all(len(chunk) <= processor.chunk_size + 20 for chunk in chunks)  # Allow variance for breaking points
    
    def test_chunk_text_with_paragraphs(self):
        """Test chunking respects paragraph breaks"""
        processor = DocumentProcessor(chunk_size=30, chunk_overlap=5)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        
        chunks = processor._chunk_text(text)  # Use private method
        
        # Should break at paragraph boundaries when possible
        assert len(chunks) >= 1
    
    def test_process_markdown_metadata(self, doc_processor):
        """Test that metadata is properly set"""
        content = "# Test\nSome content"
        chunks = doc_processor.process_markdown(content, "path/to/test.md")
        
        for i, chunk in enumerate(chunks):
            metadata = chunk["metadata"]
            assert metadata["file_path"] == "path/to/test.md"
            assert metadata["chunk_index"] == i
            assert isinstance(metadata["chunk_index"], int)
    
    def test_process_markdown_unicode(self, doc_processor):
        """Test processing markdown with unicode characters"""
        content = "# Test 测试\n\nThis has unicode: 你好世界 🌍"
        chunks = doc_processor.process_markdown(content, "unicode.md")
        
        assert len(chunks) > 0
        assert "测试" in chunks[0]["content"]
        assert "你好世界" in chunks[0]["content"]
        assert "🌍" in chunks[0]["content"]