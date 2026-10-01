# Authentik Auto-Configuration with Blueprints

## Overview

HUAN uses **Authentik Blueprints** to automatically configure the OAuth2/OIDC application during startup. No manual configuration needed!

## What Gets Auto-Configured

✅ **OAuth2/OIDC Provider**
- Client Type: Confidential
- Client ID: `huan-client-changeme` (development default)
- Client Secret: `huan-secret-changeme-use-secure-random-value` (development default)
- Redirect URIs: `http://localhost:3000/auth/callback`, `http://frontend:3000/auth/callback`
- Scopes: `openid`, `email`, `profile`
- Token validity periods

✅ **Application**
- Name: HUAN
- Slug: `huan`
- Launch URL: `http://localhost:3000`
- Provider: Linked to OAuth2 provider above

## How It Works

1. **Blueprint file** located at `authentik/blueprints/huan-app.yaml`
2. **Mounted** into Authentik containers via Docker volumes
3. **Auto-discovered** on startup via `AUTHENTIK_BLUEPRINTS_DIR`
4. **Applied automatically** when Authentik starts

## Files

```
authentik/
└── blueprints/
    ├── huan-app.yaml                      # Active blueprint (development)
    └── huan-app-production.yaml.example   # Production template
```

## Development Setup

### First Time Setup

1. **Start services**:
   ```bash
   make dev
   # or
   docker compose up -d
   ```

2. **Wait for Authentik** to fully start (~30 seconds):
   ```bash
   docker compose logs -f authentik-server
   # Wait for "Applying blueprints" messages
   ```

3. **Access Authentik** at http://localhost:9000
   - Initial setup wizard will appear
   - Create admin account
   - Blueprint will be automatically applied

4. **Verify application** was created:
   - Go to Applications → Applications
   - Should see "HUAN" application
   - Go to Applications → Providers
   - Should see "HUAN OAuth2 Provider"

5. **Update credentials** (optional):
   - If you want different credentials, edit the blueprint
   - Or manually update in Authentik UI
   - Update `.env` to match

### Using Default Credentials

The blueprint creates these default credentials (development only):
```
Client ID: huan-client-changeme
Client Secret: huan-secret-changeme-use-secure-random-value
```

These are already set in `.env.development`, so everything should work out of the box!

## Production Setup

### Option 1: Custom Blueprint (Recommended)

1. **Copy the production template**:
   ```bash
   cp authentik/blueprints/huan-app-production.yaml.example \
      authentik/blueprints/huan-app-production.yaml
   ```

2. **Generate secure credentials**:
   ```bash
   # Client ID (40 character hex)
   openssl rand -hex 20

   # Client Secret (64+ character base64)
   openssl rand -base64 64 | tr -d '\n'
   ```

3. **Edit the blueprint**:
   - Replace `REPLACE_WITH_SECURE_CLIENT_ID`
   - Replace `REPLACE_WITH_SECURE_CLIENT_SECRET`
   - Update redirect URIs to production URLs
   - Update launch URL

4. **Update `.env`**:
   ```bash
   AUTHENTIK_CLIENT_ID=<your-generated-client-id>
   AUTHENTIK_CLIENT_SECRET=<your-generated-client-secret>
   ```

5. **Rename/remove development blueprint**:
   ```bash
   mv authentik/blueprints/huan-app.yaml \
      authentik/blueprints/huan-app.yaml.dev
   ```

6. **Deploy**:
   ```bash
   make prod
   ```

### Option 2: Manual Configuration

If you prefer manual setup:

1. **Disable blueprint**:
   ```bash
   mv authentik/blueprints/huan-app.yaml \
      authentik/blueprints/huan-app.yaml.disabled
   ```

2. **Start Authentik**:
   ```bash
   docker compose up -d
   ```

3. **Configure manually** in Authentik UI
   - See `OAUTH_FLOW.md` for manual setup instructions

4. **Update `.env`** with credentials from Authentik

## Customizing the Blueprint

### Redirect URIs

Edit `huan-app.yaml`:
```yaml
redirect_uris: |-
  http://localhost:3000/auth/callback
  http://frontend:3000/auth/callback
  https://yourdomain.com/auth/callback  # Add production URL
```

### Token Validity

```yaml
access_code_validity: hours=1          # How long auth code is valid
access_token_validity: minutes=10      # How long access token is valid
refresh_token_validity: days=30        # How long refresh token is valid
```

### Scopes

