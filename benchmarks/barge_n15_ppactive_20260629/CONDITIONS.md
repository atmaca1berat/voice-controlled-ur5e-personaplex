# Barge-in Cancellation — PP-Active, n=15

**Date:** 2026-06-29
**Purpose:** Re-run of the voice barge-in measurement with PersonaPlex verified up. The earlier run (`benchmarks/barge_n15_20260627/`) was taken with PP unreachable (30/30 "Cannot connect to host ...8081", 0 agent transcripts), so its barge-in latency reflected an isolated-ASR condition and was invalid. This run was performed with PP genuinely resident on port 8081.

## Host Configuration

| Host | Role |
|------|------|
| Mac M2 Pro 16 GB | ASR (8080) + PersonaPlex (8081), PP IP 192.168.1.103 |
| Windows 11 + WSL2 (Ubuntu 22.04) | ROS 2 Humble, MoveIt2, Gazebo, bridge, executor, safety checker |

## Protocol

- `bridge_node.py` with `CASCADE_TTS=False` (PP 8081 path active; colcon-rebuilt).
- Velocity scaling 0.1 (~11 s trajectory), consistent with the rest of the article.
- ROS stack brought up once (Gazebo + MoveIt2 + UR5e, safety, executor, bridge); no stack restart between trials.
- **Per-trial cold PP restart** on the Mac before each trial (no warmup, no persistent PP, no signal listener).
- Each trial: go_home → move_to a (move_to_position_a.wav) → ~3 s after motion start, stop.wav.
- Both commands published through the bridge (publish_audio → bridge → ASR + PP → NLU → executor). `barge_measure.py` was NOT used (full speech path).

## Validity Criterion

A trial counts as valid only if all three hold:
- a) err8081 = 0 (no "Cannot connect to host ...8081" in bridge log)
- b) status = CANCELED
- c) pp_cancelled = yes

Invalid causes: degenerate (robot caught before motion started, travel = 0, move_exec < 0.5 s), stop ASR timeout, SUCCEEDED, err8081.

## Results

23 attempts → **15 valid**. Excluded 8: attempts 3, 5, 6, 9, 10, 12, 16 = degenerate (7) + attempt 8 = superseded (1, re-run at user request because travel = 0).

Across all 23 attempts: **23/23 CANCELED, err8081 = 0, pp_cancelled = yes (23/23).**

n=15 valid (mid-trajectory) trials:

| Metric | Mean ± SD |
|--------|-----------|
| stop_to_halt_s | 0.730 ± 0.343 |
| travel_after_stop_rad | 0.219 ± 0.119 |
| asr_s | 0.118 ± 0.137 |

15/15 CANCELED, pp_cancelled = yes, err8081 = 0, no stop ASR timeout.

## PP-Active Evidence (three acceptance criteria)

1. **err8081 = 0** — no "Cannot connect to host ...8081" anywhere in the bridge log (unlike the 20260627 run).
2. **PP task cancelled per trial** — bridge log shows "Previous PP task cancelled (new audio arrived)" and "PP cancelled: safety intent detected", confirming the move command's PP task was genuinely active when stop arrived.
3. **Move-stage ASR contention** — during move dispatch the co-resident PP competes with ASR for the MLX allocator (the ~4 s contention seen in go_home n=15).

### Note on asr_s

The expectation was that the stop's asr_s would be in the seconds range (ASR-PP contention). On this hardware ASR stayed fast (~0.1 s) for the stop transcription. Per the protocol this is NOT a validity criterion; asr_s is recorded as the measured value (not fabricated).

## Files

- `tum_23_deneme.csv` — all 23 attempts with valid/reason + all metrics
- `gecerli_15.csv` — the 15 valid trials, renumbered
- `SONUC_OZETI.txt` — full Turkish summary
- `bridge.log`, `executor.log`, `safety.log`, `gazebo.log`, `runlog.txt` — full-run logs
- `bridge_gecerli15.log`, `executor_gecerli15.log` — valid-15 subset logs
- `scripts/` — bridge_node.py (CASCADE_TTS=False) + bringup, trial, guard, analyze, make_valid15

Raw joint_states (~150 MB, used for travel/FK) is kept in WSL at `/home/onay/test_logs/ppactive/joint.csv` and is not committed to avoid bloating the repository.
