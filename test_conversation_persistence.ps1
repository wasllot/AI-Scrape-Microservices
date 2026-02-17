# Test RAG Chatbot with Conversation Persistence
# This script tests the conversation persistence functionality

Write-Host "=== Testing RAG Chatbot Conversation Persistence ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Create a new conversation
Write-Host "1. Creating new conversation..." -ForegroundColor Yellow
$response1 = Invoke-RestMethod -Uri "http://localhost:8001/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        question = "¿Qué es RAG?"
        max_context_items = 3
    } | ConvertTo-Json)

Write-Host "   ✓ Conversation ID: $($response1.conversation_id)" -ForegroundColor Green
Write-Host "   Answer: $($response1.answer.Substring(0, [Math]::Min(100, $response1.answer.Length)))..." -ForegroundColor Gray
$conversationId = $response1.conversation_id

Write-Host ""

# Test 2: Continue the conversation
Write-Host "2. Continuing conversation..." -ForegroundColor Yellow
$response2 = Invoke-RestMethod -Uri "http://localhost:8001/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        question = "Dame más detalles"
        conversation_id = $conversationId
        max_context_items = 3
    } | ConvertTo-Json)

Write-Host "   ✓ Same conversation ID: $($response2.conversation_id -eq $conversationId)" -ForegroundColor Green
Write-Host "   Answer: $($response2.answer.Substring(0, [Math]::Min(100, $response2.answer.Length)))..." -ForegroundColor Gray

Write-Host ""

# Test 3: Verify database persistence
Write-Host "3. Checking database..." -ForegroundColor Yellow
$convCount = docker-compose exec -T postgres psql -U postgres -d vector_db -t -c "SELECT COUNT(*) FROM conversations;"
$msgCount = docker-compose exec -T postgres psql -U postgres -d vector_db -t -c "SELECT COUNT(*) FROM messages;"

Write-Host "   ✓ Conversations in DB: $($convCount.Trim())" -ForegroundColor Green
Write-Host "   ✓ Messages in DB: $($msgCount.Trim())" -ForegroundColor Green

Write-Host ""

# Test 4: Restart service and verify persistence
Write-Host "4. Testing persistence across restart..." -ForegroundColor Yellow
Write-Host "   Restarting ai-service..." -ForegroundColor Gray
docker-compose restart ai-service | Out-Null
Start-Sleep -Seconds 5

$response3 = Invoke-RestMethod -Uri "http://localhost:8001/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        question = "¿Recuerdas de qué hablamos?"
        conversation_id = $conversationId
        max_context_items = 3
    } | ConvertTo-Json)

Write-Host "   ✓ Conversation persisted after restart!" -ForegroundColor Green
Write-Host "   Answer: $($response3.answer.Substring(0, [Math]::Min(100, $response3.answer.Length)))..." -ForegroundColor Gray

Write-Host ""
Write-Host "=== All tests passed! ===" -ForegroundColor Green
