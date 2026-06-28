# ASR Diagnosis — Cold/Warm Latency

Date: 2026-06-24
Host: Mac M2 Pro 16GB (ASR+PP) + Windows WSL2 (ROS 2/Gazebo/MoveIt2)

## Protocol
Three bridge log sessions capturing ASR latency under different
PP co-residency conditions. Used to diagnose why ASR latency in
dual-server mode (3.94 s) was far higher than isolated ASR (0.22 s).

## Finding
PP process sharing the MLX allocator causes ASR latency inflation.
Isolated ASR: 0.22 +/- 0.03 s. With PP co-resident: 3.94 +/- 0.68 s.

## Files
- bridge_revision_20260624_114337.log — session 1 (cold start)
- bridge_revision_20260624_122017.log — session 2 (warm)
- bridge_revision_20260624_140439.log — session 3 (warm, extended)
- executor_revision_20260624_115045.log — executor log
- safety_checker_20260624_115043.log — safety checker log
