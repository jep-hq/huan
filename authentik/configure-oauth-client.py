#!/usr/bin/env python3
"""
Configure Authentik OAuth2 Provider redirect URIs via API
This script runs as part of container startup to set redirect URIs that can't be set via blueprints
"""
import os
import sys
import time
import requests
from requests.auth import HTTPBasicAuth

# Configuration from environment
AUTHENTIK_URL = os.getenv('AUTHENTIK_URL', 'http://authentik-server:9000')
AUTHENTIK_TOKEN = os.getenv('AUTHENTIK_BOOTSTRAP_TOKEN', '')
CLIENT_ID = os.getenv('AUTHENTIK_CLIENT_ID', 'huan-client-changeme')
REDIRECT_URIS = os.getenv('AUTHENTIK_REDIRECT_URI', 'http://localhost:3000/auth/callback').split(',')

def wait_for_authentik(max_retries=30, delay=2):
    """Wait for Authentik to be ready"""
    print(f"Waiting for Authentik at {AUTHENTIK_URL}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{AUTHENTIK_URL}/-/health/ready/", timeout=5)
            if response.status_code == 200:
                print("✓ Authentik is ready")
                return True
        except requests.RequestException:
            pass

        if i < max_retries - 1:
            time.sleep(delay)
            print(f"  Retry {i+1}/{max_retries}...")

    print("✗ Authentik failed to become ready")
    return False

def get_provider_by_client_id(client_id):
    """Find OAuth2 provider by client ID"""
    headers = {'Authorization': f'Bearer {AUTHENTIK_TOKEN}'}

    try:
        response = requests.get(
            f"{AUTHENTIK_URL}/api/v3/providers/oauth2/",
            headers=headers,
            params={'client_id': client_id},
            timeout=10
        )
        response.raise_for_status()

        results = response.json().get('results', [])
        if results:
            return results[0]
        return None

    except requests.RequestException as e:
        print(f"✗ Error fetching provider: {e}")
        return None

def update_provider_redirect_uris(provider_id, redirect_uris):
    """Update provider's redirect URIs"""
    headers = {
        'Authorization': f'Bearer {AUTHENTIK_TOKEN}',
        'Content-Type': 'application/json'
    }

    # First get the current provider config
    try:
        response = requests.get(
            f"{AUTHENTIK_URL}/api/v3/providers/oauth2/{provider_id}/",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        provider_data = response.json()

        # Update redirect_uris field
        provider_data['redirect_uris'] = '\n'.join(redirect_uris)

        # Send PATCH request
        response = requests.patch(
            f"{AUTHENTIK_URL}/api/v3/providers/oauth2/{provider_id}/",
            headers=headers,
            json={'redirect_uris': '\n'.join(redirect_uris)},
            timeout=10
        )
        response.raise_for_status()

        print(f"✓ Updated redirect URIs: {redirect_uris}")
        return True

    except requests.RequestException as e:
        print(f"✗ Error updating provider: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text}")
        return False

def main():
    if not AUTHENTIK_TOKEN:
        print("✗ AUTHENTIK_BOOTSTRAP_TOKEN not set")
        sys.exit(1)

    if not wait_for_authentik():
        sys.exit(1)

    # Give blueprints time to apply
    print("Waiting for blueprints to apply...")
    time.sleep(5)

    provider = get_provider_by_client_id(CLIENT_ID)
    if not provider:
        print(f"✗ Provider with client_id '{CLIENT_ID}' not found")
        print("  Make sure the blueprint has been applied")
        sys.exit(1)

    print(f"✓ Found provider: {provider['name']} (ID: {provider['pk']})")

    if update_provider_redirect_uris(provider['pk'], REDIRECT_URIS):
        print("✓ OAuth2 provider configured successfully")
        sys.exit(0)
    else:
        print("✗ Failed to configure OAuth2 provider")
        sys.exit(1)

if __name__ == '__main__':
    main()
