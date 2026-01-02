#!/usr/bin/env python3
"""Test TGC auth using the thegamecrafter package."""

import os
import sys
from pathlib import Path
import requests

# Load .env
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

api_key = os.environ.get('TGC_API_KEY')
username = os.environ.get('TGC_USERNAME')
password = os.environ.get('TGC_PASSWORD')

print("Testing TGC auth...")
print(f"API Key: {api_key[:10] if api_key else 'NOT SET'}...")
print(f"Username: {username}")
print()

if not all([api_key, username, password]):
    print("ERROR: Missing credentials in .env")
    print("Required: TGC_API_KEY, TGC_USERNAME, TGC_PASSWORD")
    sys.exit(1)

# Method 1: Direct requests (like the package does internally)
print("=== Method 1: Direct POST to /api/session ===")
params = {'api_key_id': api_key, 'username': username, 'password': password}
response = requests.post('https://www.thegamecrafter.com/api/session', params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

if response.status_code == 200 and 'result' in response.json():
    print("Direct auth SUCCESS!")
    session_id = response.json()['result']['id']
    print(f"Session ID: {session_id}")
else:
    print("Direct auth FAILED")
print()

# Method 2: Using the package
print("=== Method 2: Using thegamecrafter package ===")
try:
    from thegamecrafter import TheGameCrafter

    TGC = TheGameCrafter(
        username=username,
        password=password,
        apikey=api_key,
        raise_on_errors=False  # Don't raise, let us see errors
    )

    if TGC.auth:
        print(f"Package auth SUCCESS!")
        print(f"Session ID: {TGC.session_id}")

        # Try listing games
        print("\nTrying to list games...")
        games = TGC.games.list()
        print(f"Games: {games.content}")
    else:
        print("Package auth FAILED - TGC.auth is False")
        if TGC.auth_error:
            print(f"Auth error: {TGC.auth_error}")

except Exception as e:
    print(f"Package ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("=== DONE ===")
