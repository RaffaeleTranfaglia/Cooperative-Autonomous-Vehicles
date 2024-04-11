import os
import sys
import traci
from plexe import Plexe
from Platoon import PlatoonManager

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 500

def getPlatoonTopology(vid, platoons):
    for topologies in platoons[traci.vehicle.getLaneID(vid)]:
        for t in topologies:
            if vid in t : return t
    return None

def getNextEdge(vid):
    edges = traci.vehicle.getRoute(vid)
    curr = traci.vehicle.getRoadID(vid)
    i = 0
    while i <= len(edges):
        if edges[i] == curr:
            return edges[i]
    return None
    

if __name__ == "__main__":
    sumoCmd = ["sumo-gui", "--step-length", "0.1",
           "--tripinfo-output", os.path.join("sim_cfg", "tripinfo.xml"),
           "-c", os.path.join("sim_cfg", "4way.sumo.cfg")]
    traci.start(sumoCmd)
    
    platoons = {}
    last_members = []
    all_junctions = traci.trafficlight.getIDList()
    
    plexe = Plexe()
    traci.addStepListener(plexe)
    
    step = 0
    while step < STEPS:
        traci.simulationStep()
        
        # check on last platoons members here
        for v, e in last_members[:]:    # Iterate over a copy of the list
            if traci.vehicle.getRoadID(v) == e:
                topology = getPlatoonTopology(v, platoons)
                lid = topology[v]["leader"] if topology else None
                PlatoonManager.free_platoon(lid, topology, plexe)
                last_members.remove((v, e))
        
        for junction in all_junctions:
            controlled_lanes = traci.trafficlight.getControlledLanes(junction)
            for lane in controlled_lanes:
                platoons[lane] = []
                vids = traci.lane.getLastStepVehicleIDs(lane)
                i = len(vids) - 1
                while i >= 0:
                    ti = getPlatoonTopology(vids[i], platoons)
                    if not ti:
                        if (i+1 < len(vids) and getNextEdge(vids[i]) == getNextEdge(vids[i+1])):
                            tnext = getPlatoonTopology(vids[i+1], platoons)
                            PlatoonManager.add_vehicle(tnext if tnext else None, vids[i], vids[i+1], plexe)
                            for v, e in last_members:
                                if v == vids[i+1]:
                                    last_members.remove((v, e))
                                    last_members.append((vids[i], getNextEdge(vids[i])))
                        
                        lid = vids[i]
                        j = i - 1
                        next_edg = getNextEdge(lid)
                        print(f"vehicle: {lid} -  route {next_edg}")
                        members = []
                        while j >= 0 and next_edg == getNextEdge(vids[j]):
                            members.append(vids[j])
                            j -= 1
                        platoons[lane].append(PlatoonManager.create_platoon(lid, members, plexe))
                        last_members.append((vids[j+1], getNextEdge(vids[j+1])))
                        i = j
                        
                
                
    traci.close()
    sys.stdout.flush()
        