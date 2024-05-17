import pandas as pd
import matplotlib.pyplot as plt
import os

# Read the CSV file into a DataFrame
df = pd.read_csv(os.path.join("sim_benchmarks", "log_platoon_2.csv"))

# Extract the data from the DataFrame
vid = df['nodeId']
time = df['time']
distance = df['distance']
rel_speed = df['relativeSpeed']
speed = df['speed']

# Group the data by 'ID'
grouped = df.groupby('nodeId')

# Plot the data
plt.figure(figsize=(10, 5))

for i, (key, group) in enumerate(grouped):
    plt.plot(group['time'], group['speed']*3.6, marker='o', linestyle='-', label=f'ID {key}')

# Customize the plot
plt.title('Line Graph from CSV Data')
plt.xlabel('Time [s]')
plt.ylabel('Speed [Km/h]')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

# Show the plot
plt.show()
