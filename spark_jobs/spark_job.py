from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg
import sys
import time


def run_spark_job(job_id: str):
    """
    Example Spark job that processes some data
    In a real scenario, this would process actual data from files or databases
    """
    print(f"Starting Spark job: {job_id}")

    # Initialize Spark session
    spark = SparkSession.builder \
        .appName(f"HuanJob-{job_id}") \
        .getOrCreate()

    try:
        # Example: Create sample data
        data = [
            ("user1", 25, "New York"),
            ("user2", 30, "London"),
            ("user3", 35, "Tokyo"),
            ("user4", 28, "New York"),
            ("user5", 32, "London"),
        ]

        columns = ["name", "age", "city"]
        df = spark.createDataFrame(data, columns)

        print("Sample data created:")
        df.show()

        # Perform some transformations
        result_df = df.groupBy("city") \
            .agg(
                count("name").alias("user_count"),
                avg("age").alias("avg_age")
            ) \
            .orderBy("city")

        print("Aggregation results:")
        result_df.show()

        # Simulate some processing time
        print("Processing data...")
        time.sleep(10)

        # Collect results
        results = result_df.collect()
        result_str = "\n".join([f"{row.city}: {row.user_count} users, avg age {row.avg_age:.1f}"
                                for row in results])

        print(f"Job {job_id} completed successfully")
        print(f"Results:\n{result_str}")

        return result_str

    except Exception as e:
        print(f"Error in Spark job {job_id}: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: spark_job.py <job_id>")
        sys.exit(1)

    job_id = sys.argv[1]
    result = run_spark_job(job_id)
    print(f"RESULT:{result}")
