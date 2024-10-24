import os
import sys
import traci

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 3600

if __name__ == "__main__":
    sumoCmd = ["sumo", "--step-length", "0.1", 
           "--tripinfo-output", os.path.join("sim_cfg_3_lanes", "tripinfo2.xml"),
           "-c", os.path.join("sim_cfg_3_lanes", "4way.sumo.cfg")]
    traci.start(sumoCmd)
    
    step = 0
    while step < STEPS:
        traci.simulationStep()
        step += 0.1
    traci.close()