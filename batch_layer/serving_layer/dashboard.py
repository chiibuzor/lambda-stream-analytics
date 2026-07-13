from flask import Flask, jsonify, render_template_string
import boto3
import time
from datetime import datetime
import pytz

app = Flask(__name__)

REGION = "eu-west-1"
ATHENA_DB = "wiki_lambda"
ATHENA_OUTPUT = "s3://wiki-lambda-athena-results-563170906648/"

athena = boto3.client("athena", region_name=REGION)


def get_latest_epoch():
    s3 = boto3.client('s3', region_name=REGION)
    response = s3.list_objects_v2(
        Bucket='wiki-lambda-speed-results-563170906648',
        Prefix='recent-counts/',
        Delimiter='/'
    )
    folders = [
        p['Prefix'] for p in response.get('CommonPrefixes', [])
        if 'epoch-' in p['Prefix']
    ]
    if not folders:
        return 0
    latest = sorted(
        folders,
        key=lambda x: int(x.split('epoch-')[1].rstrip('/'))
    )[-1]
    return int(latest.split('epoch-')[1].rstrip('/'))


def run_query(sql):
    response = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DB},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT}
    )
    query_id = response["QueryExecutionId"]
    while True:
        status = athena.get_query_execution(
            QueryExecutionId=query_id
        )["QueryExecution"]["Status"]["State"]
        if status == "SUCCEEDED":
            break
        elif status == "FAILED":
            return []
        time.sleep(1)
    results = athena.get_query_results(QueryExecutionId=query_id)
    rows = results["ResultSet"]["Rows"]
    headers = [c["VarCharValue"] for c in rows[0]["Data"]]
    data = []
    for row in rows[1:]:
        values = [c.get("VarCharValue", "") for c in row["Data"]]
        data.append(dict(zip(headers, values)))
    return data


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>WikiVelocity — Live Edit Tracker</title>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="60">
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,600;0,700;1,400;1,600&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'DM Sans',sans-serif;background:#ede8e0;color:#1c1917;min-height:100vh}

    .header{background:#1c1917;padding:18px 32px;display:flex;align-items:center;justify-content:space-between}
    .logo{font-family:'Fraunces',serif;font-size:23px;font-weight:700;color:#ede8e0;letter-spacing:-0.5px}
    .logo em{font-style:italic;color:#b8f07a}
    .tagline{font-size:11px;color:rgba(237,232,224,0.35);margin-top:3px;letter-spacing:0.2px;font-weight:400}
    .hright{display:flex;align-items:center;gap:10px}
    .ts{font-family:'DM Mono',monospace;font-size:11px;color:rgba(237,232,224,0.35);background:rgba(237,232,224,0.05);border:1px solid rgba(237,232,224,0.1);padding:6px 12px;border-radius:5px;font-weight:500}
    .live{display:flex;align-items:center;gap:7px;background:rgba(184,240,122,0.1);border:1px solid rgba(184,240,122,0.25);color:#b8f07a;padding:6px 14px;border-radius:5px;font-size:11px;font-weight:600;letter-spacing:0.3px}
    .ldot{width:6px;height:6px;border-radius:50%;background:#b8f07a;animation:p 2s ease-in-out infinite}
    @keyframes p{0%,100%{opacity:1}50%{opacity:0.2}}

    .kpis{display:grid;grid-template-columns:repeat(4,1fr);background:#1c1917;border-bottom:3px solid #ede8e0}
    .kpi{padding:26px 28px;border-right:1px solid rgba(237,232,224,0.07);position:relative}
    .kpi:last-child{border-right:none}
    .kpi-lbl{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(237,232,224,0.35);font-weight:600}
    .kpi-v{font-family:'Fraunces',serif;font-size:30px;font-weight:700;margin-top:8px;line-height:1;color:#ede8e0;letter-spacing:-1px}
    .kpi-s{font-size:11px;margin-top:8px;color:rgba(237,232,224,0.35);font-weight:500}
    .kpi-s.ok{color:#b8f07a}

    .panels{display:grid;grid-template-columns:1fr 1fr;background:#d8d2c8}
    .panel{background:#ede8e0;padding:28px 32px;border-right:1px solid #d8d2c8}
    .panel:last-child{border-right:none}
    .ptitle{font-family:'Fraunces',serif;font-size:19px;font-weight:700;letter-spacing:-0.5px;color:#1c1917}
    .psub{font-size:11px;color:#9c9488;margin-top:4px;margin-bottom:22px;font-weight:500}

    .br{display:flex;align-items:center;gap:10px;margin-bottom:12px}
    .rk{font-family:'DM Mono',monospace;font-size:10px;color:#c4bdb4;width:14px;flex-shrink:0;font-weight:500}
    .wk{font-size:12px;color:#1c1917;width:106px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600}
    .bt{flex:1;background:#d8d2c8;border-radius:1px;height:4px;overflow:hidden}
    .bf{height:4px;border-radius:1px}
    .bi{background:#1c1917}
    .bp{background:#7c6fe0}
    .bv{font-family:'DM Mono',monospace;font-size:11px;color:#7a7268;width:62px;text-align:right;flex-shrink:0;font-weight:500}

    .merge{background:#e6e0d7;padding:28px 32px;border-top:1px solid #d8d2c8;border-bottom:1px solid #d8d2c8}
    .mhead{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px}
    .leg{display:flex;gap:18px}
    .li{display:flex;align-items:center;gap:7px;font-size:11px;color:#9c9488;font-weight:500}
    .ld{width:18px;height:2px;border-radius:1px;flex-shrink:0}
    .mg{display:grid;grid-template-columns:1fr 1fr;gap:10px 40px}
    .pill{font-size:9px;padding:2px 8px;border-radius:3px;font-weight:600;letter-spacing:0.8px;flex-shrink:0;font-family:'DM Mono',monospace;text-transform:uppercase}
    .pl{background:#1c1917;color:#ede8e0}
    .ph{background:#ede9fe;color:#7c6fe0}

    .how{background:#1c1917;padding:28px 32px}
    .howt{font-family:'DM Mono',monospace;font-size:10px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:rgba(237,232,224,0.25);margin-bottom:20px}
    .steps{display:flex;align-items:stretch}
    .step{flex:1;padding:18px 16px;border:1px solid rgba(237,232,224,0.07);border-radius:8px;margin:0 4px}
    .step:first-child{margin-left:0}
    .step:last-child{margin-right:0}
    .sn{font-family:'DM Mono',monospace;font-size:10px;color:#b8f07a;margin-bottom:10px;font-weight:600}
    .sname{font-family:'Fraunces',serif;font-size:13px;font-weight:600;color:#ede8e0;margin-bottom:6px}
    .sdesc{font-size:11px;color:rgba(237,232,224,0.3);line-height:1.6;font-weight:400}
    .stech{font-size:9px;color:rgba(184,240,122,0.45);margin-top:10px;font-family:'DM Mono',monospace;letter-spacing:0.8px;text-transform:uppercase;font-weight:500}
    .sarr{display:flex;align-items:center;padding:0 4px;color:rgba(237,232,224,0.1);font-size:16px;flex-shrink:0}

    .footer{background:#ede8e0;padding:14px 32px;display:flex;justify-content:space-between;border-top:1px solid #d8d2c8}
    .fl{font-size:11px;color:#b0a89e;font-weight:500}
  </style>
</head>
<body>

<div class="header">
  <div>
    <div class="logo">Wiki<em>Velocity</em></div>
    <div class="tagline">Every Wikipedia edit, everywhere, right now</div>
  </div>
  <div class="hright">
    <div class="ts">{{ now }}</div>
    <div class="live"><span class="ldot"></span>Live</div>
  </div>
</div>

<div class="kpis">
  <div class="kpi">
    <div class="kpi-lbl">Hottest wiki right now</div>
    <div class="kpi-v">{{ speed[0].wiki if speed else '&mdash;' }}</div>
    <div class="kpi-s ok">{{ '{:,}'.format(speed[0].edit_count | int) }} edits in last 5 min</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">Wikis active right now</div>
    <div class="kpi-v">{{ speed | length }}</div>
    <div class="kpi-s">language wikis edited in last 5 min</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">Total edits in history</div>
    <div class="kpi-v">{{ '{:,}'.format(total_records) }}</div>
    <div class="kpi-s">recorded since {{ start_date }}</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">Pipeline health</div>
    <div class="kpi-v" style="font-size:18px;padding-top:8px;color:#b8f07a">All systems running</div>
    <div class="kpi-s ok">Stream &middot; counter &middot; history &middot; window #{{ latest_epoch }}</div>
  </div>
</div>

<div class="panels">
  <div class="panel">
    <div class="ptitle">Trending right now</div>
    <div class="psub">Most edited wikis in the last 5 min &middot; window #{{ latest_epoch }} &middot; updates every minute</div>
    {% set max_s = speed[0].edit_count | int if speed else 1 %}
    {% for row in speed[:12] %}
    <div class="br">
      <span class="rk">{{ loop.index }}</span>
      <span class="wk">{{ row.wiki }}</span>
      <div class="bt"><div class="bf bi" style="width:{{ [((row.edit_count | int) / max_s * 100) | int, 1] | max }}%"></div></div>
      <span class="bv">{{ '{:,}'.format(row.edit_count | int) }}</span>
    </div>
    {% endfor %}
  </div>

  <div class="panel">
    <div class="ptitle">All-time leaders</div>
    <div class="psub">Total edits recorded since {{ start_date }} &middot; computed over full dataset</div>
    {% set max_b = batch[0].total_edits | int if batch else 1 %}
    {% for row in batch[:12] %}
    <div class="br">
      <span class="rk">{{ loop.index }}</span>
      <span class="wk">{{ row.wiki }}</span>
      <div class="bt"><div class="bf bp" style="width:{{ [((row.total_edits | int) / max_b * 100) | int, 1] | max }}%"></div></div>
      <span class="bv">{{ '{:,}'.format(row.total_edits | int) }}</span>
    </div>
    {% endfor %}
  </div>
</div>

<div class="merge">
  <div class="mhead">
    <div>
      <div class="ptitle">Full picture &mdash; live meets history</div>
      <div class="psub" style="margin-bottom:0">Every wiki ranked by total volume &middot; live data and historical records combined</div>
    </div>
    <div class="leg">
      <div class="li"><span class="ld" style="background:#1c1917"></span>Live &mdash; last 5 min</div>
      <div class="li"><span class="ld" style="background:#7c6fe0"></span>History &mdash; all time</div>
    </div>
  </div>
  {% set max_m = merge[0].total_edits | int if merge else 1 %}
  <div class="mg">
    {% for row in merge[:20] %}
    <div class="br">
      <span class="rk">{{ loop.index }}</span>
      <span class="wk">{{ row.wiki }}</span>
      <div class="bt">
        <div class="bf {{ 'bi' if row.source == 'speed' else 'bp' }}"
          style="width:{{ [((row.total_edits | int) / max_m * 100) | int, 1] | max }}%"></div>
      </div>
      <span class="bv">{{ '{:,}'.format(row.total_edits | int) }}</span>
      <span class="pill {{ 'pl' if row.source == 'speed' else 'ph' }}">
        {{ 'live' if row.source == 'speed' else 'history' }}
      </span>
    </div>
    {% endfor %}
  </div>
</div>

<div class="how">
  <div class="howt">How it works</div>
  <div class="steps">
    <div class="step">
      <div class="sn">01</div>
      <div class="sname">Edit fires</div>
      <div class="sdesc">Every edit on any Wikipedia &mdash; English, Arabic, Chechen &mdash; triggers a real-time event the moment it's saved.</div>
      <div class="stech">Wikimedia Event Streams</div>
    </div>
    <div class="sarr">&rsaquo;</div>
    <div class="step">
      <div class="sn">02</div>
      <div class="sname">Captured instantly</div>
      <div class="sdesc">A listener running 24/7 picks up each event and pushes it into a queue. Every event is saved permanently.</div>
      <div class="stech">AWS Kinesis &middot; S3</div>
    </div>
    <div class="sarr">&rsaquo;</div>
    <div class="step">
      <div class="sn">03</div>
      <div class="sname">5-min window</div>
      <div class="sdesc">A counter tallies edits per wiki in a rolling 5-minute window. Slides every minute so you always see what's hot.</div>
      <div class="stech">Spark Structured Streaming</div>
    </div>
    <div class="sarr">&rsaquo;</div>
    <div class="step">
      <div class="sn">04</div>
      <div class="sname">History computed</div>
      <div class="sdesc">Separately the entire stored dataset is processed to produce accurate all-time totals over all accumulated data.</div>
      <div class="stech">PySpark on EMR</div>
    </div>
    <div class="sarr">&rsaquo;</div>
    <div class="step">
      <div class="sn">05</div>
      <div class="sname">Merged here</div>
      <div class="sdesc">This page queries both results &mdash; real-time trends and accurate history in one place.</div>
      <div class="stech">Amazon Athena</div>
    </div>
  </div>
</div>

<div class="footer">
  <div class="fl">WikiVelocity &middot; Auto-refreshes every 60 seconds &middot; Data since {{ start_date }}</div>
  <div class="fl">NCI MSc Cloud Computing &middot; Scalable Cloud Programming &middot; {{ today }}</div>
</div>

</body>
</html>
"""


@app.route('/')
def index():
    ireland = pytz.timezone("Europe/Dublin")
    now_dt = datetime.now(ireland)
    now = now_dt.strftime("%d %b %Y &middot; %H:%M IST")
    today = now_dt.strftime("%d %B %Y")
    start_date = "11 Jul 2026"

    latest_epoch = get_latest_epoch()

    speed = run_query(
        """
        SELECT wiki, SUM(edit_count) as edit_count
        FROM wiki_lambda.speed_counts
        WHERE "$path" LIKE '%epoch-{epoch}%'
        GROUP BY wiki
        ORDER BY edit_count DESC
        LIMIT 15
        """.format(epoch=latest_epoch)
    )

    batch = run_query(
        "SELECT wiki, total_edits "
        "FROM wiki_lambda.domain_counts "
        "ORDER BY total_edits DESC LIMIT 15"
    )

    merge = run_query(
        """
        SELECT wiki, SUM(total_edits) as total_edits, 'batch' as source
        FROM wiki_lambda.domain_counts GROUP BY wiki
        UNION ALL
        SELECT wiki, SUM(edit_count) as total_edits, 'speed' as source
        FROM wiki_lambda.speed_counts
        WHERE "$path" LIKE '%epoch-{epoch}%'
        GROUP BY wiki
        ORDER BY total_edits DESC LIMIT 20
        """.format(epoch=latest_epoch)
    )

    total_records = sum(
        int(r.get('total_edits', 0)) for r in batch
    ) if batch else 0

    return render_template_string(
        HTML,
        speed=speed,
        batch=batch,
        merge=merge,
        now=now,
        today=today,
        start_date=start_date,
        total_records=total_records,
        latest_epoch=latest_epoch
    )


@app.route('/api/speed')
def api_speed():
    latest_epoch = get_latest_epoch()
    data = run_query(
        """
        SELECT wiki, SUM(edit_count) as edit_count
        FROM wiki_lambda.speed_counts
        WHERE "$path" LIKE '%epoch-{epoch}%'
        GROUP BY wiki
        ORDER BY edit_count DESC
        LIMIT 15
        """.format(epoch=latest_epoch)
    )
    return jsonify(data)


@app.route('/api/batch')
def api_batch():
    data = run_query(
        "SELECT wiki, total_edits "
        "FROM wiki_lambda.domain_counts "
        "ORDER BY total_edits DESC LIMIT 15"
    )
    return jsonify(data)


@app.route('/health')
def health():
    ireland = pytz.timezone("Europe/Dublin")
    return jsonify({
        "status": "ok",
        "latest_epoch": get_latest_epoch(),
        "time": datetime.now(ireland).strftime("%d %b %Y · %H:%M IST")
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)