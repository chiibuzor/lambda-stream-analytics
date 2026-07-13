import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'figure.facecolor': 'white',
    'axes.facecolor': '#fafafa',
})

# ── Benchmark data ────────────────────────────────────────────────
nodes      = [1, 2, 4]
times      = [124, 117, 128]
speedups   = [1.0, 124/117, 124/128]
ideal      = [1.0, 2.0, 4.0]
records    = 500000
throughput = [records/t for t in times]

# ── Graph 1: Execution time vs worker nodes ───────────────────────
fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(nodes, times,
              color=['#4f8fff', '#7c6fe0', '#f59e0b'],
              width=0.5, zorder=3,
              edgecolor='white', linewidth=1.5)
for bar, t in zip(bars, times):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 1.5,
            f'{t}s', ha='center', va='bottom',
            fontweight='bold', fontsize=12)
ax.set_xlabel('Number of worker nodes', fontweight='bold')
ax.set_ylabel('Execution time (seconds)', fontweight='bold')
ax.set_title('Batch job execution time vs worker count',
             fontweight='bold', pad=12)
ax.set_xticks(nodes)
ax.set_xticklabels(['1 node\n(baseline)', '2 nodes', '4 nodes'])
ax.set_ylim(0, 155)
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%ds'))
plt.tight_layout()
plt.savefig('benchmarks/graph_execution_time.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("Graph 1 saved: graph_execution_time.png")

# ── Graph 2: Speedup vs worker nodes ─────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(nodes, ideal, '--', color='#ccc', linewidth=1.5,
        label='Ideal linear speedup', zorder=2)
ax.plot(nodes, speedups, 'o-', color='#4f8fff', linewidth=2.5,
        markersize=9, markerfacecolor='white',
        markeredgewidth=2.5, label='Actual speedup', zorder=3)
for x, y in zip(nodes, speedups):
    ax.annotate(f'{y:.2f}x', (x, y),
                textcoords="offset points", xytext=(10, 5),
                fontweight='bold', fontsize=11, color='#4f8fff')
ax.fill_between(nodes, speedups, ideal,
                alpha=0.08, color='#4f8fff')
ax.set_xlabel('Number of worker nodes', fontweight='bold')
ax.set_ylabel('Speedup (T\u2081 / T\u2099)', fontweight='bold')
ax.set_title('Speedup vs worker count \u2014 actual vs ideal',
             fontweight='bold', pad=12)
ax.set_xticks(nodes)
ax.set_xticklabels(['1 node', '2 nodes', '4 nodes'])
ax.set_ylim(0, 4.5)
ax.legend(framealpha=0.8)
plt.tight_layout()
plt.savefig('benchmarks/graph_speedup.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("Graph 2 saved: graph_speedup.png")

# ── Graph 3: Throughput vs worker nodes ──────────────────────────
fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(nodes, throughput,
              color=['#4f8fff', '#7c6fe0', '#f59e0b'],
              width=0.5, zorder=3,
              edgecolor='white', linewidth=1.5)
for bar, tp in zip(bars, throughput):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 50,
            f'{tp:,.0f}\nrec/s', ha='center', va='bottom',
            fontweight='bold', fontsize=11)
ax.set_xlabel('Number of worker nodes', fontweight='bold')
ax.set_ylabel('Throughput (records / second)', fontweight='bold')
ax.set_title('Processing throughput vs worker count',
             fontweight='bold', pad=12)
ax.set_xticks(nodes)
ax.set_xticklabels(['1 node\n(baseline)', '2 nodes', '4 nodes'])
ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
plt.tight_layout()
plt.savefig('benchmarks/graph_throughput.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("Graph 3 saved: graph_throughput.png")

# ── Graph 4: Speed layer latency vs ingestion rate ───────────────
rates   = [5, 20, 50, 100, 200]
latency = [0.8, 1.1, 1.4, 2.1, 3.8]

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(rates, latency, 's-', color='#3dd68c', linewidth=2.5,
        markersize=9, markerfacecolor='white',
        markeredgewidth=2.5, zorder=3)
ax.fill_between(rates, latency, alpha=0.1, color='#3dd68c')
for x, y in zip(rates, latency):
    ax.annotate(f'{y}s', (x, y),
                textcoords="offset points", xytext=(5, 8),
                fontsize=10, color='#2a9e6a', fontweight='bold')
ax.axhline(y=60, color='#f59e0b', linestyle='--',
           linewidth=1.5, label='1-min window trigger',
           alpha=0.7)
ax.set_xlabel('Ingestion rate (records / second)',
              fontweight='bold')
ax.set_ylabel('Speed layer processing latency (seconds)',
              fontweight='bold')
ax.set_title('Speed layer latency vs ingestion rate',
             fontweight='bold', pad=12)
ax.legend(framealpha=0.8)
plt.tight_layout()
plt.savefig('benchmarks/graph_latency.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("Graph 4 saved: graph_latency.png")

# ── Graph 5: Benchmark summary table ─────────────────────────────
fig, ax = plt.subplots(figsize=(7, 2.5))
ax.axis('off')
table_data = [
    ['Worker nodes', 'Exec time (s)', 'Speedup', 'Throughput (rec/s)'],
    ['1 node (baseline)', '124', '1.00x', '4,032'],
    ['2 nodes',           '117', '1.06x', '4,274'],
    ['4 nodes',           '128', '0.97x', '3,906'],
]
table = ax.table(
    cellText=table_data[1:],
    colLabels=table_data[0],
    cellLoc='center',
    loc='center',
    bbox=[0, 0, 1, 1]
)
table.auto_set_font_size(False)
table.set_fontsize(10)
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_facecolor('#1c1917')
        cell.set_text_props(color='white', fontweight='bold')
    elif row % 2 == 0:
        cell.set_facecolor('#f5f3ee')
    cell.set_edgecolor('#d8d2c8')
plt.title('Benchmark results summary',
          fontweight='bold', pad=10, fontsize=12)
plt.tight_layout()
plt.savefig('benchmarks/graph_summary_table.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("Graph 5 saved: graph_summary_table.png")

print("\nAll 5 graphs generated successfully.")
print("Location: benchmarks/")