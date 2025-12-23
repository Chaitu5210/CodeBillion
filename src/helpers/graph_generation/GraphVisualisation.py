import matplotlib.pyplot as plt

"""
Reads numeric values from a Values.txt text file and plots them using Matplotlib.
The file 'Values.txt' should contain one number per line.
Each value is plotted in order as a line graph.
"""

values = []
with open("Values.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line:
            values.append(float(line))

# Plot the data
plt.figure(figsize=(10,4))
plt.plot(values, marker='o')
plt.title("Values Visualization")
plt.xlabel("Index")
plt.ylabel("Value")
plt.grid(True)
plt.tight_layout()
plt.show()
