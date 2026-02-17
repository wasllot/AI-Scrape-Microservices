# AI Service - Testing Guide

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_embeddings.py
```

### Run specific test
```bash
pytest tests/test_embeddings.py::TestEmbeddingService::test_ingest_success
```

### Run only unit tests (skip integration)
```bash
pytest -m "not integration"
```

## Test Structure

- `tests/test_embeddings.py` - Embedding service tests
- `tests/test_database.py` - Database connection tests
- `tests/test_config.py` - Configuration tests

## Coverage Reports

After running tests with coverage, open `htmlcov/index.html` in your browser to see detailed coverage report.

## Writing Tests

Follow AAA pattern:
1. **Arrange**: Set up test data and mocks
2. **Act**: Execute the code being tested
3. **Assert**: Verify the results

Example:
```python
def test_example():
    # Arrange
    service = MyService()
    
    # Act
    result = service.do_something()
    
    # Assert
    assert result == expected_value
```
