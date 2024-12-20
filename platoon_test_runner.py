import os
import sys
import traci
from Platoon import PlatoonManager

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")
    
STEPS = 500
MIN_GAP = 2
        

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
        if state[lane] != 'r' or new_state[lane] != 'G':
            continue
        
        platoon_length = 0
        vids = traci.lane.getLastStepVehicleIDs(lane)[::-1]
        if len(vids) == 0:
            continue
        platoon_members = []
        i = 0
        while i < len(vids):
            vid = vids[i]
            front_id = vids[i-1] if i > 0 else None
            platoon_length += traci.vehicle.getMinGap(vid) + traci.vehicle.getLength(vid)
            
            '''
            Since this segment of code is executed when the traffic light turns green, the waitingTime
            of the first vehicle (vids[0]) is set to zero. This is the reason why vid needs 
            to be different from vids[0] when checking the waitingTime.
            '''
            if ((vid != vids[0] and traci.vehicle.getWaitingTime(vid) == 0)):
                break
            platoon_members.append(vid)
            i += 1
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
        iterate_on_controlled_lanes(controlled_lanes, tls_state[junction], new_state)
        tls_state[junction] = new_state
        

if __name__ == "__main__":
    # command to start the simulation
    sumoCmd = ["sumo-gui", "--step-length", "0.1",
           "--tripinfo-output", os.path.join("platoon_test","sim_cfg", "tripinfo.xml"),
           "-c", os.path.join("platoon_test", "sim_cfg", "2way.sumo.cfg")]
    traci.start(sumoCmd)
    
    platoon_manager = PlatoonManager(MIN_GAP)
    
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
    out = open(os.path.join("platoon_test", "benchmarks", "log.csv"), "w")
    out.write("nodeId,time,distance,relativeSpeed,speed,acceleration\n")
    
    traci.addStepListener(platoon_manager.plexe)
    
    # getLeader method returns ("", -1) when there is not a vehicle ahead
    traci.setLegacyGetLeader(False)
    
    initialize_tls_phases(tls_state, all_junctions)
    
    step = 0
    while step < STEPS:
        iterate_on_tls_junctions(all_junctions)
        
        to_remove = []
        for lane in platoon_manager.platoons:
            print(len(platoon_manager.platoons[lane]))
            key = next(iter(platoon_manager.platoons[lane]))
            if (traci.vehicle.getDistance(platoon_manager.platoons[lane][key]["leader"]) >= 5000):
                platoon_manager._clear_platoon(platoon_manager.platoons[lane])
                to_remove.append(lane)
                continue
            
            # simulate intra-platoon communication
            platoon_manager.communicate(lane)
            
            # log platoon metrics in the current step
            platoon_manager.log_platoon_data(step, lane, out)
        
        for lane in to_remove:
            del platoon_manager.platoons[lane]
        
        traci.simulationStep()
        step += 0.1
    
    out.close()           
    traci.close()
    sys.stdout.flush()