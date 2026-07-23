"""Smoke test script — verifies the app boots and endpoints respond.

Run locally:
    1. Start PostgreSQL + Redis (Docker or local installs)
    2. Copy .env.example to .env and fill in your values
    3. pip install -r requirements.txt
    4. python smoke_test.py

This script:
    1. Starts uvicorn in a subprocess.
    2. Waits for /api/health to respond 200.
    3. Hits key endpoints and checks status codes.
    4. Shuts down the server.
"""

import subprocess
import sys
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
ENDPOINTS = [
    ("GET", "/api/health", 200),
    ("GET", "/api/stocks", 200),
    ("GET", "/api/tags", 200),
    ("GET", "/api/screeners", 200),
    ("GET", "/api/dashboard", 200),
]


def main() -> None:
    print("🚀 Starting uvicorn...")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready.
    ready = False
    for attempt in range(20):
        try:
            r = httpx.get(f"{BASE_URL}/api/health", timeout=2)
            if r.status_code == 200:
                ready = True
                break
        except httpx.ConnectError:
            pass
        time.sleep(1)

    if not ready:
        print("❌ Server failed to start within 20 seconds.")
        server.terminate()
        sys.exit(1)

    print("✅ Server is up!\n")

    # Run endpoint checks.
    all_passed = True
    for method, path, expected_status in ENDPOINTS:
        try:
            r = httpx.request(method, f"{BASE_URL}{path}", timeout=10)
            status = "✅" if r.status_code == expected_status else "❌"
            if r.status_code != expected_status:
                all_passed = False
            print(f"  {status} {method} {path} → {r.status_code} (expected {expected_status})")
        except Exception as e:
            print(f"  ❌ {method} {path} → ERROR: {e}")
            all_passed = False

    # Test creating a screener.
    print("\n  Testing POST /api/screeners...")
    try:
        r = httpx.post(
            f"{BASE_URL}/api/screeners",
            json={"name": "Test Screener", "scan_clause": "( {cash} ( latest close > 100 ) )"},
            timeout=10,
        )
        status = "✅" if r.status_code == 201 else "❌"
        if r.status_code != 201:
            all_passed = False
        print(f"  {status} POST /api/screeners → {r.status_code} (expected 201)")
        if r.status_code == 201:
            data = r.json()
            print(f"      Created screener: id={data['id']}, name='{data['name']}'")
    except Exception as e:
        print(f"  ❌ POST /api/screeners → ERROR: {e}")
        all_passed = False

    # Cleanup.
    print("\n🛑 Shutting down server...")
    server.terminate()
    server.wait()

    if all_passed:
        print("\n🎉 All smoke tests passed!")
    else:
        print("\n⚠️  Some tests failed — check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
