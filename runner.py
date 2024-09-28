import os
import sys
import traci
import sumolib
import traci.constants
from Platoon import PlatoonManager
from utils import Utils

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 500
MIN_GAP = 4
PLATOON_SPEED = 11
MAX_DECELERATION = -8
# nubmer of vehicles that pass intersection in worst case (no platoons, turn left) = 26 (measured with the current parameters using runner2.py)
MAX_VEHICLES_TO_OPTIMIZE = 26


def create_platoon(platoon_members: list[str], lane: str) -> None:
    if len(platoon_members) > 1:
        platoon_manager.create_platoon(platoon_members, lane)
    platoon_members.clear()


def initialize_tls_phases(tls_state, all_junctions) -> None:
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
        if state[lane] != 'r' or new_state[lane] != 'G':
            continue
        
        platoon_length = 0
        vids = traci.lane.getLastStepVehicleIDs(lane)[::-1]
        if len(vids) == 0:
            continue
        leader_next_edge = Utils.getNextEdge(vids[0])
        next_lane_space = utils.getLaneAvailableSpace(
            leader_next_edge if leader_next_edge else traci.vehicle.getRoadID(vids[0])
            )
        platoon_members = []
        i = 0
        print(f'lane: {lane}')
        while i < len(vids) and i < MAX_VEHICLES_TO_OPTIMIZE:
            vid = vids[i]
            front_id = vids[i-1] if i > 0 else None
            platoon_length += platoon_manager.DISTANCE + traci.vehicle.getLength(vid)
            
            print(f"platoon_length: {platoon_length}")
            print(f"next_lane_space: {next_lane_space}")
            print(f"getNextEdge(vid): {Utils.getNextEdge(vid)}")
            if front_id:
                print(f"getNextEdge(front_id): {Utils.getNextEdge(front_id)}")
            print(f"waiting time: {traci.vehicle.getWaitingTime(vid)}")
            
            '''
            Since this segment of code is executed when the traffic light turns green, the waitingTime
            of the first vehicle (vids[0]) is set to zero. This is the reason why vid needs 
            to be different from vids[0] when checking the waitingTime.
            '''
            if ((vid != vids[0] and not traci.vehicle.getWaitingTime(vid)) or 
                platoon_length > next_lane_space):
                print(f'exiting while loop')
                break
            
            if front_id and (Utils.getNextEdge(vid) != Utils.getNextEdge(front_id) or 
                             platoon_manager.get_distance(vid) >= MIN_GAP):
                print(platoon_members)
                create_platoon(platoon_members, lane)
                
            print(f'vid: {vid}, lane change state: {traci.vehicle.getLaneChangeStatePretty(vid, traci.constants.LCA_BLOCKED)[0]}')
            # if not vid has to change lane, i.e. left or right in the changelanestate bit mask
            left_flag = 2**1
            right_flag = 2**2
            if utils.checkLaneChange(vid, left_flag) or utils.checkLaneChange(vid, right_flag):
                print(platoon_members)
                create_platoon(platoon_members, lane)
            else:
                print(f'vid added: {vid}')
                platoon_members.append(vid)
            
            i += 1
        print(platoon_members)
        if len(platoon_members) < 2:
            continue
        platoon_manager.create_platoon(platoon_members, lane)
        

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
        iterate_on_controlled_lanes(set(controlled_lanes), tls_state[junction], new_state)
        tls_state[junction] = new_state
        

if __name__ == "__main__":
    # parse the net
    net = sumolib.net.readNet(os.path.join("sim_cfg_grid", "grid.net.xml"))
    
    # command to start the simulation
    sumoCmd = ["sumo-gui", "--step-length", "0.1",
           "--tripinfo-output", os.path.join("sim_cfg_grid_2_lanes", "tripinfo.xml"),
           "-c", os.path.join("sim_cfg_grid_2_lanes", "grid.sumo.cfg")]
    traci.start(sumoCmd)
    
    platoon_manager = PlatoonManager(MIN_GAP, MAX_DECELERATION, PLATOON_SPEED)
    utils = Utils(net, MIN_GAP, PlatoonManager.DISTANCE)
    
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
    out.write("nodeId,time,distance,relativeSpeed,speed,acceleration\n")
    
    traci.addStepListener(platoon_manager.plexe)
    
    # getLeader method returns ("", -1) when there is not a vehicle ahead
    traci.setLegacyGetLeader(False)
    
    initialize_tls_phases(tls_state, all_junctions)
    
    step = 0
    while step < STEPS:
        # check on platoons last members
        platoon_manager.clear_dead_platoons()
        
        # set braking maneuver for platoons approaching the end of the road
        platoon_manager.set_braking_state()
        
        # check whether there is any member's MinGap value to be restored
        platoon_manager.restore_min_gap()
        
        iterate_on_tls_junctions(all_junctions)
        
        for lane in platoon_manager.platoons:
            # simulate intra-platoon communication
            platoon_manager.communicate(lane)
            
            # log platoon metrics in the current step
            platoon_manager.log_platoon_data(step, lane, out)
        
        traci.simulationStep()
        step += 0.1
             
    out.close()           
    traci.close()
    sys.stdout.flush()