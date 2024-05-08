import traci
import random
from typing import Optional
from plexe import Plexe, CACC, ACC, DRIVER

class PlatoonManager:
    # inter-vehicle distance
    DISTANCE = 2
    
    @classmethod
    def create_platoon(cls, vids: list[str], plexe: Plexe) -> dict[str, dict[str, str]]:
        """
        Create a platoon of n vehicles.

        Args:
            vids (list[str]): list of members0 ids to add to the platoon
            plexe (Plexe): API instance

        Returns:
            dict[str, dict[str, str]]: the topology of the platoon, i.e., a dictionary which
            indicates, for each vehicle, who is its leader and who is its front vehicle.
        """
        lid = vids[0]
        print(f"Creating a platoon composed of {lid} {vids}")
        traci.vehicle.setSpeedMode(lid, 31)
        color = tuple(random.randint(0, 254) for x in range(3)) + (255,)
        traci.vehicle.setColor(lid, color=color)
        plexe.set_active_controller(lid, DRIVER)
        plexe.use_controller_acceleration(lid, False)
        topology = {}
        topology[lid] = {"front" : None, "leader" : lid}
        for i in range(1, len(vids)):
            vid = vids[i]
            traci.vehicle.setMinGap(vid, 0)
            frontvid = vids[i-1]
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setColor(vid, traci.vehicle.getColor(lid))
            plexe.set_active_controller(vid, CACC)
            plexe.use_controller_acceleration(vid, False)
            plexe.set_path_cacc_parameters(vid, distance=cls.DISTANCE)
            topology[vid] = {"front" : frontvid, "leader" : lid}
            #plexe.enable_auto_feed(vid, True, lid, frontvid)
        return topology
    
    '''
    @classmethod
    def add_vehicle(cls, topology: Optional[dict[str, dict[str, str]]], vid: str, frontvid: str, 
                    plexe: Plexe) -> dict[str, dict[str, str]]:
        """
        Add a vehicle to an existing platoon.

        Args:
            topology (dict[str, dict[str, str]]): topology of the platoon
            vid (str): new member id
            frontvid (str): new member's front vehicle id
            plexe (Plexe): API instance
        """
        lid = topology[frontvid]["leader"]
        traci.vehicle.setSpeedMode(vid, 0)
        traci.vehicle.setColor(vid, traci.vehicle.getColor(lid))
        plexe.set_active_controller(vid, CACC)
        plexe.use_controller_acceleration(vid, True)
        plexe.set_path_cacc_parameters(vid, distance=cls.DISTANCE)
        topology[vid] = {"front" : frontvid, "leader" : lid}
        #plexe.enable_auto_feed(vid, True, lid, frontvid)
        return None
    '''
        
    @classmethod
    def free_platoon(cls, topology: Optional[dict[str, dict[str, str]]], plexe: Plexe) -> None:
        """
        Disassemble a platoon.

        Args:
            topology (dict[str, dict[str, str]]): topology of the platoon
            plexe (Plexe): API instance
        """
        if not topology: return
        print(f"Freeing a platoon composed of {topology.keys}")
        for vid in topology:
            traci.vehicle.setSpeedMode(vid, 31)
            traci.vehicle.setColor(vid, (255,255,255,255))
            plexe.use_controller_acceleration(vid, False)
            plexe.set_active_controller(vid, DRIVER)
            traci.vehicle.setMinGap(vid, 2)
            #plexe.enable_auto_feed(vid, False)
            
    @classmethod
    def communicate(cls, topology: Optional[dict[str, dict[str, str]]], plexe: Plexe) -> None:
        """
        Performs data transfer between vehicles, i.e., fetching data from
        leading and front vehicles to feed the CACC algorithm
        :param plexe: API instance
        :param topology: a dictionary pointing each vehicle id to its front
        vehicle and platoon leader. each entry of the dictionary is a dictionary
        which includes the keys "leader" and "front"
        """
        if not topology:
            return
        
        k, v = next(iter(topology.items()))
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