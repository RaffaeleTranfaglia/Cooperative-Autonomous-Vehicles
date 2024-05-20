import os
import sys
import traci
import sumolib
from plexe import Plexe, RADAR_DISTANCE, RADAR_REL_SPEED
from Platoon import PlatoonManager
from typing import Optional

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 500
MIN_GAP = 2


def getNextEdge(vid: str) -> Optional[str]:
    """
    Get the next edge of the vehicle route.

    Args:
        vid (str): vehicle id

    Returns:
        str: if exists, the next road id, otherwise None
    """
    edges = traci.vehicle.getRoute(vid)
    curr = traci.vehicle.getRoadID(vid)
    i = 0
    while i < len(edges):
        if edges[i] == curr:
            return edges[i+1] if i+1 < len(edges) else None
        i += 1
    return None


def clear_platoons():
    """
    Check if there are any platoons that have crossed the intersection in order to clear them.
    """
    for v, current_lane, next_edge in last_members[:]:    # Iterate over a copy of the list
        if traci.vehicle.getRoadID(v) != next_edge:
            continue
        
        topology = platoons[current_lane]
        PlatoonManager.clear_platoon(topology, plexe)
        last_members.remove((v, current_lane, next_edge))
        # remove topology from platoons dict
        del platoons[current_lane]


def getLaneAvailableSpace(edge):
    """
    The remaining available space (in meters) in the given edge.
    The available space is computed for every lane in the edge and the returned value is the minor.
    It is computed by subtracting the space occupied by the vehicles currently in the lane from the lane length.

    Args:
        edge (str): edge id

    Returns:
        float: remaining available space in meters
    """

    available_space = sys.float_info.max
    for lane in net.getEdge(edge).getLanes():
        lane_id = lane.getID()
        lane_length = traci.lane.getLength(lane_id)
        n_vids = traci.lane.getLastStepVehicleNumber(lane_id)
        occupied_space = n_vids + n_vids * MIN_GAP
        available_space = min(available_space, lane_length - occupied_space)
    
    return available_space
        

def initialize_tls_phases(tls_state, all_junctions):
    """
    Initialize the state of all the traffic lights in the environment.

    Args:
        tls_state (dict): the state of the traffic lights, i.e., a dictionary which
            indicates, for each traffic light and for each lane in it, its state ("GgryusoO" format).
        all_junctions (list(str)): list of all the traffic lights' id
    """
    for junction in all_junctions:
        state = traci.trafficlight.getRedYellowGreenState(junction)
        tls_state[junction] = {}
        for i, lane in enumerate(traci.trafficlight.getControlledLanes(junction)):
            tls_state[junction][lane] = state[i]


