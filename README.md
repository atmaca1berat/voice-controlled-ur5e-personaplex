# Voice-Controlled UR5e via NVIDIA PersonaPlex

Real-time full-duplex voice control of a simulated UR5e industrial manipulator, integrating NVIDIA PersonaPlex (MLX 4-bit on Apple Silicon), Qwen3-ASR, ROS 2 Humble, MoveIt2, Gazebo, and Unity 2022.3.

Detailed README under construction.

Author: Berat Atmaca (2019556012), Cukurova University, Department of Computer Engineering.
Supervisor: Ogr. Gor. Dr. Yunus Emre Cogurcu.

## Note on velocity scaling

`voice_task_executor_node.py` is configured with `max_velocity_scaling_factor=0.1` (10%) to provide a sufficiently long motion window for barge-in cancellation measurements. This is a deliberate experimental setting documented in Section 4 of the thesis, not a performance limitation. For demonstrations without cancellation timing measurements, this value can safely be raised.
