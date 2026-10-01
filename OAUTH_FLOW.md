# OAuth2 / OIDC Authentication Flow

## Overview

HUAN uses the **Authorization Code Flow** for OAuth2/OIDC authentication with Authentik. This is the recommended pattern for Single Page Applications (SPAs).

## Flow Diagram

```
┌──────────┐                                     ┌──────────┐
│          │  1. User clicks "Login"             │          │
│ Frontend │────────────────────────────────────▶│ Frontend │
│  (Vue)   │                                     │  Router  │
│          │                                     │          │
└──────────┘                                     └──────────┘
     │                                                 │
     │ 2. Redirect to Authentik                       │
     │    with redirect_uri:                          │
     │    http://localhost:3000/auth/callback         │
     │                                                 │
     └────────────────────────────────────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │   Authentik   │
                        │  Login Page   │
                        │               │
                        └───────────────┘
                                │
                    3. User authenticates
                                │
                                ▼
                        ┌───────────────┐
                        │   Authentik   │
                        │  redirects to │
                        │   Frontend    │
                        └───────────────┘
                                │
                                │ 4. With authorization code
                                │    ?code=xxx&state=yyy
                                ▼
                        ┌───────────────┐
                        │   Frontend    │
                        │   /auth/      │
                        │   callback    │
                        └───────────────┘
                                │
                                │ 5. POST code to Backend
                                │    /auth/callback
                                ▼
                        ┌───────────────┐
                        │   Backend     │
                        │   API         │
                        └───────────────┘
                                │
                    6. Exchange code for tokens
                    with Authentik (server-to-server)
                                │
                                ▼
                        ┌───────────────┐
                        │   Authentik   │
                        │   Token       │
                        │   Endpoint    │
                        └───────────────┘
                                │
                    7. Returns access token
                    & user info
                                │
                                ▼
                        ┌───────────────┐
                        │   Backend     │
                        │  - Creates    │
                        │    user       │
                        │  - Issues JWT │
                        └───────────────┘
                                │
                    8. Returns JWT to Frontend
                                │
                                ▼
                        ┌───────────────┐
                        │   Frontend    │
                        │  - Stores JWT │
                        │  - Redirects  │
                        │    to app     │
                        └───────────────┘
```

## Redirect URIs Configuration

### ✅ Correct Configuration

**In Authentik Application Settings:**
- Redirect URIs: `http://localhost:3000/auth/callback` (Frontend)
- For production: `https://yourdomain.com/auth/callback`

**In Frontend (`useAuthentik.ts`):**
```typescript
const redirectUri = `${window.location.origin}/auth/callback`
// Results in: http://localhost:3000/auth/callback
```

**In Backend (`config.py`):**
```python
authentik_redirect_uri: str = "http://localhost:3000/auth/callback"
# This is for documentation/reference - the actual redirect happens via frontend
```

### ❌ Common Mistakes

**DON'T set redirect_uri to backend:**
```
http://localhost:8001/auth/callback  # ❌ WRONG
```

**Why?** Because:
1. User's browser needs to be redirected to a page that can handle the response
2. Frontend (SPA) is the user-facing application
3. Backend should only handle server-to-server token exchange

## Endpoints

### Frontend Routes

**`GET /auth/callback`** (Frontend Vue Route)
- Receives authorization code from Authentik
- Extracts `code` and `state` from URL params
- Calls backend to exchange code for JWT

### Backend API Endpoints

**`POST /auth/callback`**
- Accepts: `{ code, redirect_uri }`
- Exchanges code with Authentik for access token
- Gets user info from Authentik
- Creates/updates user in database
- Returns JWT token

**`GET /auth/login`** (Optional - not used in current flow)
- Direct backend-initiated OAuth flow
- Not recommended for SPAs

**`GET /users/me`**
- Protected endpoint requiring JWT
- Returns current user information

## Security Features

### CSRF Protection
- Frontend generates random `state` parameter
- Stores in sessionStorage
- Validates on callback

