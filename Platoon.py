import traci
import random
from typing import Optional
from plexe import Plexe, ACC, CACC, DRIVER

class PlatoonManager:
    # inter-vehicle distance
    DISTANCE = 1.5
    
    @classmethod
    def create_platoon(cls, lid: str, vids: list[str], plexe: Plexe) -> dict[str, dict[str, str]]:
        """
        Create a platoon of n vehicles.

        Args:
            lid (str): leader id
            vids (list[str]): list of members0 ids to add to the platoon
            plexe (Plexe): API instance

        Returns:
            dict[str, dict[str, str]]: the topology of the platoon, i.e., a dictionary which
            indicates, for each vehicle, who is its leader and who is its front vehicle.
        """
        print(f"Creating a platoon composed of {lid} {vids}")
        traci.vehicle.setSpeedMode(lid, 0)
        color = tuple(random.randint(0, 254) for x in range(3)) + (255,)
        traci.vehicle.setColor(lid, color=color)
        plexe.set_active_controller(lid, ACC)
        topology = {}
        topology[lid] = {"front" : None, "leader" : lid}
        for i in range(len(vids)):
            vid = vids[i]
            frontvid = vids[i-1] if i-1>=0 else lid
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setColor(vid, traci.vehicle.getColor(lid))
            plexe.set_active_controller(vid, CACC)
            plexe.set_path_cacc_parameters(vid, distance=cls.DISTANCE)
            topology[vid] = {"front" : frontvid, "leader" : lid}
            plexe.enable_auto_feed(vid, True, lid, frontvid)
        return topology
    
    @classmethod
    def add_vehicle(cls, topology: Optional[dict[str, dict[str, str]]], vid: str, frontvid: str, 
                    plexe: Plexe) -> None:
        """
        Add a vehicle to an existing platoon.

        Args:
            topology (dict[str, dict[str, str]]): topology of the platoon
            vid (str): new member id
            frontvid (str): new member's front vehicle id
            plexe (Plexe): API instance
        """
        if not topology: return
        lid = topology[frontvid]["leader"]
        traci.vehicle.setSpeedMode(vid, 0)
        traci.vehicle.setColor(vid, traci.vehicle.getColor(lid))
        plexe.set_active_controller(vid, CACC)
        plexe.set_path_cacc_parameters(vid, distance=cls.DISTANCE)
        topology[vid] = {"front" : frontvid, "leader" : lid}
        plexe.enable_auto_feed(vid, True, lid, frontvid)
        return
        
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
            plexe.set_active_controller(vid, DRIVER)
            plexe.enable_auto_feed(vid, False)