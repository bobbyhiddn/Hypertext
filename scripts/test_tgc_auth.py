#!/usr/bin/env python3
"""Test TGC API authentication."""

import os
import sys
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

import requests

url = "https://www.thegamecrafter.com/api"

api_key = os.environ.get('TGC_API_KEY')
username = os.environ.get('TGC_USERNAME')
password = os.environ.get('TGC_PASSWORD')

print("Testing TGC API authentication...")
print(f"API Key: {api_key[:10] if api_key else 'NOT SET'}...")
print(f"Username: {username}")
print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
print()

if not all([api_key, username, password]):
    print("ERROR: Missing credentials in .env")
    print("Required: TGC_API_KEY, TGC_USERNAME, TGC_PASSWORD")
    sys.exit(1)

# Step 1: Create session
print("--- Step 1: Creating session ---")
params = {
    'api_key_id': api_key,
    'username': username,
    'password': password
}
response = requests.post(url + "/session", params=params)
print(f"Status: {response.status_code}")

if response.status_code != 200:
    print(f"ERROR: {response.text}")
    sys.exit(1)

result = response.json()
if 'error' in result:
    print(f"ERROR: {result['error']}")
    sys.exit(1)

session = result['result']
print(f"Session ID: {session['id']}")
print(f"User ID: {session['user_id']}")
print()

# Step 2: Fetch user info
print("--- Step 2: Fetching user info ---")
params = {'session_id': session['id']}
response = requests.get(url + "/user/" + session['user_id'], params=params)
print(f"Status: {response.status_code}")

if response.status_code != 200:
    print(f"ERROR: {response.text}")
    sys.exit(1)

user = response.json()['result']
print(f"Username: {user.get('username', 'N/A')}")
print(f"Display Name: {user.get('display_name', 'N/A')}")
print(f"Email: {user.get('email', 'N/A')}")
print(f"Root Folder ID: {user.get('root_folder_id', 'N/A')}")
print()

print("=== AUTH SUCCESS ===")
print(f"Logged in as: {user.get('display_name', username)}")
print(f"Ready to use session: {session['id'][:20]}...")
