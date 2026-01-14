#!/usr/bin/env python3
"""Inspect what's actually in ElevenLabs history items to find transcripts."""

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

print(f"\nFound {len(data.get('history', []))} items\n")
print("="*70)

if data.get("history"):
    for idx, item in enumerate(data["history"][:3]):  # Show first 3
        print(f"\nItem {idx + 1}:")
        print(f"  ID: {item.get('history_item_id') or item.get('id')}")
        print(f"  Type: {item.get('type') or item.get('item_type')}")
        print(f"\n  All fields: {list(item.keys())}")
        
        # Show values for key fields
        print("\n  Key field values:")
        for key in ['text', 'transcript', 'conversation_text', 'conversation_id', 
                   'conversation_name', 'text_url', 'transcript_url', 'audio_url',
                   'conversation_id', 'voice_id', 'model_id']:
            if key in item:
                value = item[key]
                if isinstance(value, str) and len(value) > 100:
                    print(f"    {key}: {value[:100]}...")
                else:
                    print(f"    {key}: {value}")
        
        print("\n  Full item (first 500 chars):")
        print(json.dumps(item, indent=2, default=str)[:500])
        print()

print("\n" + "="*70)
print("Now checking if there's a conversations endpoint...")

# Try conversations endpoint
try:
    conv_response = requests.get(f"{BASE_URL}/conversations", headers=headers)
    print(f"  /conversations status: {conv_response.status_code}")
    if conv_response.status_code == 200:
        conv_data = conv_response.json()
        print(f"  Response keys: {list(conv_data.keys()) if isinstance(conv_data, dict) else 'List'}")
except Exception as e:
    print(f"  /conversations error: {e}")
