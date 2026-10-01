#!/bin/bash

# HUAN Environment Validation Script
# Checks if your .env file is properly configured

echo "=========================================="
echo "HUAN Environment Validation"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Run './setup.sh' or 'make setup-dev' to create one"
    exit 1
fi

echo "✅ .env file exists"
echo ""

# Source the .env file
set -a
source .env 2>/dev/null
set +a

# Required variables for all environments
REQUIRED_VARS=(
    "POSTGRES_DB"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "AUTHENTIK_DB_PASSWORD"
    "AUTHENTIK_SECRET_KEY"
    "AUTHENTIK_CLIENT_ID"
    "AUTHENTIK_CLIENT_SECRET"
    "SECRET_KEY"
)

# Variables that should NOT be default values in production
SHOULD_NOT_BE=(
    "changeme"
    "your-secret-key-change-me"
    "your_client_id_here"
    "your_client_secret_here"
)

echo "Checking required variables..."
echo ""

MISSING=0
WEAK=0
GOOD=0

for var in "${REQUIRED_VARS[@]}"; do
    value="${!var}"

    if [ -z "$value" ]; then
        echo "❌ $var is not set"
        MISSING=$((MISSING + 1))
    else
        # Check if value contains weak defaults
        IS_WEAK=false
        for weak_value in "${SHOULD_NOT_BE[@]}"; do
            if [[ "$value" == *"$weak_value"* ]]; then
                IS_WEAK=true
                break
            fi
        done

        if [ "$IS_WEAK" = true ] && [ "${ENVIRONMENT}" = "production" ]; then
            echo "⚠️  $var contains default/weak value (not safe for production)"
            WEAK=$((WEAK + 1))
        else
            echo "✅ $var is set"
            GOOD=$((GOOD + 1))
        fi
    fi
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "✅ Valid: $GOOD"
echo "⚠️  Weak: $WEAK"
echo "❌ Missing: $MISSING"
echo ""

# Check environment
if [ -z "${ENVIRONMENT}" ]; then
    echo "ℹ️  ENVIRONMENT not set (defaults to development)"
else
    echo "ℹ️  ENVIRONMENT: ${ENVIRONMENT}"
fi

echo ""

# Provide recommendations
if [ $MISSING -gt 0 ]; then
    echo "❌ CRITICAL: Required variables are missing"
    echo "   Fix: Update your .env file with missing values"
    exit 1
elif [ "$WEAK" -gt 0 ] && [ "${ENVIRONMENT}" = "production" ]; then
    echo "⚠️  WARNING: Using weak/default values in PRODUCTION"
    echo "   Fix: Run './generate-secrets.sh' and update .env"
    echo ""
    echo "   This is a SECURITY RISK in production!"
    exit 2
elif [ "$WEAK" -gt 0 ]; then
    echo "⚠️  Some default values detected (OK for development)"
    echo "   For production: Run './generate-secrets.sh' and update .env"
    exit 0
else
    echo "✅ All checks passed! Environment is properly configured."
    echo ""
    echo "You can now start the services:"
    if [ "${ENVIRONMENT}" = "production" ]; then
        echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
        echo "  OR: make prod"
    else
        echo "  docker compose up -d"
        echo "  OR: make dev"
    fi
    exit 0
fi
