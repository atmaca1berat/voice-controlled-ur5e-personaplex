#!/bin/bash
# Barge-in n=15 PP-AKTIF stack bringup (kalici - trial'lar arasi ayakta kalir).
# Otomatik restart/sinyal YOK. PP (8081) surekli acik varsayilir.
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
LOG=~/test_logs/ppactive
mkdir -p "$LOG"

# temiz baslat
pkill -9 -f gzserver 2>/dev/null
pkill -9 -f gzclient 2>/dev/null
pkill -9 -f gazebo 2>/dev/null
pkill -9 -f voice_safety_checker_node 2>/dev/null
pkill -9 -f voice_task_executor_node 2>/dev/null
pkill -9 -f 'bridge_no[d]e' 2>/dev/null
pkill -9 -f 'topic echo /joint_states' 2>/dev/null
sleep 4
rm -f "$LOG/ready" "$LOG/gazebo.log" "$LOG/safety.log" "$LOG/executor.log" "$LOG/bridge.log" "$LOG/joint.csv" "$LOG/runlog.txt"

# 1) gazebo + moveit + ur5e
setsid bash -c 'source /opt/ros/humble/setup.bash; source ~/ros2_ws/install/setup.bash; ros2 launch ur_simulation_gazebo ur_sim_moveit.launch.py ur_type:=ur5e' > "$LOG/gazebo.log" 2>&1 < /dev/null &
echo "GAZEBO_LAUNCHED, waiting 60s..."
sleep 60

# 2) safety checker
setsid bash -c 'source /opt/ros/humble/setup.bash; source ~/ros2_ws/install/setup.bash; ros2 run voice_task_executor voice_safety_checker_node' > "$LOG/safety.log" 2>&1 < /dev/null &
# 3) executor (remap SART)
setsid bash -c 'source /opt/ros/humble/setup.bash; source ~/ros2_ws/install/setup.bash; ros2 run voice_task_executor voice_task_executor_node -r /voice_command/parsed:=/voice_command/checked' > "$LOG/executor.log" 2>&1 < /dev/null &
# 4) bridge (CASCADE_TTS=False -> PP 8081 yolu)
setsid bash -c 'source /opt/ros/humble/setup.bash; source ~/ros2_ws/install/setup.bash; ros2 run personaplex_bridge bridge_node' > "$LOG/bridge.log" 2>&1 < /dev/null &
# 5) joint_states kaydedici (travel/halt icin)
setsid bash -c 'source /opt/ros/humble/setup.bash; source ~/ros2_ws/install/setup.bash; ros2 topic echo /joint_states --csv' > "$LOG/joint.csv" 2>&1 < /dev/null &

# bridge hazir bekle
for i in $(seq 1 90); do
  grep -q 'HTTP session ready' "$LOG/bridge.log" 2>/dev/null && break
  sleep 2
done

if grep -q 'HTTP session ready' "$LOG/bridge.log" 2>/dev/null; then
  touch "$LOG/ready"
  echo "STACK_READY $(date +%H:%M:%S)"
else
  echo "STACK_NOT_READY (bridge HTTP session ready gorunmedi)"
fi

# distro'yu canli tut (trial'lar arasi)
tail -f /dev/null
