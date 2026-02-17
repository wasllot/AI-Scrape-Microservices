$headers = @{
    "Content-Type" = "application/json"
}

Write-Host "=== Testing RAG Recruitment Assistant ===" -ForegroundColor Cyan
Write-Host ""

$questions = @(
    "¿Cuál es tu experiencia en desarrollo backend?",
    "¿Qué tecnologías manejas?",
    "Háblame de tus proyectos recientes"
)

foreach ($question in $questions) {
    Write-Host "Q: $question" -ForegroundColor Yellow
    
    $body = @{
        question = $question
        max_context_items = 5
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/chat" -Method POST -Headers $headers -Body $body
        Write-Host "A: $($response.answer)" -ForegroundColor Green
        Write-Host "Sources: $($response.sources.Count) documents" -ForegroundColor Gray
        Write-Host ""
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}
