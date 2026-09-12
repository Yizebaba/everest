# Windy Quick Tunnel

The local helper starts a Cloudflare Quick Tunnel for the running Everest API and prints
the HTTPS URL to enter in the private Windy plugin's `MHEWS API` field.

```powershell
.\infra\docker\start-windy-quick-tunnel.ps1
```

The helper does not read or write database passwords. It launches a companion API process
inside the existing `everest-weather-api` container with the only CORS origin set to
`https://www.windy.com`, then tunnels that companion process through the official
`cloudflare/cloudflared` image.

This is a development and demonstration endpoint only. A Quick Tunnel URL changes when
the tunnel restarts, has no availability guarantee, and must not be used for life-safety
operations.
