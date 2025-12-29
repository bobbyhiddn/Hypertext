#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./tools/bootstrap_github_secrets.sh owner/repo
# Example:
#   ./tools/bootstrap_github_secrets.sh micah/hypertext

REPO="${1:-}"
if [[ -z "${REPO}" ]]; then
  echo "Usage: $0 owner/repo"
  exit 1
fi

command -v gh >/dev/null 2>&1 || { echo "gh CLI is required. Install it first."; exit 1; }

echo "Authenticating with GitHub CLI (if needed)..."
# This will prompt if you're not logged in.
gh auth status >/dev/null 2>&1 || gh auth login

echo ""
echo "Enter your Gemini API key (input hidden):"
read -r -s GEMINI_API_KEY
echo ""
if [[ -z "${GEMINI_API_KEY}" ]]; then
  echo "No key entered. Exiting."
  exit 1
fi

# Repo secret (simplest).
# If you use Environment secrets, you can add --env <ENV_NAME>.
echo "Setting repository secret GEMINI_API_KEY for ${REPO}..."
echo -n "${GEMINI_API_KEY}" | gh secret set GEMINI_API_KEY --repo "${REPO}"

echo "Done. Secret stored as GEMINI_API_KEY."
echo ""
echo "Next: In GitHub repo settings, create an Environment named 'imagegen' and add yourself as a required reviewer."
