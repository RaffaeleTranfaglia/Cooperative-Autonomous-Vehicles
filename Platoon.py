import math
import traci
import random
from typing import Optional
from plexe import Plexe, CACC, DRIVER, RADAR_DISTANCE, RADAR_REL_SPEED
from utils import Utils
from io import TextIOWrapper


class PlatoonManager:
    # inter-vehicle distance
    DISTANCE = 4
    
    def __init__(self, min_gap, max_deceleration, platoon_speed):
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
        Each platoon is associated with its state.
        Possible states:
            - standard: fixed speed
            - braking: fixed negative acceleration (deceleration)
        The state conditions are actually applied only to the leader.
        Accordingly the other members will follow the leader's behaviour.
        '''
        self.platoons_state = {}
        
        '''
        Minimum inter-vehicle gap of the simulation.
        '''
        self.min_gap = min_gap
        
        '''
        Maximum vehicle deceleration of the simulation. It is a negative float number.
        '''
        self.max_deceleration = max_deceleration
        
        '''
        Fixed speed that must be mantained by platoon members.
        '''
        self.platoon_speed = platoon_speed
        
        '''
        Plexe API
        '''
        self.plexe = Plexe()
        
    
    def _get_leader(self, lane, vid):
        for lid, topology in self.platoons[lane].items():
            if vid in topology:
                return lid
        return None
    
    
    def create_platoon(self, vids: list[str], lane: str) -> None:
        """
        Create a platoon of n vehicles.

        Args:
            vids (list[str]): list of members' id to add to the platoon
            lane (str): id of the lane where the platoon is created
        """
        
        self.platoons[lane] = {}
        
        lid = vids[0]
        print(f"Creating a platoon composed of {lid} {vids}")
        traci.vehicle.setSpeedMode(lid, 31)
        color = tuple(random.randint(0, 254) for x in range(3)) + (255,)
        traci.vehicle.setColor(lid, color=color)
        self.plexe.set_active_controller(lid, DRIVER)
        self.plexe.use_controller_acceleration(lid, False)
        self.plexe.set_path_cacc_parameters(lid, self.DISTANCE, 2, 1, 0.5)
        self.plexe.set_fixed_lane(lid, traci.vehicle.getLaneIndex(lid))
        traci.vehicle.setSpeed(lid, self.platoon_speed)
        topology = {}
        topology[lid] = {"front" : None}
        for i in range(1, len(vids)):
            vid = vids[i]
            traci.vehicle.setMinGap(vid, 0)
            frontvid = vids[i-1]
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setColor(vid, color)
            self.plexe.set_active_controller(vid, CACC)
            topology[vid] = {"front" : frontvid}
            self.plexe.use_controller_acceleration(vid, True)
            self.plexe.set_path_cacc_parameters(vid, self.DISTANCE, 2, 1, 0.5)
            self.plexe.set_fixed_lane(vid, traci.vehicle.getLaneIndex(vid))
        
        self.platoons[lane][lid] = topology
        self.platoons_state[lid] = "standard"
        last_member = vids[len(vids)-1]
        self.last_members.add((last_member, traci.vehicle.getLaneID(last_member), 
                                             Utils.getNextEdge(last_member)))
        return


    def clear_dead_platoons(self) -> None:
        """
        Check if there are any platoons that have crossed the intersection in order to clear them.
        A platoon is considered dead when the last member has succesfully crossed the intersection 
        and the inter-vehicle distance is reached for all the members, or if the platoon is stationary.
        """
        
        to_remove = set()
        for v, starting_lane, next_edge in self.last_members:
            lid = self._get_leader(starting_lane, v)
            if not lid:
                continue
            topology = self.platoons[starting_lane][lid]
            
            radar = self.plexe.get_radar_data(v)
            if (traci.vehicle.getRoadID(v) != next_edge or 
                (radar[RADAR_DISTANCE] < self.DISTANCE and 
                 traci.vehicle.getSpeed(lid)) >= 0.5):
                continue
            
            self.ex_members.update(topology.keys())
            self._clear_platoon(topology)
            to_remove.add((v, starting_lane, next_edge))
            # remove topology from platoons dict
            del self.platoons[starting_lane][lid]
            del self.platoons_state[lid]
        self.last_members.difference_update(to_remove)
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
            traci.vehicle.setSpeed(vid, -1)
            traci.vehicle.setColor(vid, (255,255,255,255))
            self.plexe.set_active_controller(vid, DRIVER)
            self.plexe.set_fixed_lane(vid, -1)
        return
            

    def communicate(self, lane: str) -> None:
        """
        Performs data transfer between vehicles, i.e., fetching data from
        leading and front vehicles to feed the CACC algorithm.
        
        Args:
            lane (str): lane id
        """
        
        for lid in self.platoons[lane]:
            topology = self.platoons[lane][lid]
            if not topology:
                continue
            
            try:
                # get data about platoon leader
                ld = self.plexe.get_vehicle_data(lid)
                '''
                print("leader vehicle data:")
                print(f"\tindex: {ld.index}")
                print(f"\tu: {ld.u }")
                print(f"\tacceleration: {ld.acceleration}")
                print(f"\tspeed: {ld.speed}")
                print(f"\tpos_x: {ld.pos_x}")
                print(f"\tpos_y: {ld.pos_y}")
                print(f"\ttime: {ld.time}")
                print(f"\tlength: {ld.length}")
                '''
            except KeyError:
                print ("The given dictionary does not have \"leader\" key")
                raise KeyError()
            
            for vid, references in topology.items():
                #print(f"vehicle: {vid}")
                if vid == lid:
                    continue
                # pass leader vehicle data to CACC
                self.plexe.set_leader_vehicle_data(vid, ld)
                try:
                    # get data about the front vehicle
                    fd = self.plexe.get_vehicle_data(references["front"])
                    '''
                    print("front vehicle data:")
                    print(f"\tindex: {fd.index}")
                    print(f"\tu: {fd.u}")
                    print(f"\tacceleration: {fd.acceleration}")
                    print(f"\tspeed: {fd.speed}")
                    print(f"\tpos_x: {fd.pos_x}")
                    print(f"\tpos_y: {fd.pos_y}")
                    print(f"\ttime: {fd.time}")
                    print(f"\tlength: {fd.length}")
                    '''
                    # pass front vehicle data to CACC
                    self.plexe.set_front_vehicle_data(vid, fd)
                except KeyError:
                    print ("The given dictionary does not have \"front\" key")
                    raise KeyError()
        return


    def _calculate_time(self, a, b, c):
            # Calculate the discriminant
            discriminant = b**2 - 4*a*c
            
            # Check if the discriminant is negative, which would mean no real solutions
            if discriminant < 0:
                return None
            
            '''
            Given that the searched value is a time, only the soulution with the positive 
            square root is calculated.
            '''
            t = (-b + math.sqrt(discriminant)) / (2*a)
            
            return t
        

    def set_braking_state(self) -> None:
        deceleration = self.max_deceleration/2
        braking_space = -(self.platoon_speed**2)/(2*deceleration)
        #braking_time = -(self.platoon_speed)/(deceleration)
        braking_time = self._calculate_time(0.5*deceleration, self.platoon_speed, -braking_space)
        
        for v, starting_lane, next_edge in self.last_members:
            '''
            if self.platoons_state[lid] == "braking":
                continue
            '''
            if traci.vehicle.getRoadID(v) != next_edge:
                continue
            
            lid = self._get_leader(starting_lane, v)
            topology = self.platoons[starting_lane][lid]
            current_position = traci.vehicle.getLanePosition(lid)
            lane_length = traci.lane.getLength(traci.vehicle.getLaneID(lid))
            remaining_distance = lane_length - current_position
            
            print(f"\nlid: {lid}")
            print(f"braking_space: {braking_space}")
            print(f"braking_time: {braking_time}")
            print(f"remaining_distance: {remaining_distance}")
            
            if self.platoons_state[lid] == "braking":
                print(f"speed: {traci.vehicle.getSpeed(lid)}")
                print(f"speed without traci: {traci.vehicle.getSpeedWithoutTraCI(lid)}")
                print(f"acceleration: {traci.vehicle.getAcceleration(lid)}")
                continue
            
            if remaining_distance <= braking_space + 5:
                print("starting braking")
                print(f"speed: {traci.vehicle.getSpeed(lid)}")
                print(f"speed without traci: {traci.vehicle.getSpeedWithoutTraCI(lid)}")
                print(f"acceleration: {traci.vehicle.getAcceleration(lid)}")
                traci.vehicle.setAcceleration(lid, deceleration, braking_time)
                self.platoons_state[lid] = "braking"


    def restore_min_gap(self) -> None:
        """
        Restore the MinGap value of past platoon members which have a reduced value due 
        to the platoon clearing maneuver.
        """
        
        members_restored = set()
        for vid in self.ex_members:
            '''
            If the vehicle has left the simulation or its minGap is already correct, it is removed 
            from the list of members with reduced minGap. Otherwise the minGap is restored to the original 
            value, provided that the distance from the front vehicle is sufficient.
            '''
            if (vid in traci.vehicle.getIDList() 
                and traci.vehicle.getMinGap(vid) != self.min_gap 
                and (traci.vehicle.getLeader(vid)[1] + traci.vehicle.getMinGap(vid) >= self.min_gap * 2)):
                traci.vehicle.setMinGap(vid, self.min_gap)
            members_restored.add(vid)
        self.ex_members.difference_update(members_restored)
        return
    
    def log_platoon_data(self, step: float, lane: str, out: TextIOWrapper):
        """
        For each member, retrieve the data needed for benchmarks.
        Data retrieved:
        - distance from the front vehicle (leader excluded)
        - relative speed to the front vehicle (leader excluded)
        - speed
        - acceleration
        The output is written in the given IO text stream.
        
        Args:
            step (float): current simulation step
            lane (str): lane id
            out (TextIOWrapper): output stream in which to write the platoon metrics
        """
        for lid, topology in self.platoons[lane].items():
            for v in topology:
                if v == lid:
                    distance = -1
                    rel_speed = 0
                else:
                    radar = self.plexe.get_radar_data(v)
                    distance = radar[RADAR_DISTANCE]
                    rel_speed = radar[RADAR_REL_SPEED]
                acc = traci.vehicle.getAcceleration(v)
                out.write(f"{v},{step},{distance},{rel_speed},{traci.vehicle.getSpeed(v)},{acc}\n")
        return