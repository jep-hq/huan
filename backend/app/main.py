from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from datetime import timedelta
import secrets
import httpx
from typing import List

from app.config import settings
from app.database import get_db, engine, Base
from app import models, schemas, auth
from app.celery_app import celery_app  # Import celery app first
from app.tasks import run_spark_job, test_task

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Huan API", version="1.0.0")

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth configuration for Zitadel
oauth = OAuth()
oauth.register(
    name='zitadel',
    client_id=settings.zitadel_client_id,
    client_secret=settings.zitadel_client_secret,
    server_metadata_url=f'{settings.zitadel_url}/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# No longer need Redis client for job queue - Celery handles it


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Huan API is running", "status": "healthy"}


@app.get("/test-celery")
async def test_celery_endpoint():
    """Test Celery task execution"""
    task = test_task.delay()
    return {
        "message": "Celery test task queued",
        "task_id": task.id,
        "status": "Check Flower UI at http://localhost:5555"
    }


@app.get("/auth/login")
async def login(request: Request):
    """Redirect to Zitadel login"""
    redirect_uri = settings.zitadel_redirect_uri
    return await oauth.zitadel.authorize_redirect(request, redirect_uri)


@app.post("/auth/callback")
async def auth_callback_post(
    code: str,
    redirect_uri: str,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Vue frontend
    Exchange authorization code for tokens
    """
    try:
        # Exchange code for token with Zitadel
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{settings.zitadel_url}/oauth/v2/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": settings.zitadel_client_id,
                    "client_secret": settings.zitadel_client_secret,
                }
            )
            token_response.raise_for_status()
            token_data = token_response.json()

            # Get user info
            user_response = await client.get(
                f"{settings.zitadel_url}/oidc/v1/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_response.raise_for_status()
            user_info = user_response.json()

        # Get or create user
        user = auth.get_or_create_user(db, user_info)

        # Create JWT token
        access_token = auth.create_access_token(
            data={"sub": user.id, "authentik_id": user.authentik_id},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "authentik_id": user.authentik_id,
            }
        }
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token exchange failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@app.get("/auth/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle OAuth callback from Zitadel"""
    try:
        token = await oauth.zitadel.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not get user info from Zitadel"
            )

        # Get or create user
        user = auth.get_or_create_user(db, user_info)

        # Create JWT token
        access_token = auth.create_access_token(
            data={"sub": user.id, "authentik_id": user.authentik_id},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@app.post("/auth/token", response_model=schemas.Token)
async def authenticate_with_zitadel(
    zitadel_token: str,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Zitadel access token and get JWT token
    This is for direct authentication from frontend
    """
    # Verify token with Zitadel
    user_info = await auth.verify_zitadel_token(zitadel_token)

    # Get or create user
    user = auth.get_or_create_user(db, user_info)

    # Create JWT token
    access_token = auth.create_access_token(
        data={"sub": user.id, "authentik_id": user.authentik_id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.User)
async def get_current_user(
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get current user information"""
    return current_user


@app.post("/api-keys", response_model=schemas.APIKey)
async def create_api_key(
    api_key_data: schemas.APIKeyCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user"""
    # Generate a secure API key
    key = f"huan_{secrets.token_urlsafe(32)}"

    api_key = models.APIKey(
        key=key,
        name=api_key_data.name,
        user_id=current_user.id
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key


@app.get("/api-keys", response_model=List[schemas.APIKey])
async def list_api_keys(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user"""
    api_keys = db.query(models.APIKey).filter(
        models.APIKey.user_id == current_user.id
    ).all()
    return api_keys


@app.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(models.APIKey).filter(
        models.APIKey.id == api_key_id,
        models.APIKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted successfully"}


@app.post("/spark/jobs", response_model=schemas.SparkJob)
async def create_spark_job(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create and trigger a Spark job using Celery
    This will run the Spark job in the background
    """
    # Generate unique job ID
    job_id = f"job_{secrets.token_urlsafe(16)}"

    # Create job record
    spark_job = models.SparkJob(
        user_id=current_user.id,
        job_id=job_id,
        status=models.JobStatus.PENDING
    )
    db.add(spark_job)
    db.commit()
    db.refresh(spark_job)

    # Trigger Celery task asynchronously
    run_spark_job.delay(job_id, spark_job.id)

    return spark_job
@app.get("/spark/jobs", response_model=List[schemas.SparkJob])
async def list_spark_jobs(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """List all Spark jobs for the current user"""
    jobs = db.query(models.SparkJob).filter(
        models.SparkJob.user_id == current_user.id
    ).order_by(models.SparkJob.created_at.desc()).all()
    return jobs


@app.get("/spark/jobs/{job_id}", response_model=schemas.SparkJob)
async def get_spark_job(
    job_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific Spark job"""
    job = db.query(models.SparkJob).filter(
        models.SparkJob.job_id == job_id,
        models.SparkJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
