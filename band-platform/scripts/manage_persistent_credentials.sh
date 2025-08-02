#!/bin/bash

# Utility to manage persistent OAuth credentials

CREDS_FILE="/etc/soleil/oauth.env"

case "$1" in
    show)
        if [ -f "$CREDS_FILE" ]; then
            echo "Current OAuth Configuration:"
            sudo grep -E "CLIENT_ID|FOLDER_ID" "$CREDS_FILE" | sed 's/SECRET=.*/SECRET=***HIDDEN***/'
        else
            echo "No credentials file found"
        fi
        ;;
    edit)
        sudo nano "$CREDS_FILE"
        echo "Credentials updated. Restart services to apply changes."
        ;;
    backup)
        BACKUP_FILE="/etc/soleil/oauth.env.backup.$(date +%Y%m%d_%H%M%S)"
        sudo cp "$CREDS_FILE" "$BACKUP_FILE"
        sudo chmod 600 "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        ;;
    validate)
        if [ -f "$CREDS_FILE" ]; then
            source "$CREDS_FILE"
            if [ -n "$GOOGLE_CLIENT_ID" ] && [ -n "$GOOGLE_CLIENT_SECRET" ]; then
                echo "✅ Credentials file is valid"
            else
                echo "❌ Credentials file is missing required values"
            fi
        else
            echo "❌ No credentials file found"
        fi
        ;;
    *)
        echo "Usage: $0 {show|edit|backup|validate}"
        exit 1
        ;;
esac