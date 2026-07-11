import boto3
import json
import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

kinesis = boto3.client('kinesis', region_name='eu-west-1')
STREAM_NAME = 'wiki-edits-stream'

HEADERS = {
    'User-Agent': 'wiki-lambda-analytics/1.0 (NCI MSc Cloud Computing CA; contact@student.ncirl.ie)'
}

def run():
    url = "https://stream.wikimedia.org/v2/stream/recentchange"
    logger.info("Starting Wikimedia producer...")
    count = 0

    while True:
        try:
            with requests.get(url, stream=True, timeout=60, headers=HEADERS) as r:
                logger.info(f"Connected, status: {r.status_code}")
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith('data:'):
                        continue
                    try:
                        raw = json.loads(line[5:].strip())
                        record = {
                            'title':       raw.get('title', ''),
                            'wiki':        raw.get('wiki', ''),
                            'user':        raw.get('user', ''),
                            'bot':         raw.get('bot', False),
                            'type':        raw.get('type', ''),
                            'namespace':   raw.get('namespace', -1),
                            'timestamp':   raw.get('timestamp', 0),
                            'server_name': raw.get('server_name', '')
                        }
                        kinesis.put_record(
                            StreamName=STREAM_NAME,
                            Data=json.dumps(record),
                            PartitionKey=record['wiki'] or 'unknown'
                        )
                        count += 1
                        if count % 50 == 0:
                            logger.info(f"Published {count} records")
                    except Exception as e:
                        logger.warning(f"Error: {e}")
        except Exception as e:
            logger.error(f"Stream error: {e}, reconnecting in 5s...")
            time.sleep(5)

if __name__ == '__main__':
    run()
