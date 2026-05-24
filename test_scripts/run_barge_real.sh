#!/usr/bin/env bash

source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

EXEC_LOG=$(ls -t ~/test_logs/executor_slow_*.log 2>/dev/null | head -1)

section() {
  echo ""
  echo "════════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════════"
}

publish_home() {
  ros2 topic pub --once /voice_command/parsed std_msgs/msg/String \
    '{data: "{\"intent\": \"motion.go_home\", \"parameters\": {}, \"priority\": 3, \"confidence\": 1.0, \"raw_transcript\": \"go home\"}"}'
}

publish_move_a() {
  ros2 topic pub --once /voice_command/parsed std_msgs/msg/String \
    '{data: "{\"intent\": \"motion.move_to\", \"parameters\": {\"target\": \"a\"}, \"priority\": 3, \"confidence\": 1.0, \"raw_transcript\": \"move to position a\"}"}'
}

publish_stop() {
  ros2 topic pub --once /voice_command/parsed std_msgs/msg/String \
    '{data: "{\"intent\": \"safety.stop\", \"parameters\": {}, \"priority\": 1, \"confidence\": 1.0, \"raw_transcript\": \"stop\"}"}'
}

for i in 1 2 3 4 5; do
  section "BARGE-IN CYCLE $i / 5"

  publish_home
  sleep 15

  T_MOVE=$(date +%s.%N)
  publish_move_a

  sleep 3

  T_STOP=$(date +%s.%N)
  publish_stop

  sleep 10

  tail -12 "$EXEC_LOG"
done

section "N=5 BARGE-IN COMPLETED"

tail -80 "$EXEC_LOG"
