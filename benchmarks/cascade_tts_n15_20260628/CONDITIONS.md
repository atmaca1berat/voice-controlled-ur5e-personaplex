# Cascade-TTS Baseline — n=15

Date: 2026-06-28
Host: Mac M2 Pro 16GB (ASR:8080 + TTS:8082, PP off) + Windows WSL2

## Protocol
Bridge runs in CASCADE_TTS=True mode. Audio -> ASR (blocking,
transcript+NLU) -> Piper TTS /synthesize (fire-and-forget) ->
agent_text + /audio/to_unity. PP server is OFF.
Each trial: go_home audio command, 14 s interval. n = 15.

TTS engine: Piper (en_US-lessac-medium, ONNX, CPU).

## Results
15/15 SUCCEEDED.
Mean V2M: 1.104 +/- 0.268 s.
Mean ASR: 0.247 +/- 0.057 s (warm, PP not co-resident).
Mean TTS synth: 49.68 +/- 2.67 ms.
Mean confirmation latency: 0.948 +/- 0.277 s.

Note: V2M is lower than full-duplex (4.83 s) because PP is off
and ASR runs in isolation (~0.2 s vs 3.94 s with PP co-resident).
The difference is from MLX allocator contention, not architecture.

## Files
- cascade_tts_n15.csv — per-trial results
- bridge_cascade_n15.log — bridge log
- executor_cascade_n15.log — executor log
