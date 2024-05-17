import os
import sys
import traci
from plexe import Plexe, RADAR_DISTANCE, RADAR_REL_SPEED
from Platoon import PlatoonManager

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 500
MIN_GAP = 2

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

def free_platoons():
    for v, current_lane, next_edge in last_members[:]:    # Iterate over a copy of the list
        if traci.vehicle.getRoadID(v) != next_edge:
            continue
        
        #topology = getPlatoonTopology(v, current_lane, platoons)
        topology = platoons[current_lane]
        PlatoonManager.free_platoon(topology, plexe)
        last_members.remove((v, current_lane, next_edge))
        # remove topology from platoons dict
        #platoons[current_lane].remove(topology)
        del platoons[current_lane]
        
def simulate_communication(lane):
    for topology in platoons[lane]: 
        PlatoonManager.communicate(topology, plexe)

def getLaneAvailableSpace(lane):
    lane_length = traci.lane.getLength(lane)
    vids = traci.lane.getLastStepVehicleIDs(lane)
    occupied_space = 0
    for vid in vids:
        occupied_space = traci.vehicle.getLength(vid) + traci.vehicle.getMinGap(vid)
    return lane_length - occupied_space
        

def iterate_on_controlled_lanes(controlled_lanes, state, new_state):
    for lane in controlled_lanes:
        if state[lane] != 'r' or new_state[lane] != 'G':
            continue
        
        next_lane_space = getLaneAvailableSpace(lane)
        platoon_length = 0
        vids = traci.lane.getLastStepVehicleIDs(lane)[::-1]
        print(vids)
        if len(vids) == 0:
            continue
        platoon_members = []
        for vid in vids:
            platoon_length += traci.vehicle.getMinGap(vid) + traci.vehicle.getLength(vid)
            front_id = traci.vehicle.getLeader(vid)[0]
            
            print(f"platoon_length: {platoon_length}")
            print(f"next_lane_space: {next_lane_space}")
            print(f"getNextEdge(vid): {getNextEdge(vid)}")
            if front_id:
                print(f"getNextEdge(front_id): {getNextEdge(front_id)}")
            print(f"waiting time: {traci.vehicle.getWaitingTime(vid)}")
                
            if ((vid != vids[0] and traci.vehicle.getWaitingTime(vid) == 0) or 
                platoon_length > next_lane_space or
                (front_id and getNextEdge(vid) != getNextEdge(front_id))):
                break
            platoon_members.append(vid)
        print(platoon_members)
        if len(platoon_members) < 2:
            continue
        topology = PlatoonManager.create_platoon(platoon_members, plexe)
        platoons[lane] = topology
        last_member = platoon_members[len(platoon_members) - 1]
        last_members.append((last_member, traci.vehicle.getLaneID(last_member), getNextEdge(last_member)))
        

def iterate_on_tls_junctions(all_junctions):
    for junction in all_junctions:
        controlled_lanes = traci.trafficlight.getControlledLanes(junction)
        state = traci.trafficlight.getRedYellowGreenState(junction)
        new_state = {}
        for i, lane in enumerate(controlled_lanes):
            new_state[lane] = state[i]
        iterate_on_controlled_lanes(controlled_lanes, tls_state[junction], new_state)
        tls_state[junction] = new_state
    

def initialize_tls_phases(tls_state, all_junctions):
    for junction in all_junctions:
        state = traci.trafficlight.getRedYellowGreenState(junction)
        tls_state[junction] = {}
        for i, lane in enumerate(traci.trafficlight.getControlledLanes(junction)):
            tls_state[junction][lane] = state[i]
        

def distance_intra_platoon(topology):
    for vid in topology:
        front, distance = traci.vehicle.getLeader(vid)
        print(vid + " " + front)
        print(f"Distance: {distance}")
        

if __name__ == "__main__":
    sumoCmd = ["sumo-gui", "--step-length", "0.1",
           "--tripinfo-output", os.path.join("sim_cfg", "tripinfo.xml"),
           "-c", os.path.join("sim_cfg", "4way.sumo.cfg")]
    traci.start(sumoCmd)
    
    platoons = {}
    last_members = []
    tls_state = {}
    all_junctions = traci.trafficlight.getIDList()
    out = open(os.path.join("sim_cfg", "log.csv"), "w")
    out.write("nodeId,time,distance,relativeSpeed,speed,acceleration,controllerAcceleration\n")
    
    plexe = Plexe()
    traci.addStepListener(plexe)
    
    # needed to GetLeader method to retrieve ('id', -1) when there is not a vehicle ahead
    traci.setLegacyGetLeader(False)
    
    initialize_tls_phases(tls_state, all_junctions)
    
    step = 0
    while step < STEPS:
        # check on last platoons members
        free_platoons()
        
        for lane in platoons:
            distance_intra_platoon(platoons[lane])
        
        iterate_on_tls_junctions(all_junctions)
        
        for lane in platoons:
            PlatoonManager.communicate(platoons[lane], plexe)
            
            for v in platoons[lane]:
                if v == platoons[lane][v]["leader"]:
                    distance = -1
                    rel_speed = 0
                else:
                    radar = plexe.get_radar_data(v)
                    distance = radar[RADAR_DISTANCE]
                    rel_speed = radar[RADAR_REL_SPEED]
                acc = traci.vehicle.getAcceleration(v)
                out.write(f"{v},{step},{distance},{rel_speed},{traci.vehicle.getSpeed(v)},{acc},{acc}\n")
    
        traci.simulationStep()
        step += 0.1
             
    out.close()           
    traci.close()
    sys.stdout.flush()