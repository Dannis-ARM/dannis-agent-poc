#!/usr/bin/env python3
"""Test Anthropic format API."""

import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DOUBAO_API_KEY")
base_url = "https://ark.cn-beijing.volces.com/api/coding"

print(f"Testing Anthropic format...")
print(f"Base URL: {base_url}")

headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01",
}

payload = {
    "model": "doubao-seed-2-0-code-preview-latest",
    "messages": [{"role": "user", "content": "Hi, respond with just 'hello'"}],
    "max_tokens": 1024,
}

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{base_url}/v1/messages", headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
