# Isolated Controller-Level Cancellation A/B — n=15

Date: 2026-06-28
Host: Windows WSL2 only (no Mac servers — commands via /voice_command/parsed)

## Protocol
Bypasses ASR/PP entirely. barge_measure.py publishes JSON commands
directly to /voice_command/parsed topic. Each trial: go_home (13 s)
-> move_to a (velocity 0.1) -> 3 s delay -> safety.stop.
Two conditions, 15 trials each:

A) Corrected: executor cancels both MoveGroup goal AND
   follow_joint_trajectory action (line 114 active).
B) Baseline: executor cancels MoveGroup goal only, trajectory
   controller cancel commented out (line 114 disabled).

## Results
Corrected: 15/15 CANCELED, mean latency 0.115 +/- 0.005 s,
travel 0.000 rad.
Baseline: 15/15 SUCCEEDED, mean latency 7.57 +/- 0.03 s,
travel 2.94 +/- 0.01 rad (robot completes full trajectory).

## Files
- isolated_corrected_n15.csv — condition A per-trial
- isolated_baseline_n15.csv — condition B per-trial
- executor_corrected_FINAL.log — condition A executor log
- executor_baseline_FINAL.log — condition B executor log
- barge_corrected_run.log — condition A measurement log
- barge_baseline_run.log — condition B measurement log
