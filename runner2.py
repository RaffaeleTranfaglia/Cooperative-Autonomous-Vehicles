import argparse
import math
import os
import sumolib
import sys
import traci
import xml.etree.ElementTree as ET
from utils import Utils

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 3600

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normal traffic simulation")
    parser.add_argument("--cfg", type=str, help="Configuration file path")
    args = parser.parse_args()
    
    cfg_tree = ET.parse(args.cfg)
    root = cfg_tree.getroot()
    route_file = root.find('./input/route-files').get('value')
    net_file = root.find('./input/net-file').get('value')
    
    route_tree = ET.parse(os.path.join(os.path.dirname(args.cfg), route_file))
    root = route_tree.getroot()
    flows = root.findall('./flow')
    flow_count = len(flows)
    flow_period = float(flows[0].get('period')) if flows else 0
    
    # Parse the net
    net = sumolib.net.readNet(os.path.join(os.path.dirname(args.cfg), net_file))
    traffic_density = flow_count * (1/flow_period) / math.log(1+Utils.getTotalEdgesLength(net))
    
    sumoCmd = ["sumo-gui", "--step-length", "0.1", 
           "--tripinfo-output", os.path.join(os.path.dirname(args.cfg), f"tripinfo_{round(traffic_density, 3)}.xml"),
           "-c", args.cfg]
    traci.start(sumoCmd)
    
    step = 0
    while step < STEPS:
        traci.simulationStep()
        step += 0.1
    traci.close()