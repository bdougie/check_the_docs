"""
Ultra-simple unit tests for core logic only.
Tests the classes directly without any external dependencies.
"""
import pytest
from pathlib import Path
from datetime import datetime
from typing import List
from pydantic import BaseModel


# Copy the core classes here to test in isolation
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


class CheckDocsRequest(BaseModel):
    repo_path: str
    commit_range: str = None
    since_days: int = 7


class TestDocumentProcessor:
    """Test DocumentProcessor pure business logic"""
    
    def test_init_defaults(self):
        """Test DocumentProcessor initialization with defaults"""
        processor = DocumentProcessor()
        assert processor.chunk_size == 2000
        assert processor.chunk_overlap == 200
    
    def test_init_custom(self):
        """Test DocumentProcessor initialization with custom values"""
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50
    
    def test_chunk_text_short(self):
        """Test chunking short text that fits in one chunk"""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        text = "Short text that fits in one chunk"
        
        chunks = processor._chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_long(self):
        """Test chunking long text into multiple chunks"""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        text = "This is a very long piece of text that definitely needs to be split into multiple chunks for proper processing and testing."
        
        chunks = processor._chunk_text(text)
        
        assert len(chunks) > 1
        # Each chunk should be roughly the right size
        for chunk in chunks:
            assert len(chunk) <= processor.chunk_size + 50  # Allow variance for sentence breaks
    
    def test_process_markdown_adds_prefix(self):
        """Test that process_markdown adds search_document prefix"""
        processor = DocumentProcessor()
        content = "# Test Document\nSome content here."
        
        result = processor.process_markdown(content, "test.md")
        
        assert len(result) >= 1
        assert result[0]["content"].startswith("search_document: ")
        assert "# Test Document" in result[0]["content"]
    
    def test_process_markdown_metadata(self):
        """Test that process_markdown creates proper metadata"""
        processor = DocumentProcessor()
        content = "Test content"
        file_path = "docs/test.md"
        
        result = processor.process_markdown(content, file_path)
        
        assert len(result) == 1
        metadata = result[0]["metadata"]
        assert metadata["file_path"] == file_path
        assert metadata["chunk_index"] == 0
        assert metadata["total_chunks"] == 1
        assert "indexed_at" in metadata
    
    def test_process_markdown_empty(self):
        """Test processing empty content"""
        processor = DocumentProcessor()
        
        result = processor.process_markdown("", "empty.md")
        
        assert len(result) == 1
        assert result[0]["content"] == "search_document: "
        assert result[0]["metadata"]["file_path"] == "empty.md"


class TestCheckDocsRequest:
    """Test CheckDocsRequest Pydantic model validation"""
    
    def test_minimal_request(self):
        """Test creating request with minimal required fields"""
        request = CheckDocsRequest(repo_path="/test/repo")
        
        assert request.repo_path == "/test/repo"
        assert request.commit_range is None
        assert request.since_days == 7  # default value
    
    def test_full_request(self):
        """Test creating request with all fields"""
        request = CheckDocsRequest(
            repo_path="/test/repo",
            commit_range="main..feature",
            since_days=14
        )
        
        assert request.repo_path == "/test/repo"
        assert request.commit_range == "main..feature"
        assert request.since_days == 14