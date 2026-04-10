# SDN QoS Priority Controller

## Objective
To implement QoS using SDN controller with priority-based flow rules.

## Tools Used
- Mininet
- Ryu Controller
- OpenFlow 1.3

## Topology
Single switch with 3 hosts:
- h1 → High Priority
- h2 → Low Priority
- h3 → Server

## Execution Steps
1. Start controller:
   ryu-manager qos_controller.py

2. Start Mininet:
   sudo mn --topo single,3 --controller remote --switch ovsk

3. Test connectivity:
   pingall

4. Test performance:
   h3 iperf -s &
   h1 iperf -c 10.0.0.3
   h2 iperf -c 10.0.0.3

## QoS Logic
- h1 traffic assigned priority 100
- h2 traffic assigned priority 10

## Results
- Successful connectivity (0% packet loss)
- Flow rules installed with different priorities
- QoS behavior observed

## Screenshots
Refer to screenshots folder

