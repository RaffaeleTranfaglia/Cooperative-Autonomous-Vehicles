import os
import sys
import traci

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 500

def isPlatoonMember(vid, platoons):
    for t in platoons[traci.vehicle.getLaneID()]:
        if vid in t : return True
    return False

if __name__ == "__main__":
    sumoCmd = ["sumo-gui", "--step-length", "0.1",
           "--tripinfo-output", os.path.join("sim_cfg", "tripinfo.xml"),
           "-c", os.path.join("sim_cfg", "4way.sumo.cfg")]
    traci.start(sumoCmd)
    
    platoons = {}
    all_junctions = traci.trafficlight.getIDList()
    
    step = 0
    while step < STEPS:
        traci.simulationStep()
        
        for junction in all_junctions:
            controlled_lanes = traci.trafficlight.getControlledLanes(junction)
            for lane in controlled_lanes:
                vids = traci.lane.getLastStepVehicleIDs(lane)
                
                i = len(vids) - 1
                while i >= 0:
                    vid = vids[i]
                    if not isPlatoonMember(vid, platoons):
                        # continue from here
                        pass
                
                
    traci.close()
    sys.stdout.flush()
        