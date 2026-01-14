#!/usr/bin/env python3
"""Check what's in the dialogue field."""

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

if data.get("history"):
    item = data["history"][0]
    print(f"\nHistory Item ID: {item.get('history_item_id')}")
    print(f"\nDialogue field type: {type(item.get('dialogue'))}")
    
    dialogue = item.get("dialogue")
    if dialogue:
        if isinstance(dialogue, list):
            print(f"\nDialogue is a list with {len(dialogue)} items")
            print("\nFirst few dialogue items:")
            for idx, d in enumerate(dialogue[:3]):
                print(f"\n  Item {idx + 1}:")
                print(f"    Type: {type(d)}")
                if isinstance(d, dict):
                    print(f"    Keys: {list(d.keys())}")
                    for key, value in d.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"    {key}: {value[:100]}...")
                        else:
                            print(f"    {key}: {value}")
        elif isinstance(dialogue, dict):
            print(f"\nDialogue is a dict:")
            print(json.dumps(dialogue, indent=2, default=str)[:1000])
        else:
            print(f"\nDialogue: {dialogue}")
    else:
        print("\nNo dialogue field or it's empty")
        
    print("\n" + "="*70)
    print("Full dialogue field:")
    print(json.dumps(dialogue, indent=2, default=str))

