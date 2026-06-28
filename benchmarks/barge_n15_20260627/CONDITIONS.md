# Barge-in n=15 — Non-blocking Bridge

Date: 2026-06-27
Host: Mac M2 Pro 16GB (ASR:8080 + PP:8081) + Windows WSL2 (ROS 2/Gazebo/MoveIt2)

## Protocol
Dual-server mode. Bridge uses non-blocking PP dispatch (create_task)
so ASR processes stop commands without waiting for PP (~12 s).
Each trial: go_home -> move_to a (velocity 0.1, ~11 s trajectory)
-> 3 s delay -> stop audio. PP restarted between trials via signal.
n = 15 trials.

## Results
14/15 CANCELED, 1/15 SUCCEEDED (trial 6: move completed 0.69 s
before stop audio was published).
Mean stop_to_halt: 0.767 +/- 0.384 s (CANCELED trials only).
Mean travel_after_stop: 0.224 +/- 0.120 rad.

## Files
- barge_v2_n15.csv — per-trial results
- bridge_bargev2_20260627_163647.log — bridge log
- executor_bargev2_20260627_163647.log — executor log
