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
        print("1")
        # check on last platoons members here
        for v, current_lane, next_edge in last_members[:]:    # Iterate over a copy of the list
            #print(f"vehicle: {v} - currentEdge: {traci.vehicle.getRoadID(v)} - nextEdge: {next_edge}")
            if traci.vehicle.getRoadID(v) == next_edge:
                topology = getPlatoonTopology(v, current_lane, platoons)
                PlatoonManager.free_platoon(topology, plexe)
                last_members.remove((v, current_lane, next_edge))
                # remove topology from platoons dict
                platoons[current_lane].remove(topology)
        print("2")
        
        for junction in all_junctions:
            controlled_lanes = traci.trafficlight.getControlledLanes(junction)
            for lane in controlled_lanes:
                if lane not in platoons:
                    platoons[lane] = []
                vids = traci.lane.getLastStepVehicleIDs(lane)
                i = len(vids) - 1
                while i >= 0:
                    #print(f"vehicle: {vids[i]} -  position {traci.vehicle.getLanePosition(vids[i])} - length {traci.vehicle.getLength(vids[i])}")
                    ti = getPlatoonTopology(vids[i], traci.vehicle.getLaneID(vids[i]), platoons)
                    if not ti:
                        if traci.vehicle.getLeader(vids[i]):
                            fid, dist = traci.vehicle.getLeader(vids[i])
                        else:
                            fid, dist = (None, 0)
                        if (fid and dist <= PlatoonManager.DISTANCE and traci.vehicle.getWaitingTime(vids[i]) > 0
                            and getNextEdge(vids[i]) == getNextEdge(fid)):
                            tnext = getPlatoonTopology(fid, traci.vehicle.getLaneID(fid), platoons)
                            topology = PlatoonManager.add_vehicle(tnext if tnext else None, vids[i], fid, plexe)
                            for v, ce, ne in last_members:
                                if v == fid:
                                    last_members.remove((v, ce, ne))
                            if topology: 
                                platoons[lane].append(topology)
                            last_members.append((vids[i], traci.vehicle.getLaneID(vids[i]), getNextEdge(vids[i])))
                        
                        '''
                        lid = vids[i]
                        j = i - 1
                        next_edge = getNextEdge(lid)
                        #print(f"vehicle: {lid} -  next_edg {next_edge}")
                        members = []
                        while (j >= 0 and traci.vehicle.getWaitingTime(vids[j+1]) > 0 
                               and traci.vehicle.getWaitingTime(vids[j]) > 0 
                               and next_edge == getNextEdge(vids[j]) 
                               and traci.vehicle.getLanePosition(vids[j+1]) - traci.vehicle.getLength(vids[j+1]) - traci.vehicle.getLanePosition(vids[j]) <= PlatoonManager.DISTANCE):
                            members.append(vids[j])
                            j -= 1
                        if len(members) > 0:
                            platoons[lane].append(PlatoonManager.create_platoon(lid, members, plexe))
                            last_members.append((vids[j+1], traci.vehicle.getLaneID(vids[j+1]), getNextEdge(vids[j+1])))
                        i = j
                        '''
                    i -= 1
                # simulate vehicle communication every step
                for topology in platoons[lane]:
                    PlatoonManager.communicate(topology, plexe)
        step += 0.1
                        
    traci.close()
    sys.stdout.flush()
        