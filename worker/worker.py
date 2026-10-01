import os
import json
import time
import redis
import subprocess
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import sessionmaker, declarative_base
import enum

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://huan:huan123@postgres:5432/huan")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Spark setup
SPARK_MASTER_URL = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SparkJob(Base):
    __tablename__ = "spark_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    job_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    result = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


def update_job_status(db_session, job_id: str, status: JobStatus,
                      result: str = None, error_message: str = None):
    """Update job status in database"""
    job = db_session.query(SparkJob).filter(SparkJob.job_id == job_id).first()
    if job:
        job.status = status
        if result:
            job.result = result
        if error_message:
            job.error_message = error_message
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        db_session.commit()
        print(f"Updated job {job_id} status to {status}")


def run_spark_job(job_data: dict):
    """
    Run Spark job via spark-submit
    """
    job_id = job_data["job_id"]
    db_job_id = job_data["db_job_id"]

    print(f"Processing job: {job_id}")

    db = SessionLocal()
    try:
        # Update status to RUNNING
        update_job_status(db, job_id, JobStatus.RUNNING)

        # Submit Spark job
        spark_submit_cmd = [
            "/opt/spark/bin/spark-submit",
            "--master", SPARK_MASTER_URL,
            "--deploy-mode", "client",
            "/opt/spark-apps/spark_job.py",
            job_id
        ]

        print(f"Running command: {' '.join(spark_submit_cmd)}")

        # Run the Spark job
        process = subprocess.Popen(
            spark_submit_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        print(f"Spark job output:\n{stdout}")
        if stderr:
            print(f"Spark job errors:\n{stderr}")

        if process.returncode == 0:
            # Extract result from output
            result = None
            for line in stdout.split('\n'):
                if line.startswith("RESULT:"):
                    result = line.replace("RESULT:", "").strip()
                    break

            if not result:
                result = "Job completed successfully"

            # Update status to COMPLETED
            update_job_status(db, job_id, JobStatus.COMPLETED, result=result)

            # Trigger post-processing
            trigger_post_processing(job_id, result)
        else:
            # Job failed
            error_msg = f"Spark job failed with return code {process.returncode}\n{stderr}"
            update_job_status(db, job_id, JobStatus.FAILED, error_message=error_msg)

    except Exception as e:
        print(f"Error processing job {job_id}: {str(e)}")
        update_job_status(db, job_id, JobStatus.FAILED, error_message=str(e))
    finally:
        db.close()


def trigger_post_processing(job_id: str, result: str):
    """
    Trigger post-processing after Spark job completes
    This is the additional Python application that runs after Spark job
    """
    print(f"Starting post-processing for job {job_id}")
    print(f"Job result: {result}")

    try:
        # Here you can add your post-processing logic
        # For example:
        # - Send notifications
        # - Update additional databases
        # - Trigger other workflows
        # - Generate reports

        # Example: Log the completion
        print(f"Post-processing completed for job {job_id}")
        print(f"Final status: SUCCESS")

        # You could also update a separate status table or send webhooks here

    except Exception as e:
        print(f"Error in post-processing for job {job_id}: {str(e)}")


def main():
    """
    Main worker loop that listens for jobs from Redis queue
    """
    print("Worker started, waiting for jobs...")
    print(f"Database URL: {DATABASE_URL}")
    print(f"Redis URL: {REDIS_URL}")
    print(f"Spark Master URL: {SPARK_MASTER_URL}")

    while True:
        try:
            # Block and wait for job from queue (timeout 1 second)
            job_data_str = redis_client.blpop("spark_job_queue", timeout=1)

            if job_data_str:
                # Parse job data
                _, job_data_json = job_data_str
                job_data = json.loads(job_data_json)

                print(f"Received job: {job_data}")

                # Process the job
                run_spark_job(job_data)

        except KeyboardInterrupt:
            print("Worker shutting down...")
            break
        except Exception as e:
            print(f"Error in worker loop: {str(e)}")
            time.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    main()
