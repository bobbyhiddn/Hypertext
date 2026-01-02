#!/bin/bash
# Test TGC API authentication

# Load .env manually to preserve special characters
if [ -f .env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # Strip Windows carriage returns
        line="${line//$'\r'/}"
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        # Split on first = only (preserves = in values)
        key="${line%%=*}"
        value="${line#*=}"
        # Remove surrounding quotes if present
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        export "$key=$value"
    done < .env
fi

echo "Testing TGC API authentication..."
echo "API Key length: ${#TGC_API_KEY}"
echo "API Key (hex first 20 chars):"
echo -n "$TGC_API_KEY" | head -c 20 | xxd
echo "Username: '$TGC_USERNAME' (length: ${#TGC_USERNAME})"
echo "Password set: $([ -n "$TGC_PASSWORD" ] && echo 'YES' || echo 'NO')"
echo "Password length: ${#TGC_PASSWORD}"
echo ""

# Try both parameter names
echo "Trying with api_key_id..."
response1=$(curl -s -X POST "https://www.thegamecrafter.com/api/session" \
    --data-urlencode "api_key_id=$TGC_API_KEY" \
    --data-urlencode "username=$TGC_USERNAME" \
    --data-urlencode "password=$TGC_PASSWORD")
echo "$response1" | python -m json.tool 2>/dev/null || echo "$response1"

echo ""
echo "Trying with api_key..."
response2=$(curl -s -X POST "https://www.thegamecrafter.com/api/session" \
    --data-urlencode "api_key=$TGC_API_KEY" \
    --data-urlencode "username=$TGC_USERNAME" \
    --data-urlencode "password=$TGC_PASSWORD")
echo "$response2" | python -m json.tool 2>/dev/null || echo "$response2"

response="$response1"

echo "Response:"
echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
