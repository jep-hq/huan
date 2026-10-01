# Migration Guide: Authentik to Zitadel

This guide explains how to migrate from the self-hosted Authentik instance to an existing Zitadel instance.

## Overview

The migration involves:
1. Removing Authentik containers from docker-compose
2. Updating backend OAuth configuration
3. Updating frontend authentication composable
4. Configuring Zitadel OAuth application
5. Updating environment variables

## Changes Made

### 1. Docker Compose Changes

**Removed services:**
- `authentik-db` - Authentik PostgreSQL database
- `authentik-redis` - Authentik Redis cache
- `authentik-server` - Authentik web server
- `authentik-worker` - Authentik background worker

**Removed volumes:**
- `authentik_db_data`
- `authentik_media`
- `authentik_templates`
- `authentik_certs`

**Updated services:**
- `backend` - Removed dependency on `authentik-server`, updated env vars
- `frontend` - Updated environment variables

### 2. Backend Changes

#### `backend/app/config.py`
- Replaced `authentik_*` settings with `zitadel_*` settings
- Updated URLs and configuration keys

#### `backend/app/auth.py`
- Renamed `verify_authentik_token()` to `verify_zitadel_token()`
- Updated userinfo endpoint: `/oidc/v1/userinfo`
- Updated `get_or_create_user()` to handle Zitadel user structure

#### `backend/app/main.py`
- Updated OAuth configuration for Zitadel
- Changed OIDC discovery URL: `/.well-known/openid-configuration`
- Updated token endpoint: `/oauth/v2/token`
- Updated userinfo endpoint: `/oidc/v1/userinfo`

### 3. Frontend Changes

#### `smlt/composables/useZitadel.ts`
Created new composable replacing `useAuthentik.ts`:
- Authorization endpoint: `/oauth/v2/authorize`
- Logout endpoint: `/oidc/v1/end_session`
- Updated parameter names and structure for Zitadel compatibility

### 4. Environment Variables

Updated `.env` file:
- Removed all `AUTHENTIK_*` variables
- Added `ZITADEL_URL`, `ZITADEL_CLIENT_ID`, `ZITADEL_CLIENT_SECRET`
- Updated frontend public variables

## Zitadel Configuration Required

### Step 1: Create Application in Zitadel

1. Log in to your Zitadel instance
2. Navigate to **Projects** → Select/Create your project
3. Click **New Application**
4. Choose **User Agent** (for Web/SPA) or **Web** depending on your setup
5. Configure the application:

   **Application Name:** `huan` (or your preferred name)
   
   **Redirect URIs:**
   ```
   http://localhost:3000/auth/callback
   http://your-production-domain/auth/callback
   ```
   
   **Post Logout URIs:**
   ```
   http://localhost:3000
   http://your-production-domain
   ```
   
   **Grant Types:**
   - Authorization Code
   - Refresh Token (optional)
   
   **Response Types:**
   - Code

6. After creation, note down:
   - **Client ID**
   - **Client Secret** (if using confidential client)

### Step 2: Configure User Grants

Ensure your Zitadel users have the necessary grants:
1. Go to **Users**
2. Select your user
3. Go to **Grants** tab
4. Add grant for your project/application if not already present

### Step 3: Update Environment Variables

Edit `.env` file with your Zitadel details:

```bash
# Zitadel Configuration
ZITADEL_URL=https://your-zitadel-instance.com
ZITADEL_CLIENT_ID=your-client-id-from-zitadel
ZITADEL_CLIENT_SECRET=your-client-secret-from-zitadel
ZITADEL_REDIRECT_URI=http://localhost:3000/auth/callback

# Frontend (public variables)
NUXT_PUBLIC_ZITADEL_URL=https://your-zitadel-instance.com
NUXT_PUBLIC_ZITADEL_CLIENT_ID=your-client-id-from-zitadel
```

**Important Notes:**
- Use the full URL including `https://` for `ZITADEL_URL`
- The `ZITADEL_URL` should NOT include any path (e.g., no `/oauth/v2`)
- For production, update redirect URIs to match your domain

## Deployment Steps

### 1. Stop Existing Services

```bash
sudo docker compose down
```

### 2. Update Environment Variables

Edit `.env` file with your Zitadel configuration (see above).

### 3. Clean Up Old Volumes (Optional)

If you want to remove Authentik data:

```bash
sudo docker volume rm huan_authentik_db_data
sudo docker volume rm huan_authentik_media
sudo docker volume rm huan_authentik_templates
sudo docker volume rm huan_authentik_certs
```

### 4. Start Services

```bash
sudo docker compose up -d
```

