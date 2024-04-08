import traci
from plexe import Plexe, ACC, CACC

# inter-vehicle distance
DISTANCE = 5

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
                cls.plexe.set_active_controller(vid, ACC)
                leader = vid
            else:
                cls.plexe.set_active_controller(vid, CACC)
                cls.plexe.set_path_cacc_parameters(vid, distance=traci.vehicle.getLength(vid)*2)
                topology[vid] = {"front" : sorted_vids[i-1], "leader" : leader}
            