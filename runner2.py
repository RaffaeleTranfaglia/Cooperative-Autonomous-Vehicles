import os
import sys
import traci

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 500

if __name__ == "__main__":
    sumoCmd = ["sumo-gui", "--step-length", "0.1",
           "--tripinfo-output", os.path.join("sim_cfg_grid", "tripinfo2.xml"),
           "-c", os.path.join("sim_cfg_grid", "grid.sumo.cfg")]
    traci.start(sumoCmd)
    
    step = 0
    while step < STEPS:
        traci.simulationStep()
        step += 0.1
    traci.close()