#!/usr/bin/env python3
"""
Quick script to test ElevenLabs API endpoints and see what's available.
"""

import os
import requests
import json

API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1"

if not API_KEY:
    print("❌ ELEVENLABS_API_KEY not set")
    exit(1)

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

print("Testing ElevenLabs API endpoints...")
print("="*70)

# Test various endpoints
endpoints_to_test = [
    "conversations",
    "conversations/history",
    "history",
    "projects",
    "workspaces",
    "user",
    "models",
    "voices",
]

for endpoint in endpoints_to_test:
    try:
        url = f"{BASE_URL}/{endpoint}"
        print(f"\nTesting: GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success!")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"  List length: {len(data)}")
                if len(data) > 0:
                    print(f"  First item keys: {list(data[0].keys())[:5] if isinstance(data[0], dict) else 'N/A'}")
        elif response.status_code == 401:
            print(f"  ❌ Unauthorized - check API key")
        elif response.status_code == 404:
            print(f"  ⚠️  Not found")
        else:
            print(f"  ⚠️  Status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*70)
print("If you see any successful endpoints above, we can use those!")
print("Otherwise, you may need to use specific interview IDs with --ids flag")

