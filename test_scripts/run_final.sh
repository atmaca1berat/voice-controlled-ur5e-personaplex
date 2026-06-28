#!/usr/bin/env bash
set -e

MAC_IP="192.168.1.102"
PP_URL="http://${MAC_IP}:8081/health"
PUB="python3 $HOME/test_audio/publish_audio.py"
AUDIO_DIR="$HOME/test_audio"

pause_for_pp() {
  local cycle_name="$1"
  read -r

  HEALTH=$(curl -s -m 3 "$PP_URL" 2>/dev/null || echo "FAIL")

  if [[ "$HEALTH" != *"ok"* ]]; then
    read -r
    HEALTH=$(curl -s -m 3 "$PP_URL" 2>/dev/null || echo "FAIL")
    if [[ "$HEALTH" != *"ok"* ]]; then
      exit 1
    fi
  fi

  sleep 3
}

section() {
  echo ""
  echo "════════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════════"
}

section "TEST 1: N=15 STOP - 25s interval"

for i in $(seq 1 15); do
  pause_for_pp "STOP-$i"

  $PUB $AUDIO_DIR/move_to_position_a.wav

  sleep 25

  $PUB $AUDIO_DIR/stop.wav

  sleep 30

  tail -10 ~/test_logs/bridge_n5_cycles_*.log
done

section "TEST 2: QUERY PIPELINE (n=1)"

pause_for_pp "QUERY"

$PUB $AUDIO_DIR/where_are_you.wav

sleep 30

tail -10 ~/test_logs/bridge_n5_cycles_*.log

section "TEST 3: N=15 BARGE-IN - 2s interval (robot in motion)"

for i in $(seq 1 15); do
  pause_for_pp "BARGE-$i"

  T_MOVE=$(date +%s.%N)
  $PUB $AUDIO_DIR/move_to_position_a.wav

  sleep 2

  T_STOP=$(date +%s.%N)
  $PUB $AUDIO_DIR/stop.wav

  sleep 40

  tail -10 ~/test_logs/bridge_n5_cycles_*.log
  tail -10 ~/test_logs/executor_n5_cycles_*.log
done

section "ALL TESTS COMPLETED"
