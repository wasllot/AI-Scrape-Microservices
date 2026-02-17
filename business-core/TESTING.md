# Laravel Testing Guide

## Running Tests

### Run all tests
```bash
php artisan test
```

### Run with coverage
```bash
php artisan test --coverage
```

### Run specific test file
```bash
php artisan test tests/Unit/Services/AIServiceClientTest.php
```

### Run specific test method
```bash
php artisan test --filter test_ingest_success
```

### Run only unit tests
```bash
php artisan test tests/Unit
```

### Run only feature tests
```bash
php artisan test tests/Feature
```

## Test Structure

- `tests/Unit/Services/` - Service layer unit tests
- `tests/Unit/Jobs/` - Job unit tests
- `tests/Feature/` - Integration/feature tests

## Writing Tests

### AAA Pattern (Arrange, Act, Assert)

```php
public function test_example(): void
{
    // Arrange: Set up test data and mocks
    $mockClient = Mockery::mock(HttpClientInterface::class);
    $service = new AIServiceClient($mockClient);
    
    // Act: Execute the code being tested
    $result = $service->ingest('test content');
    
    // Assert: Verify the results
    $this->assertTrue($result['success']);
}
```

### Mocking with Mockery

```php
$mock = Mockery::mock(InterfaceName::class);
$mock->shouldReceive('methodName')
    ->once()
    ->with('expected', 'parameters')
    ->andReturn('return value');
```

## Coverage Reports

After running tests with coverage, open `coverage-report/index.html` in your browser.

## Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** describing what is being tested
3. **Mock external dependencies** (HTTP calls, databases)
4. **Test both success and failure cases**
5. **Clean up mocks** in tearDown()
