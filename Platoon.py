import traci
import random
from plexe import ACC, CACC

# inter-vehicle distance
DISTANCE = 1

class PlatoonManager:
    """ 
    create a platoon of n vehicles
    :param lid: leader id
    :param vids: list of members' ids to add to the platoon
    :return: returns the topology of the platoon, i.e., a dictionary which
    indicates, for each vehicle, who is its leader and who is its front
    vehicle.
    """
    @staticmethod
    def create_platoon(lid, vids, plexe):
        traci.vehicle.setSpeedMode(lid, 0)
        traci.vehicle.setColor(lid, [random.randint(0, 254) for x in range(3)].append(1))
        plexe.set_active_controller(lid, ACC)
        topology = {}
        for i in range(len(vids)):
            vid = vids[i]
            frontvid = vids[i-1] if i-1>=0 else lid
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setColor(vid, traci.vehicle.getColor(lid))
            plexe.set_active_controller(vid, CACC)
            plexe.set_path_cacc_parameters(vid, distance=DISTANCE)
            topology[vid] = {"front" : frontvid, "leader" : lid}
            plexe.enable_auto_feed(vid, True, lid, frontvid)
        return topology
    
    @staticmethod
    def add_vehicle(topology, vid, frontvid, plexe):
        if not topology: return
        lid = topology[frontvid]["leader"]
        traci.vehicle.setSpeedMode(vid, 0)
        traci.vehicle.setColor(vid, traci.vehicle.getColor(lid))
        plexe.set_activate_controller(vid, CACC)
        plexe.set_path_cacc_parameters(vid, distance=DISTANCE)
        topology[vid] = {"front" : frontvid, "leader" : lid}
        plexe.enable_auto_feed(vid, True, lid, frontvid)
        return
        
    @staticmethod
    def free_platoon(lid, topology, plexe):
        if not topology: return
        traci.vehicle.setSpeedMode(lid, 31)
        traci.vehicle.setColor(lid, [255,255,255,1])
        for vid in topology:
            traci.vehicle.setSpeedMode(vid, 31)
            traci.vehicle.setColor(vid, [255,255,255,1])
            plexe.set_active_controller(ACC)
            plexe.enable_auto_feed(vid, False)