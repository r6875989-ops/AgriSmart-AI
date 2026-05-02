$Subdomain = "agrismartai-test"
$Port = 5173

Write-Host "Starting stable tunnel for $Subdomain.loca.lt on port $Port..."
Write-Host "This will automatically reconnect if it drops."

while ($true) {
    Write-Host "Connecting..."
    npx -y localtunnel --port $Port --subdomain $Subdomain
    Write-Host "Tunnel disconnected. Reconnecting in 5 seconds..."
    Start-Sleep -Seconds 5
}
