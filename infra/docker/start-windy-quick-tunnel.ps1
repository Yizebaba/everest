param(
    [string]$ApiContainer = "everest-weather-api",
    [string]$TunnelContainer = "everest-windy-quick-tunnel",
    [int]$ApiPort = 52149
)

$ErrorActionPreference = "Stop"

docker inspect --format "{{.State.Running}}" $ApiContainer | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Everest API container '$ApiContainer' is not running."
}

# Keep the production-like API process untouched; the tunnel uses a CORS-scoped companion.
docker exec $ApiContainer python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$ApiPort/healthz', timeout=2)" 2>$null
if ($LASTEXITCODE -ne 0) {
    docker exec -d -e "EVEREST_API_PORT=$ApiPort" -e "EVEREST_CORS_ALLOWED_ORIGINS=https://www.windy.com" $ApiContainer python apps/api/run_dev.py | Out-Null
    Start-Sleep -Seconds 3
}

docker exec $ApiContainer python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$ApiPort/healthz', timeout=5)" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Windy CORS companion API did not become healthy."
}

docker rm -f $TunnelContainer 2>$null | Out-Null
docker run -d --name $TunnelContainer --restart no --network "container:$ApiContainer" cloudflare/cloudflared:latest tunnel --url "http://127.0.0.1:$ApiPort" | Out-Null

for ($attempt = 0; $attempt -lt 12; $attempt++) {
    Start-Sleep -Seconds 2
    $logs = cmd /c "docker logs $TunnelContainer 2>&1"
    $match = [regex]::Match(($logs -join "`n"), "https://[a-z0-9-]+\.trycloudflare\.com")
    if ($match.Success) {
        $match.Value
        exit 0
    }
}

throw "Cloudflare Quick Tunnel did not return a public URL. Run 'docker logs $TunnelContainer' for details."
