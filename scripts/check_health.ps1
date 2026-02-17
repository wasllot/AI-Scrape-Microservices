$services = @(
    @{ Name = "AI Service"; Url = "http://localhost/ai/health" },
    @{ Name = "Business Core"; Url = "http://localhost/app/health" },
    @{ Name = "Scraper Service"; Url = "http://localhost/scraper/health" }
)

Write-Host "Checking service health..." -ForegroundColor Cyan

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -Method Get -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
             Write-Host "✓ $($service.Name): OK" -ForegroundColor Green
        } else {
             Write-Host "⚠ $($service.Name): $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ $($service.Name): Failed ($($_.Exception.Message))" -ForegroundColor Red
    }
}
