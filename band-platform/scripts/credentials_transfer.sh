#!/bin/bash

# This script provides secure transfer of OAuth credentials between environments
# Usage: ./credentials_transfer.sh [export|import] [passphrase]

set -e

OPERATION=$1
PASSPHRASE=$2
EXPORT_FILE="oauth_credentials.enc"

# Export credentials with encryption
export_credentials() {
    if [ -z "$PASSPHRASE" ]; then
        read -s -p "Enter encryption passphrase: " PASSPHRASE
        echo ""
    fi
    
    # Create temporary file with credentials
    TEMP_FILE=$(mktemp)
    echo "GOOGLE_CLIENT_ID=$(grep GOOGLE_CLIENT_ID backend/.env.production | cut -d= -f2)" > "$TEMP_FILE"
    echo "GOOGLE_CLIENT_SECRET=$(grep GOOGLE_CLIENT_SECRET backend/.env.production | cut -d= -f2)" >> "$TEMP_FILE"
    echo "GOOGLE_DRIVE_SOURCE_FOLDER_ID=$(grep GOOGLE_DRIVE_SOURCE_FOLDER_ID backend/.env.production | cut -d= -f2)" >> "$TEMP_FILE"
    
    # Encrypt the file
    openssl enc -aes-256-cbc -salt -in "$TEMP_FILE" -out "$EXPORT_FILE" -k "$PASSPHRASE"
    
    # Clean up
    rm -f "$TEMP_FILE"
    
    echo "✓ Credentials exported to $EXPORT_FILE"
    echo "Transfer this file securely to your deployment environment"
}

# Import credentials with decryption
import_credentials() {
    if [ ! -f "$EXPORT_FILE" ]; then
        echo "❌ Export file $EXPORT_FILE not found"
        exit 1
    fi
    
    if [ -z "$PASSPHRASE" ]; then
        read -s -p "Enter decryption passphrase: " PASSPHRASE
        echo ""
    fi
    
    # Decrypt the file
    TEMP_FILE=$(mktemp)
    openssl enc -aes-256-cbc -d -in "$EXPORT_FILE" -out "$TEMP_FILE" -k "$PASSPHRASE"
    
    # Source the credentials
    source "$TEMP_FILE"
    
    # Update environment files
    ./scripts/oauth_credentials_manager.sh <<EOF
$GOOGLE_CLIENT_ID
$GOOGLE_CLIENT_SECRET
$GOOGLE_DRIVE_SOURCE_FOLDER_ID
y
EOF
    
    # Clean up
    rm -f "$TEMP_FILE" "$EXPORT_FILE"
    
    echo "✓ Credentials imported successfully"
}

case "$OPERATION" in
    export)
        export_credentials
        ;;
    import)
        import_credentials
        ;;
    *)
        echo "Usage: $0 [export|import] [passphrase]"
        exit 1
        ;;
esac