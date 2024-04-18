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

def getPlatoonTopology(vid, laneid, platoons):
    for topology in platoons.get(laneid, list()):
        if vid in topology: 
            return topology
    return None

def getNextEdge(vid):
    edges = traci.vehicle.getRoute(vid)
    curr = traci.vehicle.getRoadID(vid)
    i = 0
    while i < len(edges):
        if edges[i] == curr:
            return edges[i+1] if i+1 < len(edges) else None
        i += 1
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
        for v, ce, ne in last_members[:]:    # Iterate over a copy of the list
            print(f"vehicle: {v} - currentEdge: {traci.vehicle.getRoadID(v)} - nextEdge: {ne}")
            if traci.vehicle.getRoadID(v) == ne:
                topology = getPlatoonTopology(v, ce, platoons)
                PlatoonManager.free_platoon(topology, plexe)
                last_members.remove((v, ce, ne))
        
        for junction in all_junctions:
            controlled_lanes = traci.trafficlight.getControlledLanes(junction)
            for lane in controlled_lanes:
                if lane not in platoons:
                    platoons[lane] = []
                vids = traci.lane.getLastStepVehicleIDs(lane)
                i = len(vids) - 1
                while i >= 0:
                    print(f"vehicle: {vids[i]} -  position {traci.vehicle.getLanePosition(vids[i])} - length {traci.vehicle.getLength(vids[i])}")
                    ti = getPlatoonTopology(vids[i], traci.vehicle.getLaneID(vids[i]), platoons)
                    if not ti:
                        if (i+1 < len(vids) 
                            and traci.vehicle.getLanePosition(vids[i+1]) - traci.vehicle.getLength(vids[i+1]) - traci.vehicle.getLanePosition(vids[i]) <= PlatoonManager.DISTANCE
                            and getNextEdge(vids[i]) == getNextEdge(vids[i+1])):
                            tnext = getPlatoonTopology(vids[i+1], traci.vehicle.getLaneID(vids[i+1]), platoons)
                            PlatoonManager.add_vehicle(tnext if tnext else None, vids[i], vids[i+1], plexe)
                            for v, ce, ne in last_members:
                                if v == vids[i+1]:
                                    last_members.remove((v, ce, ne))
                                    last_members.append((vids[i], traci.vehicle.getLaneID(vids[i]), getNextEdge(vids[i])))
                        
                        lid = vids[i]
                        j = i - 1
                        next_edg = getNextEdge(lid)
                        print(f"vehicle: {lid} -  next_edg {next_edg}")
                        members = []
                        while (j >= 0 and next_edg == getNextEdge(vids[j]) 
                               and traci.vehicle.getLanePosition(vids[j+1]) - traci.vehicle.getLength(vids[j+1]) - traci.vehicle.getLanePosition(vids[j]) <= PlatoonManager.DISTANCE):
                            members.append(vids[j])
                            j -= 1
                        if len(members) > 0:
                            platoons[lane].append(PlatoonManager.create_platoon(lid, members, plexe))
                            last_members.append((vids[j+1], traci.vehicle.getLaneID(vids[j+1]), getNextEdge(vids[j+1])))
                        i = j
                    else:
                        i -= 1
                # simulate vehicle communication every step
                for topology in platoons[lane]:
                    PlatoonManager.communicate(topology, plexe)
        step += 0.1
                        
    traci.close()
    sys.stdout.flush()
        