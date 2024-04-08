import traci
import random
from plexe import Plexe, ACC, CACC

# inter-vehicle distance
DISTANCE = 1.5

class PlatoonManager:
    plexe = Plexe()
    
    
    @classmethod
    def create_platoon(cls, vids):
        sorted_vids = sorted(vids, key=lambda x : traci.vehicle.getLanePosition(x), reverse=True)
        # add a platoon of n vehicles
        topology = {}
        for i in range(len(sorted_vids)):
            vid = sorted_vids[i]
            traci.vehicle.setSpeedMode(vid, 0)
            if vid == sorted_vids[0]:
                traci.vehicle.setColor(vid, [random.randint(0, 254) for x in range(3)].append(1))
                cls.plexe.set_active_controller(vid, ACC)
                leader = vid
            else:
                traci.vehicle.setColor(vid, traci.vehicle.getColor(leader))
                cls.plexe.set_active_controller(vid, CACC)
                cls.plexe.set_path_cacc_parameters(vid, distance=DISTANCE)
                topology[vid] = {"front" : sorted_vids[i-1], "leader" : leader}
        return topology
    
# create a platoon when the next traffic light (the one after the tl in the current edge) 
# is the same for each vehicle using traci.vehicle.getNextTLS()
            