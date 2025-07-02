"""
Simple test configuration - no external dependencies.
"""
import pytest


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing"""
    return """# Test Document

This is a test document with some content.

## Section 1

Here's some content in section 1 with more text to make it longer.

## Section 2

And some content in section 2 with code:

```python
def hello():
    return "world"
```

More text here to ensure we have enough content for chunking tests.
"""