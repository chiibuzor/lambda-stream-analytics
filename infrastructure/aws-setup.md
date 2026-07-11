# AWS Infrastructure Setup

## Region: eu-west-1
## Account: 563170906648

## S3 Buckets
- wiki-lambda-raw-563170906648             — master dataset (Firehose writes here)
- wiki-lambda-batch-results-563170906648   — batch layer Parquet output
- wiki-lambda-speed-results-563170906648   — speed layer output
- wiki-lambda-athena-results-563170906648  — Athena query results

## Kinesis
- Stream name: wiki-edits-stream
- Shards: 2

## Firehose
- Name: wiki-edits-firehose
- Source: wiki-edits-stream
- Destination: wiki-lambda-raw-563170906648/wiki-edits/year=.../month=.../day=.../
- Buffer: 5MB or 60 seconds

## EMR Cluster
- Cluster ID: j-1CKML80RAYSTY
- Release: emr-7.1.0
- Apps: Spark, Hadoop
- Master: 1x m5.xlarge
- Core: 2x m5.xlarge
- Auto-scaling: min 2 / max 6 nodes

## EMR Auto-scaling Policy
- Scale out: YARNMemoryAvailablePercentage < 20% → +2 nodes, cooldown 300s
- Scale in:  YARNMemoryAvailablePercentage > 80% → -1 node,  cooldown 300s

## EC2 Producer
- Instance ID: i-061b670ef18c105b1
- Type: t3.micro
- IP: 52.215.205.57
- Runs: producer.py as systemd service wiki-producer
