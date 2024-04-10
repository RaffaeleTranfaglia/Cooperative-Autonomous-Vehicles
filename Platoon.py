import traci
import random
from plexe import Plexe, ACC, CACC

# inter-vehicle distance
DISTANCE = 1

class PlatoonManager:
    def __init__(self, plexe = Plexe()):
        self.plexe = plexe
    
    """ 
    create a platoon of n vehicles
    :param lid: leader id
    :param vids: list of members' ids to add to the platoon
    :return: returns the topology of the platoon, i.e., a dictionary which
    indicates, for each vehicle, who is its leader and who is its front
    vehicle.
    """
    def create_platoon(self, lid, vids):
        traci.vehicle.setSpeedMode(lid, 0)
        traci.vehicle.setColor(vid, [random.randint(0, 254) for x in range(3)].append(1))
        self.plexe.set_active_controller(vid, ACC)
        topology = {}
        for i in range(len(vids)):
            vid = vids[i]
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setColor(vid, traci.vehicle.getColor(lid))
            self.plexe.set_active_controller(vid, CACC)
            self.plexe.set_path_cacc_parameters(vid, distance=DISTANCE)
            topology[vid] = {"front" : vids[i], "leader" : lid}
            #self.plexe.add_member(lid, vid, i)
        return topology
    
# create a platoon when the next traffic light (the one after the tl in the current edge) 
# is the same for each vehicle using traci.vehicle.getNextTLS()
            