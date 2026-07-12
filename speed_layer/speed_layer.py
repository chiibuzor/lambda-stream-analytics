from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, window,
    from_json, from_unixtime, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, BooleanType, LongType, IntegerType
)
import logging
import boto3
import os
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

STREAM_NAME = "wiki-edits-stream"
REGION      = "eu-west-1"
ENDPOINT    = "https://kinesis.eu-west-1.amazonaws.com"
CHECKPOINT  = "/tmp/wiki-speed-checkpoint2/"
LOCAL_OUT   = "/tmp/speed-results"
S3_BUCKET   = "wiki-lambda-speed-results-563170906648"

spark = SparkSession.builder \
    .appName("WikiSpeedLayer") \
    .config("spark.sql.shuffle.partitions", "2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("title",       StringType(),  True),
    StructField("wiki",        StringType(),  True),
    StructField("user",        StringType(),  True),
    StructField("bot",         BooleanType(), True),
    StructField("type",        StringType(),  True),
    StructField("namespace",   IntegerType(), True),
    StructField("timestamp",   LongType(),    True),
    StructField("server_name", StringType(),  True),
])

logger.info("Reading from Kinesis stream...")

raw_df = spark.readStream \
    .format("kinesis") \
    .option("streamName", STREAM_NAME) \
    .option("startingPosition", "LATEST") \
    .option("region", REGION) \
    .option("endpointUrl", ENDPOINT) \
    .load()

parsed_df = raw_df \
    .selectExpr("CAST(data AS STRING) as json_str") \
    .select(from_json(col("json_str"), schema).alias("d")) \
    .select("d.*") \
    .withColumn("event_time",
        to_timestamp(from_unixtime(col("timestamp"))))

# 5-minute sliding window, slides every 1 minute
# Distinction-level requirement per CA marking rubric
windowed_counts = parsed_df \
    .withWatermark("event_time", "30 seconds") \
    .groupBy(
        window(col("event_time"), "5 minutes", "1 minute"),
        col("wiki")
    ) \
    .agg(count("*").alias("edit_count"))

def write_batch(df, epoch_id):
    count_val = df.count()
    if count_val == 0:
        logger.info(f"Epoch {epoch_id}: no data yet")
        return

    logger.info(f"\n=== Epoch {epoch_id} — Top wikis in 5-min sliding window ===")
    df.orderBy(col("edit_count").desc()).show(15, truncate=False)

    # Write locally first
    local_path = f"{LOCAL_OUT}/epoch-{epoch_id}"
    os.makedirs(local_path, exist_ok=True)
    df.write.mode("overwrite").parquet(local_path)

    # Upload to S3
    s3 = boto3.client("s3", region_name=REGION)
    for root, dirs, files in os.walk(local_path):
        for file in files:
            if file.endswith(".parquet"):
                full_path = os.path.join(root, file)
                s3_key = f"recent-counts/epoch-{epoch_id}/{file}"
                s3.upload_file(full_path, S3_BUCKET, s3_key)
                logger.info(f"Uploaded {s3_key}")

logger.info("Starting 5-min sliding window, 1-min slide...")

query = windowed_counts.writeStream \
    .outputMode("update") \
    .foreachBatch(write_batch) \
    .option("checkpointLocation", CHECKPOINT) \
    .trigger(processingTime="1 minute") \
    .start()

logger.info("Speed layer running. Windows updating every 1 minute.")
query.awaitTermination()