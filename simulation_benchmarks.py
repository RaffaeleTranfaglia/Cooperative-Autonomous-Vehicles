import bisect
import math
import sys
import xml.etree.ElementTree as ET

def get_metrics(benchmark):
    trips = len(benchmark)
    total_waiting_time = 0
    min_time = sys.float_info.max
    max_time = sys.float_info.min
    sorted_waiting_times = []
    for info in benchmark:
        waiting_time = float(info.get("waitingTime"))/60
        total_waiting_time += waiting_time
        max_time = max(max_time, waiting_time)
        min_time = min(min_time, waiting_time)
        bisect.insort(sorted_waiting_times, waiting_time)
    
    # Given that trips is the throughput per hour, compute the throughput per minute
    throughput = trips / 60
    
    # Average waiting time per vehicle
    avg_waiting_time = total_waiting_time/trips
    
    p50 = sorted_waiting_times[math.ceil(len(sorted_waiting_times)*50/100)]
    p90 = sorted_waiting_times[math.ceil(len(sorted_waiting_times)*90/100)]
    
    # Get the percentage of vehicles that are waiting less or equal than a neighbourhood of average 
    # -> average +- epsilon
    epsilon = avg_waiting_time * 30 / 100
    index = bisect.bisect_right(sorted_waiting_times, avg_waiting_time + epsilon)
    percentage = index * 100 / len(sorted_waiting_times)
    
    # Throughput to waiting time ratio, combines the two metrics to give a single measure of system efficency
    # Higher values indicate a better-performing system where throughput is maximized while waiting time is minimized.
    tw_ratio = throughput / avg_waiting_time
    
    # Traffic Efficiency Index, the overall efficiency of traffic flow, 
    # taking into account how smoothly vehicles move through the system.
    # Since the throughput unity of time is 1 hour, total waiting time is transformed in hours.
    tei = throughput / total_waiting_time
    
    return {
        "throughput_per_hour": trips,
        "throughput_per_min": round(throughput, 2),
        "total_waiting_time": round(total_waiting_time, 2),
        "avg_waiting_time": round(avg_waiting_time, 2),
        "min_time": round(min_time, 2),
        "max_time": round(max_time, 2),
        "percentage_below_avg": round(percentage, 2),
        "p50": round(p50, 2),
        "p90": round(p90, 2),
        "tw_ratio": round(tw_ratio, 2),
        "tei": round(tei, 5)
    }

if __name__ == "__main__":
    feed1 = "sim_cfg_3_lanes/tripinfo.xml"
    feed2 = "sim_cfg_3_lanes/tripinfo2.xml"
    
    try:
        tree1 = ET.parse(feed1)
        tree2 = ET.parse(feed2)
        root1 = tree1.getroot()
        root2 = tree2.getroot()
        tripinfos1 = root1.findall("tripinfo")
        tripinfos2 = root2.findall("tripinfo")     
    except Exception as e:
        print(f"Error: {e}")
        
    platooning_metrics = get_metrics(tripinfos1)
    normal_metrics = get_metrics(tripinfos2)
        
    print(f"Total trips ended using platooning strategy: {platooning_metrics['throughput_per_hour']}")
    print(f"Total trips ended: {normal_metrics['throughput_per_hour']}")
        
    trips_increment = platooning_metrics["throughput_per_hour"] - normal_metrics["throughput_per_hour"]
    percent_trips_increment = trips_increment * 100 / normal_metrics["throughput_per_hour"]
    print(f"Trips increment by using platooning strategy: {round(percent_trips_increment, 2)}%\n")
    
    print(f"Throughput per minute using platooning strategy: {platooning_metrics['throughput_per_min']}")
    print(f"Throughput per minute: {normal_metrics['throughput_per_min']}\n")
    
    print(f"Total waiting time using platooning strategy: {platooning_metrics['total_waiting_time']} min")
    print(f"Total waiting time: {normal_metrics['total_waiting_time']} min")
    
    waiting_time_reduction = normal_metrics['total_waiting_time'] - platooning_metrics['total_waiting_time']
    percent_waiting_time_reduction = waiting_time_reduction * 100 / normal_metrics["total_waiting_time"]
    print(f"Reduction of total waiting time by using platooning strategy: {round(percent_waiting_time_reduction, 2)}%\n")
    
    print(f"Average waiting time per vehicle using platooning strategy: {platooning_metrics['avg_waiting_time']} min")
    print(f"Average waiting time per vehicle: {normal_metrics['avg_waiting_time']} min\n")
    
    print(f"Min and Max waiting time using platooning strategy: ({platooning_metrics['min_time']},{platooning_metrics['max_time']}) min")
    print(f"Min and Max waiting time: ({normal_metrics['min_time']},{normal_metrics['max_time']}) min\n")
    
    print(f"Percentage of vehicle whose waiting time meets the average using platooning strategy: {platooning_metrics['percentage_below_avg']}%")
    print(f"Percentage of vehicle whose waiting time meets the average: {normal_metrics['percentage_below_avg']}%\n")
    
    print(f"P50 (median) using platooning strategy: {platooning_metrics['p50']} min")
    print(f"P50 (median): {normal_metrics['p50']} min\n")
    
    print(f"P90 using platooning strategy: {platooning_metrics['p90']} min")
    print(f"P90: {normal_metrics['p90']} min\n")
    
    print(f"Throughput to waiting time ratio using platooning strategy: {platooning_metrics['tw_ratio']}")
    print(f"Throughput to waiting time ratio: {normal_metrics['tw_ratio']}\n")
    
    print(f"Traffic efficiency index using platooning strategy: {platooning_metrics['tei']}")
    print(f"Traffic efficiency index: {normal_metrics['tei']}")