### 5. Update Frontend Code

In your Vue components, replace `useAuthentik` with `useZitadel`:

**Before:**
```typescript
import { useAuthentik } from '~/composables/useAuthentik'
const { login, logout, isAuthenticated } = useAuthentik()
```

**After:**
```typescript
import { useZitadel } from '~/composables/useZitadel'
const { login, logout, isAuthenticated } = useZitadel()
```

## Differences Between Authentik and Zitadel

### API Endpoints

| Purpose | Authentik | Zitadel |
|---------|-----------|---------|
| OIDC Discovery | `/application/o/<app>/.well-known/openid-configuration` | `/.well-known/openid-configuration` |
| Authorization | `/application/o/authorize/` | `/oauth/v2/authorize` |
| Token Exchange | `/application/o/token/` | `/oauth/v2/token` |
| User Info | `/application/o/userinfo/` | `/oidc/v1/userinfo` |
| Logout | `/application/o/<app>/end-session/` | `/oidc/v1/end_session` |

### User Info Response

**Authentik:**
```json
{
  "sub": "user-id",
  "email": "user@example.com",
  "preferred_username": "username",
  "nickname": "nickname",
  "given_name": "John",
  "family_name": "Doe"
}
```

**Zitadel:**
```json
{
  "sub": "user-id",
  "email": "user@example.com",
  "name": "John Doe",
  "preferred_username": "username",
  "given_name": "John",
  "family_name": "Doe"
}
```

## Database Considerations

The existing database schema uses `authentik_id` field in the `User` model. This field is being reused for Zitadel user IDs. If you want to rename it:

1. Create a migration to rename the column:
   ```python
   # In backend directory
   alembic revision -m "rename authentik_id to idp_id"
   ```

2. Update the migration file to rename the column
3. Update `backend/app/models.py` to use the new field name
4. Run the migration:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

## Testing the Migration

### 1. Test Authentication Flow

1. Navigate to `http://localhost:3000`
2. Click login
3. Should redirect to Zitadel login page
4. After login, should redirect back to your app
5. Verify user information is displayed correctly

### 2. Test API Calls

```bash
# Get token
curl -X POST http://localhost:8001/auth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "authorization_code", "redirect_uri": "http://localhost:3000/auth/callback"}'

# Test protected endpoint
curl -X GET http://localhost:8001/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Test Logout

1. Click logout in the UI
2. Should redirect to Zitadel logout page
3. Should be redirected back to home page
4. Verify user is logged out

## Rollback Plan

If you need to rollback to Authentik:

1. Restore the original `docker-compose.yml` from git:
   ```bash
   git checkout HEAD -- docker-compose.yml
   ```

2. Restore backend files:
   ```bash
   git checkout HEAD -- backend/app/config.py backend/app/auth.py backend/app/main.py
   ```

3. Restore frontend:
   ```bash
   git checkout HEAD -- smlt/composables/
   ```

4. Restore `.env` file from backup

5. Restart services:
   ```bash
   sudo docker compose up -d
   ```

## Troubleshooting

### Issue: "Could not validate Zitadel token"

**Cause:** Invalid client credentials or wrong Zitadel URL

**Solution:**
1. Verify `ZITADEL_URL` is correct (including `https://`)
2. Check client ID and secret match Zitadel application
3. Ensure redirect URI is registered in Zitadel

### Issue: "Invalid state parameter"

**Cause:** CSRF state mismatch

**Solution:**
1. Clear browser session storage
2. Try login again
3. Check if cookies are enabled

### Issue: User info missing fields

**Cause:** Zitadel user info response structure different

**Solution:**
1. Check what fields Zitadel returns: `GET /oidc/v1/userinfo`
2. Update `get_or_create_user()` in `backend/app/auth.py` to handle missing fields

### Issue: Redirect URI mismatch

**Cause:** Redirect URI not registered in Zitadel

**Solution:**
1. Go to Zitadel → Your Application → Redirect URIs
2. Add the exact URI: `http://localhost:3000/auth/callback`
3. Save changes

## Additional Resources

- [Zitadel Documentation](https://zitadel.com/docs)
- [Zitadel OAuth/OIDC Guide](https://zitadel.com/docs/guides/integrate/oauth)
- [OAuth 2.0 Authorization Code Flow](https://oauth.net/2/grant-types/authorization-code/)
- [OpenID Connect Core Spec](https://openid.net/specs/openid-connect-core-1_0.html)

## Support

If you encounter issues:
1. Check Zitadel logs for errors
2. Check backend logs: `docker compose logs backend`
3. Check browser console for frontend errors
4. Verify environment variables are correctly set
