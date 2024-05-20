import traci
import random
from typing import Optional
from plexe import Plexe, CACC, ACC, DRIVER

class PlatoonManager:
    # inter-vehicle distance
    DISTANCE = 3
    
    @classmethod
    def create_platoon(cls, vids: list[str], plexe: Plexe) -> dict[str, dict[str, str]]:
        """
        Create a platoon of n vehicles.

        Args:
            vids (list[str]): list of members0 ids to add to the platoon
            plexe (Plexe): API instance

        Returns:
            dict[str, dict[str, str]]: the topology of the platoon, i.e., a dictionary which
            indicates, for each vehicle, who is its leader and its front vehicle.
        """
        lid = vids[0]
        print(f"Creating a platoon composed of {lid} {vids}")
        traci.vehicle.setSpeedMode(lid, 31)
        color = tuple(random.randint(0, 254) for x in range(3)) + (255,)
        traci.vehicle.setColor(lid, color=color)
        plexe.set_active_controller(lid, DRIVER)
        plexe.use_controller_acceleration(lid, False)
        plexe.set_path_cacc_parameters(lid, cls.DISTANCE, 2, 1, 0.5)
        plexe.set_acc_headway_time(lid, 1.5)
        topology = {}
        topology[lid] = {"front" : None, "leader" : lid}
        for i in range(1, len(vids)):
            vid = vids[i]
            traci.vehicle.setMinGap(vid, 0)
            frontvid = vids[i-1]
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setColor(vid, color)
            plexe.set_active_controller(vid, CACC)
            topology[vid] = {"front" : frontvid, "leader" : lid}
            plexe.use_controller_acceleration(vid, False)
            plexe.set_path_cacc_parameters(vid, cls.DISTANCE, 2, 1, 0.5)
            plexe.set_acc_headway_time(vid, 1.5)
        return topology
        
    @classmethod
    def clear_platoon(cls, topology: Optional[dict[str, dict[str, str]]], plexe: Plexe) -> None:
        """
        Disassemble a platoon.

        Args:
            topology (dict[str, dict[str, str]]): topology of the platoon
            plexe (Plexe): API instance
        """
        if not topology: return
        print(f"Freeing a platoon composed of {topology}")
        for vid in topology:
            traci.vehicle.setSpeedMode(vid, 31)
            traci.vehicle.setColor(vid, (255,255,255,255))
            plexe.set_active_controller(vid, DRIVER)
            traci.vehicle.setMinGap(vid, 1.8)
            
    @classmethod
    def communicate(cls, topology: Optional[dict[str, dict[str, str]]], plexe: Plexe) -> None:
        """
        Performs data transfer between vehicles, i.e., fetching data from
        leading and front vehicles to feed the CACC algorithm.
        
        Args:
            plexe (Plexe): API instance
            topology (dict[str, dict[str, str]]): a dictionary pointing each vehicle id to its front
            vehicle and platoon leader. Each entry of the dictionary is a dictionary
            which includes the keys "leader" and "front".
        """
        if not topology:
            return
        
        '''
        Access to the dictionary associated to the first topology element in order to get 
        the leader id through the "leader" key.
        '''
        v = next(iter(topology.items()))[1]
        try:
            # get data about platoon leader
            ld = plexe.get_vehicle_data(v["leader"])
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
        
        for vid, l in topology.items():
            print(f"vehicle: {vid}")
            if vid == l["leader"]:
                continue
            # pass leader vehicle data to CACC
            plexe.set_leader_vehicle_data(vid, ld)
            if "front" in l.keys():
                # get data about the front vehicle
                fd = plexe.get_vehicle_data(l["front"])
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
                plexe.set_front_vehicle_data(vid, fd)
        return