$headers = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

$body = @{
    question = "Hola desde Business Core Proxy"
    max_context_items = 3
} | ConvertTo-Json

Write-Host "Testing Business Core Chat Endpoint..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:9000/api/chat" -Method POST -Headers $headers -Body $body
    Write-Host "SUCCESS!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    # Print the full response body for debugging 500 errors (Laravel binding errors usually show here)
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $body = $reader.ReadToEnd()
        Write-Host "Response Body: $body" -ForegroundColor Gray
    }
}
