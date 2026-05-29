# Barge-In Cancellation Fix and Honest Measurement

Date: 2026-05-29
Machine: Windows + WSL2 Ubuntu 22.04, ROS2 Humble, MoveIt2, UR5e
Simulation: Gazebo Classic (built from source: Universal_Robots_ROS2_Gazebo_Simulation, humble branch) + gazebo_ros2_control

## Summary

The original `voice_task_executor_node.py` cancelled only the MoveGroup (`/move_action`)
goal on "stop". By the time that cancel was processed, MoveGroup had already handed the
trajectory to the controller, so nothing was preempted: the controller goal finished
SUCCEEDED and the robot completed its motion. The fix additionally sends a CancelGoal
request to the trajectory controller's cancel service, which preempts the active
trajectory: controller goal status becomes CANCELED and the robot stops mid-motion.

All numbers below are measured on this machine. No values are estimated.

## Environment / setup deviations (honest)

1. No Gazebo Classic binary for UR on Humble. There is no `ros-humble-ur-simulation-gazebo`
   package; apt only ships `ros-humble-ur-simulation-gz` (modern Gazebo Sim). Gazebo Classic
   for UR5e was built from source from `Universal_Robots_ROS2_Gazebo_Simulation` (humble
   branch) against the apt `gazebo_ros2_control` (Classic) package. Gazebo ran headless
   (gzserver, no GUI) on WSL2.

2. Controller name differs from the thesis. `ros2 control list_controllers` shows the only
   active trajectory controller in this Gazebo Classic sim is `joint_trajectory_controller`,
   NOT `scaled_joint_trajectory_controller` (the scaled controller is for the real UR driver
   and is not active here). The cancel action used is therefore:
   `/joint_trajectory_controller/follow_joint_trajectory`. The executor constant is named
   `TRAJECTORY_CONTROLLER_ACTION` and points to that verified action. See
   `ros2_action_list.txt`.

3. `/joint_states` velocity field is unreliable under gazebo_ros2_control here (reports ~0
   even while joint positions clearly change). Motion and stop are therefore measured from
   joint POSITION change over time (finite-difference speed), not the reported velocity.
   Position-based motion was verified directly: shoulder_pan_joint travels 0 -> 3.144 rad in
   ~10.65 s for the "a" move (matches the thesis ~11 s).

## Method (identical for baseline and fixed)

- Joints, home, target "a", and vel/accel scaling 0.1 are exactly the thesis Section 4.5 values.
- `barge_measure.py` drives the real executor over `/voice_command/parsed`:
  go_home -> wait -> move_to "a" -> wait until moving + ~3 s -> publish safety.stop.
- Measured per trial: controller final goal status (from
  `/joint_trajectory_controller/follow_joint_trajectory/_action/status`), cancel-to-stop
  latency (stop command -> last detected motion), and travel_after_stop (joint-space
  distance the arm moved after the stop command).
- n = 5 trials each, same running sim. Only the executor code changed between runs.

## Mechanism proof: cancel_test.py

Sends a trajectory directly to the controller and cancels it mid-motion.
See `cancel_test_output.txt`:

```
goal accepted, executing
>>> CANCEL (robot moving) <<<
cancel response: goals_canceling=1
FINAL STATUS = CANCELED (5)
REAL PREEMPTION
```

Result: the controller honours cancellation at the control layer (goals_canceling=1,
status CANCELED). This proves the mechanism the fix relies on.

## Baseline (original code) — bug reproduced, n=5

| trial | controller status | travel_after_stop (rad) | "latency" (s) | max_speed (rad/s) |
|------:|:------------------:|------------------------:|--------------:|------------------:|
| 1 | SUCCEEDED | 2.9474 | 7.584 | 0.418 |
| 2 | SUCCEEDED | 2.9435 | 7.578 | 0.419 |
| 3 | SUCCEEDED | 2.1410 | 3.486 | 1.309 |
| 4 | SUCCEEDED | 2.9555 | 7.607 | 0.420 |
| 5 | SUCCEEDED | 2.9505 | 7.591 | 0.415 |

- Controller status: 5/5 SUCCEEDED. The robot did NOT stop on command; it completed the
  motion (travel_after_stop ~2.1-3.0 rad after "stop").
- The reported "latency" here is NOT a stop time — it is the time until the trajectory
  finished naturally. Mean 6.77 s (sd 1.64).
- Trial 3 is an honest outlier: MoveIt planned a faster trajectory that run (max_speed
  1.31 vs ~0.42), so it finished sooner; status was still SUCCEEDED.

Executor log on each stop (see `executor_baseline_cancel_lines.txt`):
`Cancelling current goal` -> `Goal not active or already finished` (MoveGroup
goals_canceling = 0) -> `Goal completed successfully`. This confirms the thesis finding:
the MoveGroup-level cancel reports goals_canceling=0 and the motion completes.

## Fixed (controller-level cancel) — n=5

| trial | controller status | travel_after_stop (rad) | cancel-to-stop latency (s) | goals_canceling |
|------:|:------------------:|------------------------:|---------------------------:|:---------------:|
| 1 | CANCELED | 0.000 | 0.119 | 1 |
| 2 | CANCELED | 0.000 | 0.110 | 1 |
| 3 | CANCELED | 0.000 | 0.110 | 1 |
| 4 | CANCELED | 0.000 | 0.119 | 1 |
| 5 | CANCELED | 0.000 | 0.119 | 1 |

- Controller status: 5/5 CANCELED. The robot stopped essentially in place
  (travel_after_stop = 0.000 rad).
- Cancel-to-stop latency: mean 0.115 s, sd 0.004 s, min 0.110 s, max 0.119 s.
- Executor log on each stop (see `executor_fixed_cancel_lines.txt`):
  `Cancelling current MoveGroup goal` -> `Trajectory controller goal preempted: 1`
  (controller goals_canceling = 1) -> `MoveGroup goal not active or already finished`.
  The MoveGroup cancel alone is still a no-op; the trajectory-controller cancel is what
  stops the robot.

## Baseline vs fixed

| metric | baseline (n=5) | fixed (n=5) |
|---|---|---|
| controller final status | 5/5 SUCCEEDED | 5/5 CANCELED |
| robot stops on "stop" | no (completes) | yes (mid-motion) |
| travel after stop (mean) | 2.788 rad | 0.000 rad |
| controller goals_canceling | 0 | 1 |
| cancel-to-stop latency (mean) | n/a (no stop; 6.77 s to natural finish) | 0.115 s |

## Files

- `baseline_n5.csv`, `fixed_n5.csv` — raw per-trial data
- `cancel_test_output.txt` — mechanism proof
- `executor_baseline_cancel_lines.txt`, `executor_fixed_cancel_lines.txt` — executor log evidence
- `ros2_action_list.txt` — action/controller name verification