### Token Storage
- JWT stored in localStorage (for persistence)
- Include in API requests via Authorization header
- Axios interceptor can handle this automatically

### Token Exchange
- Authorization code is single-use
- Exchange happens server-to-server (backend ↔ Authentik)
- Client secret never exposed to browser

## Configuration in Authentik

When creating the OAuth2/OIDC Provider in Authentik:

1. **Client Type**: Confidential (for server-side apps with client secret)
2. **Authorization Grant Type**: `authorization-code`
3. **Redirect URIs**:
   ```
   http://localhost:3000/auth/callback
   ```
   (Add production URL when deploying)
4. **Scopes**: `openid email profile`

## Environment Variables

```bash
# Backend connects to Authentik (internal Docker network)
AUTHENTIK_URL=http://authentik-server:9000

# Frontend connects to Authentik (browser/external)
NUXT_PUBLIC_AUTHENTIK_URL=http://localhost:9000

# OAuth2 Credentials
AUTHENTIK_CLIENT_ID=<your-client-id>
AUTHENTIK_CLIENT_SECRET=<your-client-secret>

# Redirect URI (frontend callback URL)
AUTHENTIK_REDIRECT_URI=http://localhost:3000/auth/callback
```

## Production Considerations

### HTTPS
- All URLs must use HTTPS in production
- Update redirect URIs in Authentik
- Update environment variables

### CORS
- Backend must allow frontend origin
- Already configured in `main.py`:
  ```python
  allow_origins=["http://localhost:3000", "http://frontend:3000"]
  ```
- Add production domain

### Domains
Development:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8001`
- Authentik: `http://localhost:9000`

Production Example:
- Frontend: `https://app.yourdomain.com`
- Backend: `https://api.yourdomain.com`
- Authentik: `https://auth.yourdomain.com`

Update environment variables:
```bash
AUTHENTIK_REDIRECT_URI=https://app.yourdomain.com/auth/callback
NUXT_PUBLIC_API_URL=https://api.yourdomain.com
NUXT_PUBLIC_AUTHENTIK_URL=https://auth.yourdomain.com
```

## Troubleshooting

### "Invalid redirect_uri"
- Check Authentik application settings
- Ensure redirect URI matches exactly (including protocol and trailing slash)
- Frontend and Authentik must agree on the URI

### "Invalid state parameter"
- State verification failed (CSRF protection)
- Clear browser sessionStorage
- Try logging in again

### CORS errors
- Check backend CORS configuration
- Ensure frontend origin is allowed
- Check browser console for details

### Token exchange fails
- Verify `AUTHENTIK_CLIENT_ID` and `AUTHENTIK_CLIENT_SECRET`
- Check backend can reach Authentik (Docker network)
- Review backend logs: `make logs` or `docker compose logs backend`

## Testing the Flow

1. Start services:
   ```bash
   make dev
   ```

2. Open frontend:
   ```
   http://localhost:3000
   ```

3. Click "Login"

4. Should redirect to:
   ```
   http://localhost:9000/application/o/authorize/?client_id=...&redirect_uri=http://localhost:3000/auth/callback...
   ```

5. After authentication, redirected to:
   ```
   http://localhost:3000/auth/callback?code=...&state=...
   ```

6. Frontend automatically calls backend and gets JWT

7. Redirected to app homepage with authenticated session

## Code References

- **Frontend Auth Logic**: `/smlt/composables/useAuthentik.ts`
- **Frontend Callback Page**: `/smlt/app/pages/auth/callback.vue`
- **Backend Auth Endpoints**: `/backend/app/main.py` (lines 70-165)
- **Backend Auth Logic**: `/backend/app/auth.py`
- **Backend Config**: `/backend/app/config.py`

---

**Summary**: The redirect_uri should **ALWAYS point to the frontend** in an Authorization Code Flow for SPAs. The backend only handles server-to-server token exchange.
