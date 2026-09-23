import httpx

base_url = "https://nereus-sih.onrender.com"
endpoints = [
    "/health",
    "/health/db",
    "/api/v1/health",
    "/api/v1/health/db",
    "/docs",
    "/openapi.json",
    "/api/v1/datasets",
    "/api/v1/platforms",
    "/api/v1/observations",
    "/api/v1/provenance",
]

print("=== TESTING RENDER ENDPOINTS ===")
for ep in endpoints:
    try:
        r = httpx.get(f"{base_url}{ep}", timeout=15.0)
        print(f"{ep:25} -> {r.status_code} ({len(r.text)} bytes): {r.text[:200]}")
    except Exception as e:
        print(f"{ep:25} -> ERROR: {e}")
