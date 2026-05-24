#!/usr/bin/env bash
set -e

MAC_IP="172.21.61.203"
PP_URL="http://${MAC_IP}:8081/health"
ASR_URL="http://${MAC_IP}:8080/health"

N=5

for cycle in $(seq 1 $N); do
  read -r

  HEALTH=$(curl -s -m 3 "$PP_URL" 2>/dev/null || echo "FAIL")

  if [[ "$HEALTH" != *"ok"* ]]; then
    read -r
    HEALTH=$(curl -s -m 3 "$PP_URL" 2>/dev/null || echo "FAIL")
    if [[ "$HEALTH" != *"ok"* ]]; then
      exit 1
    fi
  fi

  ASR_HEALTH=$(curl -s -m 3 "$ASR_URL" 2>/dev/null || echo "FAIL")

  sleep 3

  TS=$(date +%s.%N)
  python3 ~/test_audio/publish_audio.py ~/test_audio/go_home.wav

  sleep 45

  tail -10 ~/test_logs/bridge_n5_cycles_*.log
done

ls -la ~/test_logs/bridge_n5_cycles_*.log
ls -la ~/test_logs/executor_n5_cycles_*.log
