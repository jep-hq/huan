from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime
import subprocess
import os
from app.database import SessionLocal
from app.models import SparkJob, JobStatus
from app.config import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_spark_job(self, job_id: str, db_job_id: int):
    """
    Run Spark job as Celery task

    Args:
        job_id: Unique job identifier
        db_job_id: Database record ID

    Returns:
        dict: Job result with status and output
    """
    db = SessionLocal()

    try:
        # Get job from database
        job = db.query(SparkJob).filter(SparkJob.id == db_job_id).first()
        if not job:
            raise ValueError(f"Job {db_job_id} not found")

        # Update status to RUNNING
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        print(f"Starting Spark job: {job_id}")

        # Prepare spark-submit command
        spark_submit_cmd = [
            "/opt/spark/bin/spark-submit",
            "--master", settings.spark_master_url,
            "--deploy-mode", "client",
            "--conf", "spark.driver.memory=1g",
            "--conf", "spark.executor.memory=2g",
            "/opt/spark-apps/spark_job.py",
            job_id
        ]

        print(f"Running command: {' '.join(spark_submit_cmd)}")

        # Run Spark job
        result = subprocess.run(
            spark_submit_cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        # Parse output
        stdout = result.stdout
        stderr = result.stderr

        if result.returncode == 0:
            # Extract result from output
            job_result = None
            for line in stdout.split('\n'):
                if line.startswith("RESULT:"):
                    job_result = line.replace("RESULT:", "").strip()
                    break

            if not job_result:
                job_result = "Job completed successfully"

            # Update status to COMPLETED
            job.status = JobStatus.COMPLETED
            job.result = job_result
            job.completed_at = datetime.utcnow()
            db.commit()

            print(f"Spark job {job_id} completed successfully")

            # Chain to post-processing task
            post_process_job.delay(job_id, db_job_id, job_result)

            return {
                "status": "success",
                "job_id": job_id,
                "result": job_result
            }
        else:
            # Job failed
            error_msg = f"Spark job failed with return code {result.returncode}\n{stderr}"
            job.status = JobStatus.FAILED
            job.error_message = error_msg[:1000]  # Limit error message length
            job.completed_at = datetime.utcnow()
            db.commit()

            print(f"Spark job {job_id} failed: {error_msg}")

            return {
                "status": "failed",
                "job_id": job_id,
                "error": error_msg
            }

    except subprocess.TimeoutExpired:
        # Handle timeout
        error_msg = "Spark job timed out after 1 hour"
        job.status = JobStatus.FAILED
        job.error_message = error_msg
        job.completed_at = datetime.utcnow()
        db.commit()

        print(f"Spark job {job_id} timed out")

        return {
            "status": "failed",
            "job_id": job_id,
            "error": error_msg
        }

    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Error running Spark job: {str(e)}"
        print(error_msg)

        try:
            job.status = JobStatus.FAILED
            job.error_message = error_msg[:1000]
            job.completed_at = datetime.utcnow()
            db.commit()
        except:
            pass

        # Retry the task if retries are available
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "job_id": job_id,
                "error": f"Max retries exceeded: {error_msg}"
            }
    finally:
        db.close()


@shared_task
def post_process_job(job_id: str, db_job_id: int, result: str):
    """
    Post-processing task that runs after Spark job completes

    Args:
        job_id: Unique job identifier
        db_job_id: Database record ID
        result: Result from Spark job

    This is where you can add additional processing:
    - Send notifications (email, Slack, etc.)
    - Update other databases
    - Trigger downstream workflows
    - Generate reports
    - Archive results
    """
    print(f"Post-processing job {job_id}")
    print(f"Job result: {result}")

    db = SessionLocal()
    try:
        job = db.query(SparkJob).filter(SparkJob.id == db_job_id).first()
        if job:
            print(f"Job {job_id} completed for user {job.user_id}")
            print(f"Status: {job.status}")
            print(f"Result: {job.result}")

            # TODO: Add your post-processing logic here
            # Examples:
            # - send_email_notification(job.user_id, job_id, result)
            # - update_analytics_database(result)
            # - trigger_ml_model_training(result)
            # - send_webhook(job_id, result)

            print(f"Post-processing completed for job {job_id}")
    finally:
        db.close()


@shared_task
def cleanup_old_jobs():
    """
    Cleanup task that runs periodically to remove old completed jobs
    This task is scheduled in celery_app.py beat_schedule
    """
    from datetime import timedelta

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # Delete jobs older than 30 days
        deleted_count = db.query(SparkJob).filter(
            SparkJob.completed_at < cutoff_date,
            SparkJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED])
        ).delete()

        db.commit()
        print(f"Cleaned up {deleted_count} old jobs")

        return {"deleted_count": deleted_count}
    finally:
        db.close()


@shared_task
def test_task():
    """Simple test task to verify Celery is working"""
    print("Test task executed successfully!")
    return {"status": "success", "message": "Celery is working!"}
