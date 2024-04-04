from __future__ import absolute_import
from __future__ import print_function

from Agent import Agent

import os
import sys
import time
import optparse
import random
import numpy as np
import torch
import matplotlib.pyplot as plt

# we need to import python modules from the $SUMO_HOME/tools directory
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Environment variable 'SUMO_HOME' not defined.")

from sumolib import checkBinary  # noqa
import traci  # noqa

def get_vehicle_numbers(lanes):
    vehicle_per_lane = dict()
    for l in lanes:
        vehicle_per_lane[l] = 0
        for k in traci.lane.getLastStepVehicleIDs(l):
            if traci.vehicle.getLanePosition(k) > 10:
                vehicle_per_lane[l] += 1
    return vehicle_per_lane


def get_waiting_time(lanes):
    waiting_time = 0
    for lane in lanes:
        waiting_time += traci.lane.getWaitingTime(lane)
    return waiting_time


def phaseDuration(junction, phase_time, phase_state):
    traci.trafficlight.setRedYellowGreenState(junction, phase_state)
    traci.trafficlight.setPhaseDuration(junction, phase_time)


def run(train=True,model_name="model",epochs=50,steps=500,ard=False):
    '''
    if ard:
        arduino = serial.Serial(port='COM4', baudrate=9600, timeout=.1)
        def write_read(x):
            arduino.write(bytes(x, 'utf-8'))
            time.sleep(0.05)
            data = arduino.readline()
            return data
    '''
    """execute the TraCI control loop"""
    epochs = epochs
    steps = steps
    best_time = np.inf
    total_time_list = list()
    traci.start(
        [checkBinary("sumo"), "-c", "configuration.sumocfg", "--tripinfo-output", os.path.join("maps", "tripinfo.xml")]
    )
    all_junctions = traci.trafficlight.getIDList()
    junction_numbers = list(range(len(all_junctions)))

    brain = Agent(
        gamma=0.99,
        epsilon=0.0,
        lr=0.1,
        input_dims=4,
        # input_dims = len(all_junctions) * 4,
        fc1_dims=256,
        fc2_dims=256,
        batch_size=1024,
        n_actions=4,
        junctions=junction_numbers,
    )

    if not train:
        model_file = os.path.join("models", f"{model_name}.bin")
        brain.Q_eval.load_state_dict(torch.load(model_file,map_location=brain.Q_eval.device))

    print(brain.Q_eval.device)
    traci.close()
    for e in range(epochs):
        if train:
            traci.start(
            [checkBinary("sumo"), "-c", "configuration.sumocfg", "--tripinfo-output", os.path.join("maps", "tripinfo.xml")]
            )
        else:
            traci.start(
            [checkBinary("sumo-gui"), "-c", "configuration.sumocfg", "--tripinfo-output", os.path.join("maps", "tripinfo.xml")]
            )

        print(f"epoch: {e}")
        select_lane = [
            ["yyyrrrrrrrrr", "GGGrrrrrrrrr"],
            ["rrryyyrrrrrr", "rrrGGGrrrrrr"],
            ["rrrrrryyyrrr", "rrrrrrGGGrrr"],
            ["rrrrrrrrryyy", "rrrrrrrrrGGG"],
        ]

        # select_lane = [
        #     ["yyyyrrrrrrrrrrrr", "GGGGrrrrrrrrrrrr"],
        #     ["rrrryyyyrrrrrrrr", "rrrrGGGGrrrrrrrr"],
        #     ["rrrrrrrryyyyrrrr", "rrrrrrrrGGGGrrrr"],
        #     ["rrrrrrrrrrrryyyy", "rrrrrrrrrrrrGGGG"],
        # ]

        step = 0
        total_time = 0
        min_duration = 5
        
        traffic_lights_time = dict()
        prev_wait_time = dict()
        prev_vehicles_per_lane = dict()
        prev_action = dict()
        all_lanes = list()
        
        for junction_number, junction in enumerate(all_junctions):
            prev_wait_time[junction] = 0
            prev_action[junction_number] = 0
            traffic_lights_time[junction] = 0
            prev_vehicles_per_lane[junction_number] = [0] * 4
            # prev_vehicles_per_lane[junction_number] = [0] * (len(all_junctions) * 4) 
            all_lanes.extend(list(traci.trafficlight.getControlledLanes(junction)))

        while step <= steps:
            traci.simulationStep()
            for junction_number, junction in enumerate(all_junctions):
                controled_lanes = traci.trafficlight.getControlledLanes(junction)
                waiting_time = get_waiting_time(controled_lanes)
                total_time += waiting_time
                if traffic_lights_time[junction] == 0:
                    vehicles_per_lane = get_vehicle_numbers(controled_lanes)
                    # vehicles_per_lane = get_vehicle_numbers(all_lanes)

                    #storing previous state and current state
                    reward = -1 *  waiting_time
                    state_ = list(vehicles_per_lane.values()) 
                    state = prev_vehicles_per_lane[junction_number]
                    prev_vehicles_per_lane[junction_number] = state_
                    brain.store_transition(state, state_, prev_action[junction_number],reward,(step==steps),junction_number)

                    #selecting new action based on current state
                    lane = brain.choose_action(state_)
                    prev_action[junction_number] = lane
                    phaseDuration(junction, 6, select_lane[lane][0])
                    phaseDuration(junction, min_duration + 10, select_lane[lane][1])

                    '''
                    if ard:
                        ph = str(traci.trafficlight.getPhase("0"))
                        value = write_read(ph)
                    '''

                    traffic_lights_time[junction] = min_duration + 10
                    if train:
                        brain.learn(junction_number)
                else:
                    traffic_lights_time[junction] -= 1
            step += 1
        print("total_time",total_time)
        total_time_list.append(total_time)

        if total_time < best_time:
            best_time = total_time
            if train:
                brain.save(model_name)

        traci.close()
        sys.stdout.flush()
        if not train:
            break
    if train:
        plot_file = os.path.join("plots", f"time_vs_epoch_{model_name}.png")
        plt.plot(list(range(len(total_time_list))),total_time_list)
        plt.xlabel("epochs")
        plt.ylabel("total time")
        plt.savefig(plot_file)
        plt.show()

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option(
        "-m",
        dest='model_name',
        type='string',
        default="model",
        help="name of model",
    )
    optParser.add_option(
        "--train",
        action = 'store_true',
        default=False,
        help="training or testing",
    )
    optParser.add_option(
        "-e",
        dest='epochs',
        type='int',
        default=50,
        help="Number of epochs",
    )
    optParser.add_option(
        "-s",
        dest='steps',
        type='int',
        default=500,
        help="Number of steps",
    )
    optParser.add_option(
       "--ard",
        action='store_true',
        default=False,
        help="Connect Arduino", 
    )
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()
    model_name = options.model_name
    train = options.train
    epochs = options.epochs
    steps = options.steps
    ard = options.ard
    run(train=train,model_name=model_name,epochs=epochs,steps=steps,ard=ard)