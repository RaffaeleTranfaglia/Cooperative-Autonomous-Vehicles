import sys
import traci
from typing import Optional
from traci.constants import LCA_BLOCKED

class Utils:
    def __init__(self, min_gap, platoon_intervehicle_distance):
        self.min_gap = min_gap
        self.platoon_intervehicle_distance = platoon_intervehicle_distance

    @staticmethod
    def getNextEdge(vid: str) -> Optional[str]:
        """
        Get the next edge of the vehicle route.

        Args:
            vid (str): vehicle id

        Returns:
            str: if exists, the next road id, otherwise None
        """
        edges = traci.vehicle.getRoute(vid)
        curr = traci.vehicle.getRoadID(vid)
        i = 0
        while i < len(edges):
            if edges[i] == curr:
                return edges[i+1] if i+1 < len(edges) else None
            i += 1
        return None


    def getLaneAvailableSpace(self, edge, net):
        """
        The remaining available space (in meters) in the given edge.
        The available space is computed for every lane in the edge and the returned value is the minor.
        It is computed by subtracting the space occupied by the vehicles currently in the lane from the lane length.

        Args:
            edge (str): edge id

        Returns:
            float: remaining available space in meters
        """

        available_space = sys.float_info.max
        for lane in net.getEdge(edge).getLanes():
            lane_id = lane.getID()
            lane_length = traci.lane.getLength(lane_id)
            n_vids = traci.lane.getLastStepVehicleNumber(lane_id)
            occupied_space = n_vids + n_vids * max(self.min_gap, self.platoon_intervehicle_distance)
            available_space = min(available_space, lane_length - occupied_space)
        
        return available_space
    
    
    @staticmethod
    def checkLaneChange(vid: str, bitmask: int) -> bool:
        return (traci.vehicle.getLaneChangeState(vid, LCA_BLOCKED)[0] & bitmask) == bitmask
    
    @staticmethod
    def getTotalEdgesLength(net) -> float:
        """
        Compute the sum of the lengths of all edges

        Returns:
            float: Total edges length
        """
        return sum(edge.getLength() for edge in net.getEdges())