def iterate_on_controlled_lanes(controlled_lanes, state, new_state):
    """
    Operations on traffic lights controlled lanes.

    Args:
        controlled_lanes (tuple(str)): list of lanes controlled by the traffic light
        state (dict(str,char)): dictionary associating each controlled lane 
        with its traffic light state in the last step
        new_state (dict(str,char)): dictionary associating each controlled lane 
        with its traffic light state in the current step
    """
    for lane in controlled_lanes:
        print(f"lane = {lane}")
        print(f"\tstate = {state[lane]}")
        print(f"\tnew state = {new_state[lane]}")
        if state[lane] != 'r' or new_state[lane] != 'G':
            continue
        
        print("it turned green")
        
        platoon_length = 0
        vids = traci.lane.getLastStepVehicleIDs(lane)[::-1]
        print(vids)
        if len(vids) == 0:
            continue
        next_lane_space = getLaneAvailableSpace(getNextEdge(vids[0]))
        platoon_members = []
        i = 0
        while i < len(vids):
            vid = vids[i]
            front_id = vids[i-1] if i > 0 else None
            platoon_length += traci.vehicle.getMinGap(vid) + traci.vehicle.getLength(vid)
            
            print(f"platoon_length: {platoon_length}")
            print(f"next_lane_space: {next_lane_space}")
            print(f"getNextEdge(vid): {getNextEdge(vid)}")
            if front_id:
                print(f"getNextEdge(front_id): {getNextEdge(front_id)}")
            print(f"waiting time: {traci.vehicle.getWaitingTime(vid)}")
            
            '''
            Since this segment of code is executed when the traffic light turns green, the waitingTime
            of the first vehicle (vids[0]) is set to zero. This is the reason why vid needs 
            to be different from vids[0] when checking the waitingTime.
            '''
            #TOBEFIXED check the following if statement
            print((vid != vids[0] and traci.vehicle.getWaitingTime(vid) == 0))
            print(platoon_length > next_lane_space)
            print((front_id and getNextEdge(vid) != getNextEdge(front_id)))
            if ((vid != vids[0] and traci.vehicle.getWaitingTime(vid) == 0) or 
                platoon_length > next_lane_space or
                (front_id and getNextEdge(vid) != getNextEdge(front_id))):
                break
            platoon_members.append(vid)
            i += 1
        print(platoon_members)
        if len(platoon_members) < 2:
            continue
        topology = PlatoonManager.create_platoon(platoon_members, plexe)
        platoons[lane] = topology
        last_member = platoon_members[len(platoon_members) - 1]
        last_members.append((last_member, traci.vehicle.getLaneID(last_member), getNextEdge(last_member)))
        

def iterate_on_tls_junctions(all_junctions):
    """
    Operations on traffic lights intersections.
    Each step update the traffic lights state.

    Args:
        all_junctions (list(str)): list of all the traffic lights' id
    """
    for junction in all_junctions:
        controlled_lanes = traci.trafficlight.getControlledLanes(junction)
        state = traci.trafficlight.getRedYellowGreenState(junction)
        new_state = {}
        for i, lane in enumerate(controlled_lanes):
            new_state[lane] = state[i]
        iterate_on_controlled_lanes(controlled_lanes, tls_state[junction], new_state)
        tls_state[junction] = new_state
        

if __name__ == "__main__":
    # parse the net
    net = sumolib.net.readNet(os.path.join("sim_cfg", "intelligent_traffic.net.xml"))
    
    # command to start the simulation
    sumoCmd = ["sumo-gui", "--step-length", "0.1",
           "--tripinfo-output", os.path.join("sim_cfg", "tripinfo.xml"),
           "-c", os.path.join("sim_cfg", "4way.sumo.cfg")]
    traci.start(sumoCmd)
    
    '''
    Dictionary storing all the topologies of the platoons currently operating in the environment.
    Each topology is associated to the lane where it was created.
    '''
    platoons = {}
    
    '''
    List of the last members of the platoons.
    The scope of the list is to keep track of the last member in order to kwow when the whole platoon has
    crossed the junction.
    '''
    last_members = []
    
    '''
    The state of the traffic lights. A dictionary which indicates, for each traffic light 
    and for each lane in it, its state ("GgryusoO" format).
    '''
    tls_state = {}
    
    '''
    List containing all the traffic lights id in the environment.
    '''
    all_junctions = traci.trafficlight.getIDList()
    
    
    # Log file containing the platoons related data.
    out = open(os.path.join("sim_benchmarks", "log.csv"), "w")
    out.write("nodeId,time,distance,relativeSpeed,speed,acceleration,controllerAcceleration\n")
    
    plexe = Plexe()
    traci.addStepListener(plexe)
    
    # getLeader method returns ("", -1) when there is not a vehicle ahead
    traci.setLegacyGetLeader(False)
    
    initialize_tls_phases(tls_state, all_junctions)
    
    step = 0
    while step < STEPS:
        # check on platoons last members
        clear_platoons()
        
        iterate_on_tls_junctions(all_junctions)
        
        for lane in platoons:
            # simulate intra-platoon communication
            PlatoonManager.communicate(platoons[lane], plexe)
            
            '''
            For each member of each platoon, retrieve the data needed for benchmarks.
            '''
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