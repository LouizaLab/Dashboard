#!/usr/bin/env python3
"""Debug script to see what's in ElevenLabs history items."""

import os
import requests
import json

API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1"

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

print("Fetching history...")
response = requests.get(f"{BASE_URL}/history", headers=headers)
data = response.json()

print(f"\nFound {len(data.get('history', []))} items")
print("\nFirst history item structure:")
print("="*70)

if data.get("history"):
    first_item = data["history"][0]
    print(json.dumps(first_item, indent=2, default=str))
    print("\n" + "="*70)
    print("\nAvailable fields:")
    for key in first_item.keys():
        value = first_item[key]
        value_preview = str(value)[:100] if not isinstance(value, (dict, list)) else type(value).__name__
        print(f"  - {key}: {value_preview}")

