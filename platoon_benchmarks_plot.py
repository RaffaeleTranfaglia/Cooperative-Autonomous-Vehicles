import pandas as pd
import matplotlib.pyplot as plt
import os

class PlatoonBenchmarksPlotter:
    def __init__(self, grouped_df, x_variable, y_variable, x_label, y_label, title):
        self.grouped_df = grouped_df
        self.x_variable = x_variable
        self.y_variable = y_variable
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        
    def plot(self):
        #Plot the speed data
        plt.figure()

        for key, data in self.grouped_df:
            plt.plot(data[self.x_variable], data[self.y_variable], linestyle='-', label=f'ID {key}')

        # Customize the plot
        plt.title(self.title)
        plt.xlabel(self.x_label)
        plt.ylabel(self.y_label)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend()

        # Show the plot
        plt.show()

        
# Read the CSV file into a DataFrame
df = pd.read_csv(os.path.join("sim_benchmarks", "log_platoon_2.csv"))

# Group the data by 'ID'
grouped_df = df.groupby('nodeId')
map(lambda x: x*3.6, grouped_df['speed'])

for vid, group in grouped_df:
    print(vid)
    print(group)

# Plot speed graph
speed_plotter = PlatoonBenchmarksPlotter(grouped_df, 'time', 'speed', 'Time [s]', 'Speed [Km/h]', 
                                         'Speed over time of platoon members')
speed_plotter.plot()


# Plot distance graph
filtered_df= grouped_df.filter(lambda x: (x['distance'] != -1).all())
grouped_filtered_df = filtered_df.groupby('nodeId')

distance_plotter = PlatoonBenchmarksPlotter(grouped_filtered_df, 'time', 'distance', 'Time [s]', 'Distance [m]', 
                                            'Platoon Inter-vehicle distance')
distance_plotter.plot()

# Plot acceleration graph
acceleration_plotter = PlatoonBenchmarksPlotter(grouped_df, 'time', 'acceleration', 'Time [s]', 
                                                'Acceleration [m/(s**2)]', 
                                                "Acceleration over time of platoon members")
acceleration_plotter.plot()