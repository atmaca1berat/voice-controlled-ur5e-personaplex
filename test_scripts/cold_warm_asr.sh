#!/usr/bin/env bash
# EXP-2a: Cold vs warm ASR test
# ASR sunucusu ÇALIŞIR durumda, PersonaPlex restart YOK
# Aynı go_home.wav'i arka arkaya 6 kez gönder

set -e

PUB="python3 $HOME/test_audio/publish_audio.py"
AUDIO="$HOME/test_audio/go_home.wav"

echo "=== EXP-2a: Cold vs Warm ASR (6 calls, no restart) ==="

for i in $(seq 1 6); do
  T0=$(date +%s.%N)
  echo "--- Call $i at $T0 ---"
  $PUB $AUDIO
  sleep 8
done

echo "=== Done. Check bridge logs for ASR timing ==="
tail -60 ~/test_logs/bridge_*.log | grep -E "POST ASR|Published /voice_command/text"
