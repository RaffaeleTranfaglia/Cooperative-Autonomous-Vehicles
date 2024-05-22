import traci
import random
from typing import Optional
from plexe import Plexe, CACC, ACC, DRIVER
from utils import Utils

class PlatoonManager:
    # inter-vehicle distance
    DISTANCE = 3
    
    def __init__(self, min_gap):
        '''
        Dictionary storing all the topologies of the platoons currently operating in the environment.
        Each topology is associated to the lane where it was created.
        '''
        self.platoons = {}
        
        '''
        Last members of the currently alive platoons.
        The scope of the set is to keep track of the last member in order to kwow when the whole platoon has
        crossed the junction.
        '''
        self.last_members = set()
        
        '''
        Past platoons members whose min_gap has been reduced.
        The scope of the set is to keep track of the vehicles whose min_gap has to be restored.
        '''
        self.ex_members = set()
        
        '''
        Minimum inter-vehicle gap of the simulation.
        '''
        self.min_gap = min_gap
        
        '''
        Plexe API
        '''
        self.plexe = Plexe()
    
    
    def create_platoon(self, vids: list[str], lane: str) -> None:
        """
        Create a platoon of n vehicles.

        Args:
            vids (list[str]): list of members0 ids to add to the platoon
            lane (str): id of the lane where the platoon is created
        """
        lid = vids[0]
        print(f"Creating a platoon composed of {lid} {vids}")
        traci.vehicle.setSpeedMode(lid, 31)
        color = tuple(random.randint(0, 254) for x in range(3)) + (255,)
        traci.vehicle.setColor(lid, color=color)
        self.plexe.set_active_controller(lid, DRIVER)
        self.plexe.use_controller_acceleration(lid, False)
        self.plexe.set_path_cacc_parameters(lid, self.DISTANCE, 2, 1, 0.5)
        topology = {}
        topology[lid] = {"front" : None, "leader" : lid}
        for i in range(1, len(vids)):
            vid = vids[i]
            traci.vehicle.setMinGap(vid, 0)
            frontvid = vids[i-1]
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setColor(vid, color)
            self.plexe.set_active_controller(vid, CACC)
            topology[vid] = {"front" : frontvid, "leader" : lid}
            self.plexe.use_controller_acceleration(vid, False)
            self.plexe.set_path_cacc_parameters(vid, self.DISTANCE, 2, 1, 0.5)
        
        self.platoons[lane] = topology
        last_member = vids[len(vids)-1]
        self.last_members.add((last_member, traci.vehicle.getLaneID(last_member), 
                                             Utils.getNextEdge(last_member)))
        return
        
    def clear_dead_platoons(self) -> None:
        """
        Check if there are any platoons that have crossed the intersection in order to clear them.
        A platoon is considered dead when the last member has succesfully crossed the intersection.
        """
        for v, current_lane, next_edge in self.last_members[:]:    # Iterate over a copy of the list
            if traci.vehicle.getRoadID(v) != next_edge:
                continue
            
            topology = self.platoons[current_lane]
            self.ex_members.update(topology.keys())
            self._clear_platoon(topology)
            self.last_members.remove((v, current_lane, next_edge))
            # remove topology from platoons dict
            del self.platoons[current_lane]
            return
    
    def _clear_platoon(self, topology: Optional[dict[str, dict[str, str]]]) -> None:
        """
        Disassemble a platoon.

        Args:
            topology (dict[str, dict[str, str]]): a dictionary pointing each vehicle id to its front
            vehicle and platoon leader; each entry of the dictionary is a dictionary
            which includes the keys "leader" and "front".
        """
        if not topology: return
        print(f"Freeing a platoon composed of {topology}")
        for vid in topology:
            traci.vehicle.setSpeedMode(vid, 31)
            traci.vehicle.setColor(vid, (255,255,255,255))
            self.plexe.set_active_controller(vid, DRIVER)
            if vid == topology[vid]["leader"]: continue
            
            '''
            In order to avoid collisions after changing controller, min_gap is set to a 
            value slightly lower than the actual distance. The original min_gap will be restored as soon 
            as the space between vehicles becomes available.
            '''
            distance = traci.vehicle.getLeader(vid)[1]
            new_distance = distance - (self.min_gap / 10)
            traci.vehicle.setMinGap(vid, new_distance if new_distance >= 1 else 1)
            return
            

    def communicate(self, lane: str) -> None:
        """
        Performs data transfer between vehicles, i.e., fetching data from
        leading and front vehicles to feed the CACC algorithm.
        
        Args:
            lane (str): lane id
        """
        topology = self.platoons[lane]
        if not topology:
            return
        
        '''
        Access to the dictionary associated to one of the elements in order to get 
        the leader id through the "leader" key.
        '''
        v = next(iter(topology.items()))[1]
        try:
            # get data about platoon leader
            ld = self.plexe.get_vehicle_data(v["leader"])
            print("leader vehicle data:")
            print(f"\tindex: {ld.index}")
            print(f"\tu: {ld.u }")
            print(f"\tacceleration: {ld.acceleration}")
            print(f"\tspeed: {ld.speed}")
            print(f"\tpos_x: {ld.pos_x}")
            print(f"\tpos_y: {ld.pos_y}")
            print(f"\ttime: {ld.time}")
            print(f"\tlength: {ld.length}")
        except KeyError:
            print ("The given dictionary does not have \"leader\" key")
            raise KeyError()
        
        for vid, references in topology.items():
            print(f"vehicle: {vid}")
            if vid == references["leader"]:
                continue
            # pass leader vehicle data to CACC
            self.plexe.set_leader_vehicle_data(vid, ld)
            try:
                # get data about the front vehicle
                fd = self.plexe.get_vehicle_data(references["front"])
                print("front vehicle data:")
                print(f"\tindex: {fd.index}")
                print(f"\tu: {fd.u}")
                print(f"\tacceleration: {fd.acceleration}")
                print(f"\tspeed: {fd.speed}")
                print(f"\tpos_x: {fd.pos_x}")
                print(f"\tpos_y: {fd.pos_y}")
                print(f"\ttime: {fd.time}")
                print(f"\tlength: {fd.length}")
                # pass front vehicle data to CACC
                self.plexe.set_front_vehicle_data(vid, fd)
            except KeyError:
                print ("The given dictionary does not have \"front\" key")
                raise KeyError()
        return
    
    def restore_min_gap(self):
        # continue here
        pass