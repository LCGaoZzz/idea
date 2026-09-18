#!/usr/bin/env python3
"""Optional deterministic teaching plot; not empirical PreGame data."""
from pathlib import Path
import matplotlib.pyplot as plt

output = Path(__file__).resolve().parents[1] / 'figures/max_aggregation_hypothetical.png'
counts = list(range(1, 101))
fig, ax = plt.subplots(figsize=(8.5, 5.2))
ax.plot(counts, [100*(1-.99**n) for n in counts])
for n in (1, 10, 30, 100):
    value = 100*(1-.99**n)
    ax.plot(n, value, 'o')
    ax.annotate(f'{n} cells: {value:.1f}%', (n, value),
                xytext=(7 if n<100 else -110, 8), textcoords='offset points')
ax.set(xlabel='Cells per clonotype',
       ylabel='Probability of at least one threshold exceedance (%)',
       title='Maximum-score aggregation and clone size\nHypothetical independent-cell example; NOT empirical PreGame performance',
       xlim=(0, 105), ylim=(0, 75))
fig.tight_layout()
output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output, dpi=180)
plt.close(fig)
