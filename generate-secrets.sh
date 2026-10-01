#!/bin/bash

# ===========================================
# HUAN - Secret Generator Script
# ===========================================
# This script generates secure random secrets for production use
# Run: ./generate-secrets.sh

echo "===========================================
HUAN - Generating Secure Secrets
===========================================
"

echo "# Generated Secrets for Production - $(date)"
echo "# Add these to your .env file"
echo ""

echo "# Postgres Password (32 chars alphanumeric)"
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)"
echo ""

echo "# Authentik Database Password (32 chars alphanumeric)"
echo "AUTHENTIK_DB_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)"
echo ""

echo "# Authentik Secret Key (60 chars base64)"
echo "AUTHENTIK_SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n')"
echo ""

echo "# Backend JWT Secret Key (32 chars base64)"
echo "SECRET_KEY=$(openssl rand -base64 32 | tr -d '\n')"
echo ""

echo "===========================================
⚠️  IMPORTANT:
===========================================
1. Copy these values to your .env file
2. Keep them secure and never commit to git
3. Get AUTHENTIK_CLIENT_ID and AUTHENTIK_CLIENT_SECRET
   from Authentik admin panel after setup
4. Use different secrets for each environment
===========================================
"
