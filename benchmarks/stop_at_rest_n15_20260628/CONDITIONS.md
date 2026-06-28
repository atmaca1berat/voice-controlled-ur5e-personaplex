# Stop-at-Rest Recognition & Dispatch — n=15

**Date:** 2026-06-28
**Purpose:** Verify that the full voice pipeline (ASR → NLU → executor) correctly recognises a spoken "stop" command and reaches the cancellation handler when the robot is stationary (no active goal).

## Setup

| Component | Detail |
|-----------|--------|
| Mac host | ASR only (port 8080), PP off, TTS off |
| Windows host | Gazebo + MoveIt2 + bridge + executor + safety checker |
| Robot state | Canonical home position, no active goal (current_goal_handle=None) |
| Audio | Pre-recorded stop.wav, 15 trials, 7 s inter-trial interval |
| Bridge mode | CASCADE_TTS=False (default), only ASR path exercised |

## Results

| Metric | Value |
|--------|-------|
| ASR transcript | "Stop." (15/15) |
| NLU intent | safety.stop (15/15) |
| Priority | 1 (highest) |
| Reached cancel handler | yes (15/15) |
| No active goal logged | yes (15/15) |
| Overall status | success 15/15 |

## Files

- `stop_at_rest_n15.csv` — per-trial results
- `sar_bridge.log` — bridge node log (ASR + NLU output)
- `sar_executor.log` — executor log (cancel handler path)
- `sar_safety.log` — safety checker log
- `sar_run.log` — test harness log
