#!/bin/bash
# TEK trial barge-in (PP aktif) - danismanin protokolu BIREBIR:
# go_home -> move_to a -> move_to_position_a.wav yayinla -> ~3 SN SONRA stop.wav (ikisi de BRIDGE).
# barge_measure.py KULLANMAZ. Loglar kalici stack tarafindan yaziliyor.
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
LOG=~/test_logs/ppactive
PUB="python3 /home/onay/test_audio/publish_audio.py"
AUD=/home/onay/test_audio

echo "===== TRIAL START $(date +%H:%M:%S) ====="
echo "[go_home] $(date +%H:%M:%S)"
ros2 topic pub --once /voice_command/parsed std_msgs/msg/String '{"data": "{\"intent\": \"motion.go_home\", \"params\": {}}"}'
sleep 15

echo "[move_to a yayin] $(date +%H:%M:%S)"
$PUB "$AUD/move_to_position_a.wav" 2>&1 | tee -a "$LOG/runlog.txt"
sleep 3

echo "[stop yayin] $(date +%H:%M:%S)"
$PUB "$AUD/stop.wav" 2>&1 | tee -a "$LOG/runlog.txt"
sleep 35

echo "===== TRIAL DONE $(date +%H:%M:%S) ====="
