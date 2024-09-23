import matplotlib.pyplot as plt
import pandas as pd

# Assuming you've already loaded the data into a DataFrame (e.g., from a CSV)
df = pd.read_csv("ndvi_0.csv")

# Convert the interval_from column to datetime
df["interval_from"] = pd.to_datetime(df["interval_from"])

# Plot the NDVI mean values over time
plt.figure(figsize=(10, 6))
plt.plot(
    df["interval_from"],
    df["data_daily_max_ndvi_mean"],
    marker="o",
    linestyle="-",
    color="green",
)

# Add labels and title
plt.title("NDVI Mean Values Over Time", fontsize=16)
plt.xlabel("Date", fontsize=12)
plt.ylabel("NDVI Mean", fontsize=12)
plt.grid(True)

# Show the plot
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.tight_layout()  # Adjust layout for a clean look
plt.savefig("ndvi_mean.png")
plt.show()
