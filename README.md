# SDN QoS Priority Controller

A Software-Defined Networking (SDN) project that implements **Quality of Service (QoS)** using priority-based OpenFlow flow rules via a Ryu controller. Traffic from high-priority hosts gets preferential treatment over low-priority hosts at the data plane level.

---

## Table of Contents
- [Overview](#overview)
- [Tools & Technologies](#tools--technologies)
- [Network Topology](#network-topology)
- [How It Works](#how-it-works)
- [Setup & Execution](#setup--execution)
- [Results](#results)
- [Project Structure](#project-structure)

---

## Overview

This project demonstrates how an SDN controller can enforce QoS policies without requiring any hardware-level configuration. The Ryu controller intercepts packets, classifies traffic based on source IP, and installs OpenFlow 1.3 flow rules with different priority values into the OVS switch — giving `h1` (high-priority) significantly more bandwidth than `h2` (low-priority) when both communicate with the same server `h3`.

---

## Tools & Technologies

| Tool | Purpose |
|------|---------|
| **Ryu** | SDN Controller (Python-based) |
| **Mininet** | Network emulation |
| **Open vSwitch (OVS)** | Software switch |
| **OpenFlow 1.3** | Flow rule protocol |
| **iperf** | Bandwidth testing |

---

## Network Topology

```
  h1 (10.0.0.1) ─────┐
                      │
  h2 (10.0.0.2) ─── [s1] ──── h3 (10.0.0.3)  [Server]
                      │
              [Ryu Controller]
               (remote, port 6653)
```

| Host | IP | Role | Priority |
|------|----|------|----------|
| h1 | 10.0.0.1 | High-priority client | 100 |
| h2 | 10.0.0.2 | Low-priority client | 10 |
| h3 | 10.0.0.3 | iperf server | — |

---

## How It Works

1. **Switch connects** → Controller installs a table-miss rule (priority 0) that sends all unknown packets to the controller.
2. **Packet arrives** → `packet_in_handler` inspects the IP source.
3. **Classification:**
   - `src = 10.0.0.1` → priority **100** (HIGH)
   - anything else → priority **10** (LOW)
4. **Flow rule installed** → Match on `(in_port, eth_type, ipv4_src, ipv4_dst, eth_dst)` with the assigned priority.
5. **Subsequent packets** → Handled directly by the switch without hitting the controller.

---

## Setup & Execution

### Prerequisites
```bash
pip install ryu mininet
# iperf must be installed on the system
```

### Step 1 — Start the Ryu Controller
```bash
ryu-manager qos_controller.py
```

### Step 2 — Launch Mininet Topology
```bash
sudo mn --topo single,3 --controller remote --switch ovsk
```

### Step 3 — Test Connectivity
```
mininet> pingall
```

### Step 4 — Run iperf Bandwidth Test
```
mininet> h3 /usr/bin/iperf -s &
mininet> h1 /usr/bin/iperf -c 10.0.0.3
mininet> h2 /usr/bin/iperf -c 10.0.0.3
```

### Step 5 — Inspect Flow Table
```bash
sudo ovs-ofctl dump-flows s1
```

---

## Results

### 1. Ryu Controller — QoS Decisions
The controller logs each flow classification in real time, identifying HIGH vs LOW priority traffic and the assigned output port.

![Ryu Controller QoS Decisions](screenshots/01_ryu_controller_qos_decisions.png)

---

### 2. Mininet — First pingall (Flow Learning Phase)
On the first `pingall`, some packets are dropped as the controller is still learning MAC addresses and installing flow rules (66% drop rate is expected during the ARP/learning phase).

![First pingall - flow learning](screenshots/02_mininet_first_pingall.png)

---

### 3. Mininet — Successful pingall (0% packet loss)
After flow rules are installed, full connectivity is confirmed with **0% packet loss** across all 6 host pairs.

![Successful pingall](screenshots/03_mininet_successful_pingall.png)

---

### 4. iperf Bandwidth Results
Bandwidth test confirms QoS differentiation:

| Host | Bandwidth |
|------|-----------|
| **h1** (priority 100) | **21.7 Gbits/sec** |
| **h2** (priority 10) | **12.4 Gbits/sec** |

h1 achieves ~75% higher throughput than h2, demonstrating effective priority enforcement.

![iperf bandwidth results](screenshots/04_iperf_bandwidth_results.png)

---

### 5. OVS Flow Table
The installed flow rules confirm correct priority assignment and packet forwarding actions per flow.

![OVS flow table dump](screenshots/05_ovs_flow_table.png)

**Key flows observed:**
- `priority=100, nw_src=10.0.0.1 → output:s1-eth3` — h1→h3 (HIGH)
- `priority=10, nw_src=10.0.0.2 → output:s1-eth3` — h2→h3 (LOW)
- `priority=0 → CONTROLLER` — table-miss fallback

---

## Project Structure

```
sdn-qos-project/
├── qos_controller.py      # Ryu SDN controller with QoS logic
├── requirements.txt       # Python dependencies
├── run_commands.txt       # Quick reference for all commands
├── outputs/
│   └── flow_table.txt     # Captured OVS flow table output
├── screenshots/           # Terminal output screenshots
└── README.md
```

---

## Key Observations

- Priority-based flow rules are enforced entirely at the **data plane** (OVS switch), with no per-packet controller involvement after the first packet.
- The controller acts as a **reactive** learning switch enhanced with QoS classification — scalable and easy to extend.
- ARP packets are always flooded (not subject to QoS) since they don't carry IP headers.
- Flow rules persist for the session and can be inspected live via `ovs-ofctl dump-flows s1`.
