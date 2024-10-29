import os
import re
import xml.etree.ElementTree as ET
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

def parse_tripinfo_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        tripinfos = root.findall("tripinfo")
        return tripinfos
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None
    
def get_waiting_times(tripinfos):
    waiting_times = []
    for info in tripinfos:
        waiting_times.append(float(info.get("waitingTime"))/60)
    return waiting_times

def process_folder(folder_path):
    data_throughput = []
    data_waiting_time = []

    for filename in os.listdir(folder_path):
        if match := re.match(r"(tripinfo|tripinfo-platooning)_(\d+\.\d+|\d+)\.xml", filename):
            category = match.group(1)
            traffic_density = float(match.group(2)) 
            file_path = os.path.join(folder_path, filename)
            
            # Parse the XML and get the tripinfo count
            tripinfos = parse_tripinfo_file(file_path)
            throughput = len(tripinfos) if tripinfos else 0
            data_throughput.append({"category": category, "traffic_density": traffic_density, "throughput": throughput})
            waiting_times = get_waiting_times(tripinfos)
            for waiting_time in waiting_times:
                data_waiting_time.append({"category": category, "traffic_density": traffic_density, "waiting_time": waiting_time})

    return {"throughput": pd.DataFrame(data_throughput), "waiting_time": pd.DataFrame(data_waiting_time)}

def plot_throughput_data(df):
    plt.figure(figsize=(12, 6))
    sns.barplot(x="traffic_density", y="throughput", hue="category", data=df)
    plt.title("Throughput (considered unit time = 1 hour) by the traffic intensity")
    plt.xlabel("Traffic density")
    plt.ylabel("Throughput")
    plt.legend(title="Category")
    plt.show()
    
def plot_waiting_time_data(df):
    plt.figure(figsize=(12, 6))
    sns.boxplot(x="traffic_density", y="waiting_time", hue="category", data=df)
    plt.title("Waiting time by the traffic intensity")
    plt.xlabel("Traffic density")
    plt.ylabel("Waiting time [min]")
    plt.legend(title="Category")
    plt.show()

if __name__ == "__main__":
    folder_path = "sim_cfg_2_lanes"
    metrics = process_folder(folder_path)
    
    if not metrics["throughput"].empty and not metrics["waiting_time"].empty:
        plot_throughput_data(metrics["throughput"])
        plot_waiting_time_data(metrics["waiting_time"])
    else:
        print("No matching files found or no valid data to plot.")
    
