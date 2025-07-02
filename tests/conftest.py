import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import chromadb
from server import ChromaDBManager, DocumentProcessor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing"""
    return """# Test Document

This is a test document with some content.

## Section 1

Here's some content in section 1.

## Section 2

And some content in section 2 with code:

```python
def hello():
    return "world"
```

More text here.
"""


@pytest.fixture
def sample_markdown_files(temp_dir):
    """Create sample markdown files for testing"""
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    
    # Create sample files
    (docs_dir / "doc1.md").write_text("""# Document 1
This is the first document.
""")
    
    (docs_dir / "doc2.md").write_text("""# Document 2
This is the second document with more content.

## API Reference
Details about the API.
""")
    
    (docs_dir / "subdir").mkdir()
    (docs_dir / "subdir" / "doc3.md").write_text("""# Subdocument
This is in a subdirectory.
""")
    
    return docs_dir


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client"""
    with patch('chromadb.PersistentClient') as mock_client:
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        mock_client.return_value.create_collection.return_value = mock_collection
        yield mock_client


@pytest.fixture
def mock_ollama_embedding():
    """Mock Ollama embedding function"""
    with patch('chromadb.utils.embedding_functions.OllamaEmbeddingFunction') as mock_ef:
        yield mock_ef


@pytest.fixture
def chroma_manager(temp_dir, mock_chroma_client, mock_ollama_embedding):
    """ChromaDBManager instance with mocked dependencies"""
    return ChromaDBManager(persist_path=str(temp_dir))


@pytest.fixture
def doc_processor():
    """DocumentProcessor instance"""
    return DocumentProcessor(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def mock_git_repo(temp_dir):
    """Mock git repository"""
    with patch('git.Repo') as mock_repo:
        mock_instance = Mock()
        mock_repo.return_value = mock_instance
        mock_instance.git.diff.return_value = "file1.py\nfile2.js\nREADME.md"
        yield mock_instance