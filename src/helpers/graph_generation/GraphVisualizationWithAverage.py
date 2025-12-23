import matplotlib.pyplot as plt

"""
Plots values from 'Values.txt' along with their running average.
Each value is read from the file (one per line), plotted as a line graph,
and annotated with its percentage change from the previous value.
"""

values = []
with open("Values.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line:
            values.append(float(line))

# Compute running average
running_avg = []
total = 0
for i, v in enumerate(values, start=1):
    total += v
    running_avg.append(total / i)

plt.figure(figsize=(12, 5))

# Plot actual values
plt.plot(values, marker='o', label='Actual Values')

# Plot running average
plt.plot(running_avg, marker='x', linestyle='--', label='Running Average')

# Add labels with percentage change
for i, v in enumerate(values):
    if i == 0:
        pct = "0%"  # No previous value
    else:
        pct_change = ((v - values[i-1]) / values[i-1]) * 100
        pct = f"{pct_change:+.2f}%"

    plt.text(i, v, f"{v:.2f} ({pct})", fontsize=8, ha='left', va='bottom')

plt.title("Values Visualization with Running Average + % Change")
plt.xlabel("Index")
plt.ylabel("Value")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
