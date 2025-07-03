#!/bin/bash

# Cloudflare API Credentials
CLOUDFLARE_API_TOKEN="hier-kommt-token"
ZONE_ID="hier-kommt-die -zonen-id"
RECORD_NAME="*.example.com"
RECORD_TYPE="A"

# Ensure log file exists with correct permissions
LOG_FILE="/var/log/cloudflare-ddns.log"
sudo touch "$LOG_FILE"
sudo chmod 666 "$LOG_FILE"

# Get current public IP
CURRENT_IP=$(curl -s https://ipv4.icanhazip.com)

# Get existing DNS record
RECORD_DETAILS=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=$RECORD_TYPE&name=$RECORD_NAME" \
     -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
     -H "Content-Type: application/json")

# Extract record ID and current IP
RECORD_ID=$(echo "$RECORD_DETAILS" | jq -r '.result[0].id')
EXISTING_IP=$(echo "$RECORD_DETAILS" | jq -r '.result[0].content')

# Detailed logging
echo "$(date): Starting IP check" >> "$LOG_FILE"
echo "$(date): Current IP: $CURRENT_IP" >> "$LOG_FILE"
echo "$(date): Existing IP: $EXISTING_IP" >> "$LOG_FILE"

# Update record if IP has changed
if [ "$CURRENT_IP" != "$EXISTING_IP" ]; then
    UPDATE_RESULT=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
         -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
         -H "Content-Type: application/json" \
         --data "{\"type\":\"$RECORD_TYPE\",\"name\":\"$RECORD_NAME\",\"content\":\"$CURRENT_IP\",\"ttl\":1,\"proxied\":false}")
    
    # Log the update with more details
    if echo "$UPDATE_RESULT" | jq -e '.success' > /dev/null; then
        echo "$(date): IP successfully updated to $CURRENT_IP" >> "$LOG_FILE"
    else
        echo "$(date): Failed to update IP" >> "$LOG_FILE"
        echo "$(date): API Response: $(echo "$UPDATE_RESULT" | jq -c .)" >> "$LOG_FILE"
    fi
else
    echo "$(date): No IP change detected" >> "$LOG_FILE"
fi
