#!/usr/bin/env bash
set -e

MAC_IP="192.168.1.102"
PP_URL="http://${MAC_IP}:8081/health"
ASR_URL="http://${MAC_IP}:8080/health"
N=15

echo "=== EXP-1 dual-server n=$N (PP restart per trial) ==="

for i in $(seq 1 $N); do
  echo "--- Trial $i/$N: waiting for both servers ---"
  until curl -s -m 3 "$PP_URL" 2>/dev/null | grep -q ok; do
    sleep 2
  done
  until curl -s -m 3 "$ASR_URL" 2>/dev/null | grep -q ok; do
    sleep 2
  done
  echo "Both servers healthy."
  sleep 3
  echo "Sending test audio at $(date +%H:%M:%S)..."
  python3 ~/test_audio/publish_audio.py ~/test_audio/go_home.wav
  sleep 60
  echo "--- Trial $i/$N DONE. Waiting for PP restart ---"
  while curl -s -m 2 "$PP_URL" 2>/dev/null | grep -q ok; do
    sleep 2
  done
  echo "PP down, waiting for it to come back..."
done

echo "=== ALL $N TRIALS DONE ==="
