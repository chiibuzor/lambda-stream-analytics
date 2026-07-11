# Wiki Lambda Analytics

NCI MSc Cloud Computing — Scalable Cloud Programming CA
Due: 4 August 2026

## Real-time question
Which Wikipedia article titles are trending in the last 5 minutes,
and how does their current edit velocity compare against their
long-term historical edit frequency?

## Architecture
Lambda architecture on AWS:
- Stream source: Wikimedia Event Streams (SSE)
- Ingestion: Kinesis Data Streams + Firehose
- Batch layer: PySpark on EMR
- Speed layer: Spark Structured Streaming (5-min sliding window)
- Serving layer: Athena over S3

## Repo structure
ingestion/       — Kinesis producer
batch_layer/     — PySpark batch job
speed_layer/     — Spark Structured Streaming
serving_layer/   — Athena SQL queries
infrastructure/  — AWS setup docs and service files
benchmarks/      — timing scripts and results
report/          — IEEE PDF

## Setup
See infrastructure/aws-setup.md for full AWS configuration.

## Dataset
Wikimedia Event Streams — https://stream.wikimedia.org/v2/stream/recentchange
No API key required.
