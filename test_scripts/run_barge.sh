#!/usr/bin/env bash
set -e

MAC_IP="172.21.61.203"
PP_URL="http://${MAC_IP}:8081/health"
PUB="python3 /home/berat/test_audio/publish_audio.py"
AUDIO_DIR="/home/berat/test_audio"

pause_for_pp() {
  local cycle_name="$1"
  read -r

  HEALTH=$(curl -s -m 3 "$PP_URL" 2>/dev/null || echo "FAIL")

  if [[ "$HEALTH" != *"ok"* ]]; then
    read -r
  fi

  sleep 3
}

for i in 1 2 3 4 5; do
  pause_for_pp "BARGE-$i"

  T_MOVE=$(date +%s.%N)
  $PUB $AUDIO_DIR/move_to_position_a.wav

  sleep 2

  T_STOP=$(date +%s.%N)
  $PUB $AUDIO_DIR/stop.wav

  sleep 35

  tail -15 ~/test_logs/executor_barge_*.log
done
