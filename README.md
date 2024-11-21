# Managing intersections in a smart city exploiting the platooning system
The scope of the project is to optimize traffic flow in urban intersections by adopting the platooning system.  
Adjacent agents that have to turn the same way will aggregate into a platoon.  
[Here](./assets/clips/standard_simulation.zip) is shown the normal simulation and [here](./assets/clips/simulation_with_platooning.zip) the platooning algorythm behaviour.

## Installation
In order to set up the project the simulator [SUMO](https://eclipse.dev/sumo/) is required.

It is recommended to set up the workspace in a virtual environment.
To install dependencies:
```
pip install requirements.txt
```
One additional dependency is [PlexeAPI](https://github.com/michele-segata/plexe-pyapi).

## Usage
To run the standard simulation:
```
python runner2.py --cfg <path_to_the_map_configuration>
```
e.g. `python runner2.py --cfg sim_cfg_3_lanes/config.sumo.cfg`

To run the simulation with platooning:
```
python runner.py --cfg <path_to_the_map_configuration>
```
e.g. `python runner.py --cfg sim_cfg_3_lanes/config.sumo.cfg`

To plot the simulation metrics:
```
python metrics_plot.py <folder_path_to_the_map>
```
e.g. `python metrics_plot.py sim_cfg_3_lanes`

To plot the platoon's behaviour related benchmarks:
```
python platoon_benchmarks_plot.py <path_to_the_platoon_log_file>
```
e.g. python platoon_benchmarks_plot.py platoon_test/benchmarks/log.csv