Add additional OAuth2 scopes:
```yaml
property_mappings:
  - !Find [authentik_providers_oauth2.scopemapping, [scope_name, openid]]
  - !Find [authentik_providers_oauth2.scopemapping, [scope_name, email]]
  - !Find [authentik_providers_oauth2.scopemapping, [scope_name, profile]]
  - !Find [authentik_providers_oauth2.scopemapping, [scope_name, offline_access]]  # For refresh tokens
```

### Client Type

For public clients (mobile apps, CLIs):
```yaml
client_type: public  # Instead of 'confidential'
```

## Blueprint Syntax Reference

### Finding Existing Objects

```yaml
!Find [model, [field, value]]
```

Example:
```yaml
authorization_flow: !Find [authentik_flows.flow, [slug, default-authorization-flow]]
```

### Referencing Other Entries

```yaml
!KeyOf entry-id
```

Example:
```yaml
provider: !KeyOf huan-oauth2-provider
```

### Multi-line Strings

```yaml
redirect_uris: |-
  http://localhost:3000/auth/callback
  http://frontend:3000/auth/callback
```

## Verifying Blueprint Application

### Check Logs

```bash
# Watch for blueprint application
docker compose logs -f authentik-worker | grep -i blueprint

# Should see:
# Successfully applied blueprint <name>
# Applied 2 instances
```

### Check Authentik UI

1. Go to **Admin Interface** → **System** → **Blueprints**
2. Look for "HUAN Application Setup"
3. Status should be "Successful"

### Check Application

1. Go to **Applications** → **Applications**
2. "HUAN" should appear
3. Click to verify provider is linked

## Updating Blueprints

### After First Run

Blueprints are **idempotent** - they can be safely re-applied. Changes will update existing objects.

To update:
1. Edit `authentik/blueprints/huan-app.yaml`
2. Restart Authentik:
   ```bash
   docker compose restart authentik-server authentik-worker
   ```
3. Blueprint will automatically re-apply

### Force Re-apply

If blueprint doesn't auto-update:

```bash
# Enter Authentik server container
docker compose exec authentik-server bash

# Apply blueprint manually
ak apply_blueprint /blueprints/custom/huan-app.yaml

# Exit
exit
```

## Troubleshooting

### Blueprint not applied

**Check if directory is mounted**:
```bash
docker compose exec authentik-server ls -la /blueprints/custom/
# Should show huan-app.yaml
```

**Check environment variable**:
```bash
docker compose exec authentik-server env | grep BLUEPRINTS
# Should show: AUTHENTIK_BLUEPRINTS_DIR=/blueprints/custom
```

**Check logs**:
```bash
docker compose logs authentik-worker | grep -i blueprint
```

### "Object not found" errors

Blueprint references might be wrong. Common issues:
- Flow slug doesn't exist
- Certificate name doesn't match
- Scope mapping not found

Solution: Check Authentik UI for actual object names/slugs.

### Credentials don't match

If blueprint credentials don't match `.env`:

**Option 1**: Update blueprint to match `.env`
**Option 2**: Update `.env` to match blueprint
**Option 3**: Update both to new secure values

Then restart:
```bash
docker compose restart authentik-server authentik-worker backend frontend
```

## Advanced: Multiple Environments

Create different blueprints for different environments:

```
authentik/blueprints/
├── huan-app-dev.yaml
├── huan-app-staging.yaml
└── huan-app-prod.yaml
```

Activate the one you need by renaming or using different compose files.

## Security Notes

⚠️ **Development Defaults**
- Default credentials in `huan-app.yaml` are for **development only**
- Never use these in production
- Always generate secure random credentials for production

⚠️ **Blueprint Security**
- Blueprints are **committed to git** (should be)
- Don't put production secrets directly in blueprints
- Use the production template and generate unique credentials
- Consider using environment variables or secrets management

✅ **Best Practice**
1. Use default blueprint for development
2. Create environment-specific production blueprint
3. Generate unique credentials per environment
4. Keep production blueprint separate (not in git)
5. Use secrets management for production credentials

## Resources

- [Authentik Blueprints Documentation](https://goauthentik.io/docs/flow/blueprints/)
- [OAuth2 Provider Reference](https://goauthentik.io/integrations/services/oauth/)
- `OAUTH_FLOW.md` - OAuth flow documentation

---

**Summary**: Authentik will automatically configure the HUAN OAuth2 application on first startup. No manual clicking required! 🎉
