#!/bin/bash

# HUAN Quick Setup Script
# This script helps you get started with HUAN quickly

set -e

echo "=========================================="
echo "HUAN - Quick Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Ask for environment type
echo "Which environment do you want to set up?"
echo "1) Development (default passwords, quick setup)"
echo "2) Production (secure secrets, manual configuration)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "Setting up DEVELOPMENT environment..."
        cp .env.development .env
        echo "✅ Created .env from .env.development"
        echo ""
        echo "📝 Next steps:"
        echo "1. Start services: docker compose up -d"
        echo "2. Wait for services to start (~30 seconds)"
        echo "3. Access Authentik at http://localhost:9000"
        echo "4. Create admin account and OAuth2 application"
        echo "5. Update .env with AUTHENTIK_CLIENT_ID and AUTHENTIK_CLIENT_SECRET"
        echo "6. Restart services: docker compose restart backend frontend"
        echo ""
        echo "Quick start command: make dev"
        ;;
    2)
        echo ""
        echo "Setting up PRODUCTION environment..."
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo ""
        echo "🔐 Generating secure secrets..."
        ./generate-secrets.sh > secrets.txt
        echo ""
        echo "✅ Secrets saved to secrets.txt"
        echo ""
        echo "⚠️  IMPORTANT: Complete the following steps:"
        echo "1. Edit .env and replace all 'changeme' values"
        echo "2. Copy secrets from secrets.txt to .env"
        echo "3. Set ENVIRONMENT=production in .env"
        echo "4. Update URLs to your production domain"
        echo "5. Start services: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
        echo "6. Configure Authentik OAuth2 and update credentials"
        echo ""
        echo "⚠️  Don't forget to delete secrets.txt after copying values!"
        echo ""
        echo "Quick start command: make prod"
        ;;
    *)
        echo "Invalid choice. Setup cancelled."
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Setup complete! 🎉"
echo "=========================================="
