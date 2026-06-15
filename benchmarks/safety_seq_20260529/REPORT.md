# Safety Checker (#3) and Waypoint / Pick-Place (#4)

Date: 2026-05-29
Machine: Windows + WSL2 Ubuntu 22.04, ROS2 Humble, MoveIt2, UR5e
Simulation: Gazebo Classic (Universal_Robots_ROS2_Gazebo_Simulation, humble branch) + gazebo_ros2_control
Active controller: joint_trajectory_controller (verified)

All numbers and statuses below are measured on this machine. Nothing is estimated.

## #3 voice_safety_checker

New node `voice_safety_checker` validates every parsed motion command BEFORE it can
reach the executor. Topology: `/voice_command/parsed` -> safety_checker ->
`/voice_command/checked`. The executor was launched with a remap
(`-r /voice_command/parsed:=/voice_command/checked`), so a rejected command never reaches
it (no executor source change). safety.* and query.* intents pass through unchanged.

Checks enforced:
- Joint limits: each named/explicit joint target within [-2pi, 2pi] per joint (UR5e range).
- Workspace reach: end-effector pose radius within [0.18, 0.85] m and z >= 0.0.
- Forbidden zone: axis-aligned no-go box x[0.20,0.50] y[-0.50,-0.30] z[0.00,0.50]; target inside is rejected.
- Velocity/acceleration: any requested scaling > 0.1 is rejected (executor uses 0.1).

Test: 7 commands published to `/voice_command/parsed`. Result (see `safety_checker_test.txt`):

| case | command | verdict |
|---|---|---|
| 1 | motion.go_home | Accepted |
| 2 | motion.move_to target=b | Accepted |
| 3 | target_joints [...,7.0] | Rejected: wrist_3_joint 7.0 outside [-6.2832, 6.2832] |
| 4 | target_pose [1.5,0,0] | Rejected: reach 1.5 exceeds MAX_REACH 0.85 |
| 5 | target_pose [0.35,-0.4,0.25] | Rejected: inside forbidden zone |
| 6 | move_to a, velocity_scaling 0.5 | Rejected: velocity_scaling 0.5 exceeds max 0.1 |
| 7 | move_to target=zzz | Rejected: unknown named target 'zzz' |

Gate verified end to end: exactly the 2 accepted commands were forwarded to
`/voice_command/checked`, and the executor log shows it received only those 2 intents.
The 5 rejected commands never reached the executor.

## #4 voice_sequence_executor

New node `voice_sequence_executor` (own MoveGroup action client, sequential execution via a
worker thread). Subscribes `/voice_command/parsed`. Handles `motion.waypoint`
(sequence of named targets) and `motion.pick_place`.

### Waypoint: home -> a -> ready

3/3 waypoints reported SUCCEEDED in order (see `sequence_test.txt`):
- home: SUCCEEDED
- a: SUCCEEDED (~11.7 s, 0.1 vel scaling)
- ready: SUCCEEDED (~10.8 s)
- "Waypoint sequence complete"
Final joint state matched `ready` = [0, -1.047, 1.047, -1.571, -1.571, 0]. Robot moved.

### Pick-place (simulated grasp)

No gripper exists in this UR5e Gazebo model, so grasp/release are simulated and explicitly
marked as such in the logs. Flow: move to pick -> "Simulated grasp" + hold -> move to place
-> "Simulated release".

pick='a' place='ready' (joint targets): full flow SUCCEEDED.
- Move to pick 'a': SUCCEEDED
- "Simulated grasp (no gripper in sim)" ... "Simulated grasp complete (object attached: simulated)"
- Move to place 'ready': SUCCEEDED
- "Simulated release (no gripper in sim)"
- "Pick-place complete (simulated grasp)"
Final joint state matched `ready`. Robot moved through both poses.

### Honest deviation: pose-target pick-place is unreliable in this sim

The first pick_place attempt used the Cartesian pose targets b=(0.4,-0.2,0.4) and
c=(0.3,0.0,0.6) with loose orientation tolerance. MoveIt planned a solution, but the
joint_trajectory_controller aborted execution mid-trajectory with a state/path tolerance
violation (`State tolerances failed for joint 3: Position Error 0.211859 > 0.200000`,
`PATH_TOLERANCE_VIOLATED`), so the MoveGroup result was CONTROL_FAILED (error_code -4) and
the arm stopped in an off-trajectory configuration. From that unstable configuration the arm
kept drifting, so subsequent MoveGroup goals failed `allowed_start_tolerance` validation
("start point deviates from current robot state more than 0.01"). Recovery required sending a
direct FollowJointTrajectory home command to the controller (bypassing MoveGroup), which
re-stabilized the arm (error_code 0). After recovery the joint-target pick-place succeeded.

Conclusion: in this Gazebo Classic + gazebo_ros2_control setup, loosely-constrained Cartesian
pose goals can produce trajectories the controller cannot track within its tolerances.
Joint-named targets are reliable. The node default pick/place targets were therefore set to
joint-named targets (pick='a', place='ready'). Explicit pose/joint targets remain supported
via parameters.

## Files
- `safety_checker_test.txt` — #3 verdicts, forwarded /checked messages, executor gate evidence
- `sequence_test.txt` — #4 waypoint + pick-place logs and the pose-target failure cause
