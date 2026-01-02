import requests

# Example: Using GitHub API to fetch user info
# (No real password needed, just a public API + optional token)

url = "https://api.github.com/users/bobbyhiddn"

# If you have a token (optional):
# headers = {"Authorization": "token YOUR_GITHUB_TOKEN"}
# response = requests.get(url, headers=headers)

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("GitHub User Info:")
    print("Name:", data.get("name"))
    print("Public Repos:", data.get("public_repos"))
    print("Followers:", data.get("followers"))
else:
    print("Failed to fetch data. Status code:", response.status_code)