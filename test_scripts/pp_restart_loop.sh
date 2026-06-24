#!/usr/bin/env bash
set -e

N=15
PP_DIR="$HOME/Documents/tez-projesi/qwen3-asr-swift"
PP_CMD="swift run -c release audio-server --host 0.0.0.0 --port 8081 --mode pp"

for i in $(seq 1 $N); do
  echo "=== [MAC] Trial $i/$N: Starting PP ==="
  screen -dmS pp_server bash -c "cd $PP_DIR && $PP_CMD 2>&1 | tee /tmp/pp_server_$i.log"

  until curl -s -m 3 http://localhost:8081/health 2>/dev/null | grep -q ok; do
    sleep 2
  done
  echo "[MAC] PP healthy at $(date +%H:%M:%S). Windows test başlasın..."

  sleep 45

  echo "[MAC] Killing PP..."
  pkill -f "audio-server.*8081" 2>/dev/null || true
  screen -S pp_server -X quit 2>/dev/null || true
  sleep 3
done

echo "=== [MAC] ALL $N TRIALS DONE ==="
