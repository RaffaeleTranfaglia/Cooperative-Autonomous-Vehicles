import sys
import traci
from typing import Optional

class Utils:
    def __init__(self, net, min_gap, platoon_intervehicle_distance):
        self.net = net
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
        print(f'edges: {edges}')
        print(f'curr: {curr}')
        while i < len(edges):
            if edges[i] == curr:
                return edges[i+1] if i+1 < len(edges) else None
            i += 1
        return None


    def getLaneAvailableSpace(self, edge):
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
        for lane in self.net.getEdge(edge).getLanes():
            lane_id = lane.getID()
            lane_length = traci.lane.getLength(lane_id)
            n_vids = traci.lane.getLastStepVehicleNumber(lane_id)
            occupied_space = n_vids + n_vids * max(self.min_gap, self.platoon_intervehicle_distance)
            available_space = min(available_space, lane_length - occupied_space)
        
        return available_space