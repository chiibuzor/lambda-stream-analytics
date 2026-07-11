from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

spark = SparkSession.builder \
    .appName("WikiBatchLayer") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

INPUT_PATH  = "s3://wiki-lambda-raw-563170906648/wiki-edits/"
OUTPUT_PATH = "s3://wiki-lambda-batch-results-563170906648/"

logger.info("Reading raw data from S3...")
df = spark.read.json(INPUT_PATH)

total = df.count()
logger.info(f"Total records: {total}")

domain_counts = df.groupBy("wiki") \
    .agg(count("*").alias("total_edits")) \
    .orderBy(desc("total_edits"))

domain_counts.show(10, truncate=False)

type_counts = df.groupBy("type") \
    .agg(count("*").alias("total_edits")) \
    .orderBy(desc("total_edits"))

type_counts.show(10, truncate=False)

bot_counts = df.groupBy("bot") \
    .agg(count("*").alias("total_edits"))

bot_counts.show()

wiki_type_counts = df.groupBy("wiki", "type") \
    .agg(count("*").alias("total_edits")) \
    .orderBy(desc("total_edits"))

domain_counts.write.mode("overwrite") \
    .parquet(OUTPUT_PATH + "domain-counts/")

type_counts.write.mode("overwrite") \
    .parquet(OUTPUT_PATH + "type-counts/")

bot_counts.write.mode("overwrite") \
    .parquet(OUTPUT_PATH + "bot-counts/")

wiki_type_counts.write.mode("overwrite") \
    .parquet(OUTPUT_PATH + "wiki-type-counts/")

logger.info(f"Batch job complete. Processed {total} records.")
spark.stop()
