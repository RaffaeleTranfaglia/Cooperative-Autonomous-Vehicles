import traci
import random
from typing import Optional
from plexe import Plexe, ACC, CACC

# inter-vehicle distance
DISTANCE = 1

class PlatoonManager:
    @staticmethod
    def create_platoon(lid: str, vids: list[str], plexe: Plexe) -> dict[str, dict[str, str]]:
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
    def add_vehicle(topology: Optional[dict[str, dict[str, str]]], vid: str, frontvid: str, 
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
        plexe.set_path_cacc_parameters(vid, distance=DISTANCE)
        topology[vid] = {"front" : frontvid, "leader" : lid}
        plexe.enable_auto_feed(vid, True, lid, frontvid)
        return
        
    @staticmethod
    def free_platoon(lid: Optional[str], topology: Optional[dict[str, dict[str, str]]], 
                     plexe: Plexe) -> None:
        """
        Disassemble a platoon.

        Args:
            lid (str): leader vehicle id
            topology (dict[str, dict[str, str]]): topology of the platoon
            plexe (Plexe): API instance
        """
        if not topology or not lid: return
        traci.vehicle.setSpeedMode(lid, 31)
        traci.vehicle.setColor(lid, [255,255,255,1])
        for vid in topology:
            traci.vehicle.setSpeedMode(vid, 31)
            traci.vehicle.setColor(vid, [255,255,255,1])
            plexe.set_active_controller(vid, ACC)
            plexe.enable_auto_feed(vid, False)