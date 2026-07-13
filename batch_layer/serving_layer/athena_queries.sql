-- Create database
CREATE DATABASE IF NOT EXISTS wiki_lambda;

-- Batch results table
CREATE EXTERNAL TABLE IF NOT EXISTS wiki_lambda.domain_counts (
  wiki string,
  total_edits bigint
)
STORED AS PARQUET
LOCATION 's3://wiki-lambda-batch-results-563170906648/domain-counts/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

-- Type counts table
CREATE EXTERNAL TABLE IF NOT EXISTS wiki_lambda.type_counts (
  type string,
  total_edits bigint
)
STORED AS PARQUET
LOCATION 's3://wiki-lambda-batch-results-563170906648/type-counts/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

-- Bot counts table
CREATE EXTERNAL TABLE IF NOT EXISTS wiki_lambda.bot_counts (
  bot boolean,
  total_edits bigint
)
STORED AS PARQUET
LOCATION 's3://wiki-lambda-batch-results-563170906648/bot-counts/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

-- Speed layer table
CREATE EXTERNAL TABLE IF NOT EXISTS wiki_lambda.speed_counts (
  wiki string,
  edit_count bigint
)
STORED AS PARQUET
LOCATION 's3://wiki-lambda-speed-results-563170906648/recent-counts/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

-- Lambda merge query (serving layer)
SELECT wiki, SUM(total_edits) as total_edits, 'batch' as source
FROM wiki_lambda.domain_counts
GROUP BY wiki
UNION ALL
SELECT wiki, SUM(edit_count) as total_edits, 'speed' as source
FROM wiki_lambda.speed_counts
WHERE "$path" LIKE '%epoch-71%'
GROUP BY wiki
ORDER BY total_edits DESC
LIMIT 20;