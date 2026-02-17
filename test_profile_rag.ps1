$headers = @{
    "Content-Type" = "application/json"
}

Write-Host "=== Testing RAG Profile Knowledge ===" -ForegroundColor Cyan
Write-Host "Verifying understanding of: Philosophy, Soft Skills, and Projects"
Write-Host ""

$questions = @(
    "¿Qué opinas de los microservicios vs monolitos?",
    "Cuéntame una situación dificil que hayas resuelto con tu equipo",
    "¿Cómo aplicas los principios SOLID?",
    "Hablame de la migracion del e-commerce legado"
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
        if ($response.sources.Count -gt 0) {
            Write-Host "Top Source Metadata: $($response.sources[0].metadata | ConvertTo-Json -Compress)" -ForegroundColor DarkGray
        }
        Write-Host ""
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}
