# Quick Start Script para Windows

Write-Host "🚀 Iniciando Sistema SaaS con RAG y Scraping..." -ForegroundColor Cyan
Write-Host ""

# 1. Generar APP_KEY para Laravel
Write-Host "📝 Generando Laravel APP_KEY..." -ForegroundColor Yellow
cd business-core-temp
$appKey = php artisan key:generate --show
cd ..

if ($appKey) {
    Write-Host "✓ APP_KEY generada: $appKey" -ForegroundColor Green
    
    # Actualizar .env
    $envContent = Get-Content .env
    $envContent = $envContent -replace 'APP_KEY=.*', "APP_KEY=$appKey"
    $envContent | Set-Content .env
    Write-Host "✓ .env actualizado" -ForegroundColor Green
} else {
    Write-Host "✗ Error al generar APP_KEY" -ForegroundColor Red
    Write-Host "Genera manualmente con: cd business-core; php artisan key:generate" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⚠️  ANTES DE CONTINUAR:" -ForegroundColor Yellow
Write-Host "   1. Abre el archivo .env" -ForegroundColor White
Write-Host "   2. Agrega tu GEMINI_API_KEY (obtén en: https://aistudio.google.com/app/apikey)" -ForegroundColor White
Write-Host "   3. Cambia DB_PASSWORD por una contraseña segura" -ForegroundColor White
Write-Host ""

$response = Read-Host "¿Deseas iniciar Docker ahora? (s/n)"

if ($response -eq 's' -or $response -eq 'S') {
    Write-Host ""
    Write-Host "🐳 Iniciando Docker Compose..." -ForegroundColor Cyan
    docker-compose up -d
    
    Write-Host ""
    Write-Host "⏳ Esperando que los servicios estén listos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host ""
    Write-Host "🏥 Verificando salud de los servicios..." -ForegroundColor Cyan
    
    try {
        $aiHealth = Invoke-RestMethod -Uri "http://localhost/ai/health" -Method Get
    }
    catch {
        Write-Host "✗ AI Service: No responde" -ForegroundColor Red
    }
    
    try {
        $appHealth = Invoke-RestMethod -Uri "http://localhost/app/health" -Method Get
        Write-Host "✓ Business Core: $($appHealth.status)" -ForegroundColor Green
    } catch {
        Write-Host "✗ Business Core: No responde" -ForegroundColor Red
    }
    
    try {
        $scraperHealth = Invoke-RestMethod -Uri "http://localhost/scraper/health" -Method Get
        Write-Host "✓ Scraper Service: $($scraperHealth.status)" -ForegroundColor Green
    } catch {
        Write-Host "✗ Scraper Service: No responde" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "✨ Sistema iniciado!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📚 Próximos pasos:" -ForegroundColor Cyan
    Write-Host "   - Ver logs: docker-compose logs -f" -ForegroundColor White
    Write-Host "   - Detener: docker-compose down" -ForegroundColor White
    Write-Host "   - Ver README.md para ejemplos de uso" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Para iniciar manualmente: docker-compose up -d" -ForegroundColor Cyan
}
