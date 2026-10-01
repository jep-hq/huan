# HUAN - Environment Setup Guide

This project uses environment variables for configuration to support both development and production deployments securely.

## 🚀 Quick Start

### For Development

1. **Copy the development environment file:**
   ```bash
   cp .env.development .env
   ```

2. **Update Authentik credentials** (after first setup):
   - Start the services: `docker compose up -d`
   - Access Authentik at http://localhost:9000
   - Create an OAuth2/OIDC provider application
   - Copy the Client ID and Client Secret
   - Update `.env` with your credentials

3. **Start the stack:**
   ```bash
   docker compose up -d
   ```

### For Production

1. **Generate secure secrets:**
   ```bash
   ./generate-secrets.sh
   ```

2. **Create production environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Fill in the values:**
   - Copy the generated secrets from step 1
   - Set `ENVIRONMENT=production`
   - Configure OAuth2 credentials from Authentik
   - Update URLs to match your domain

4. **Deploy:**
   ```bash
   docker compose up -d
   ```

## 📁 Environment Files

| File | Purpose | Git Tracked? |
|------|---------|--------------|
| `.env.example` | Template with all variables | ✅ Yes |
| `.env.development` | Safe defaults for local dev | ✅ Yes |
| `.env` | Your actual configuration | ❌ No (gitignored) |
| `.env.production` | Production configuration | ❌ No (gitignored) |

## 🔐 Security Best Practices

### Required Secrets

These **must** be changed from defaults in production:

1. **POSTGRES_PASSWORD** - Database password
2. **AUTHENTIK_DB_PASSWORD** - Authentik database password
3. **AUTHENTIK_SECRET_KEY** - Authentik encryption key (60+ chars)
4. **SECRET_KEY** - Backend JWT signing key (32+ chars)
5. **AUTHENTIK_CLIENT_SECRET** - OAuth2 client secret

### Generating Secure Secrets

```bash
# Generate all secrets at once
./generate-secrets.sh

# Or generate individually:
openssl rand -base64 60  # For AUTHENTIK_SECRET_KEY
openssl rand -base64 32  # For SECRET_KEY
openssl rand -hex 32     # For passwords
```

### Never Commit:
- `.env` files with real credentials
- Client secrets
- Database passwords
- JWT signing keys

## 🔧 Configuration Variables

### Environment Control
- `ENVIRONMENT` - Set to `development` or `production`

### Database
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password

### Authentik (SSO/Auth)
- `AUTHENTIK_SECRET_KEY` - Encryption key for Authentik
- `AUTHENTIK_DB_PASSWORD` - Authentik's database password
- `AUTHENTIK_CLIENT_ID` - OAuth2 client ID
- `AUTHENTIK_CLIENT_SECRET` - OAuth2 client secret
- `AUTHENTIK_URL` - Internal Authentik URL (service-to-service)
- `AUTHENTIK_PUBLIC_URL` - External Authentik URL (browser access)

### Backend
- `SECRET_KEY` - JWT signing secret
- `SPARK_MASTER_URL` - Spark cluster URL

### Frontend
- `NUXT_PUBLIC_API_URL` - Backend API URL (public)
- `NUXT_PUBLIC_AUTHENTIK_URL` - Authentik URL (public)
- `NUXT_PUBLIC_AUTHENTIK_CLIENT_ID` - OAuth2 client ID (safe to be public)

### Port Mappings (Optional)
All services have configurable ports:
- `POSTGRES_PORT` (default: 5432)
- `REDIS_PORT` (default: 6380)
- `AUTHENTIK_HTTP_PORT` (default: 9000)
- `AUTHENTIK_HTTPS_PORT` (default: 9443)
- `BACKEND_PORT` (default: 8001)
- `FRONTEND_PORT` (default: 3000)
- `FLOWER_PORT` (default: 5555)
- `SPARK_MASTER_UI_PORT` (default: 8081)
- `SPARK_MASTER_PORT` (default: 7077)

## 🔄 Switching Environments

### Development → Production

1. Create new `.env` from `.env.example`
2. Generate new secrets with `./generate-secrets.sh`
3. Set `ENVIRONMENT=production`
4. Update all URLs to production domains
5. Restart: `docker compose down && docker compose up -d`

### Using Multiple Environments

```bash
# Use development
cp .env.development .env
docker compose up -d

# Switch to staging
cp .env.staging .env
docker compose down && docker compose up -d

# Switch to production
cp .env.production .env
docker compose down && docker compose up -d
```

## 📊 Service URLs (Development)

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web application |
| Backend API | http://localhost:8001 | REST API |
| Authentik | http://localhost:9000 | Authentication/SSO |
| Flower | http://localhost:5555 | Celery monitoring |
| Spark Master UI | http://localhost:8081 | Spark cluster UI |

## 🐛 Troubleshooting

### "Required environment variable not set"
- Check that `.env` file exists in project root
- Verify all required variables are defined
- Use `.env.development` as a starting point

### OAuth2/Authentik connection issues
- Ensure `AUTHENTIK_CLIENT_ID` and `AUTHENTIK_CLIENT_SECRET` match Authentik admin panel
- Check that URLs are accessible from containers
- Verify Authentik is fully started before backend

### Database connection errors
- Ensure `POSTGRES_PASSWORD` matches in all services using it
- Wait for health checks to pass
- Check `docker compose logs postgres`

## 📝 Environment Variable Checklist

Before deploying to production:

- [ ] All secrets generated with `./generate-secrets.sh`
- [ ] `ENVIRONMENT=production` is set
- [ ] Database passwords changed from defaults
- [ ] `AUTHENTIK_SECRET_KEY` is 60+ character random string
- [ ] `SECRET_KEY` is 32+ character random string
- [ ] OAuth2 credentials obtained from Authentik admin
- [ ] All URLs updated to production domains
- [ ] `.env` file is gitignored
- [ ] `.env.example` is documented and up-to-date

## 🔒 Production Hardening

Additional steps for production:

1. **Use Docker secrets** instead of environment variables:
   ```yaml
   secrets:
     db_password:
       external: true
   ```

2. **Enable HTTPS** for all public-facing services

3. **Set up proper firewall rules**

4. **Use managed databases** (AWS RDS, Google Cloud SQL, etc.)

5. **Implement secrets rotation** policy

6. **Enable Authentik 2FA** for all users

7. **Review and restrict** `FLOWER_UNAUTHENTICATED_API` (set to `false`)

8. **Set up monitoring** and alerting

9. **Regular security updates** for all container images

10. **Backup strategy** for databases and Authentik media

---

For more information, see the main [README.md](./README.md)
