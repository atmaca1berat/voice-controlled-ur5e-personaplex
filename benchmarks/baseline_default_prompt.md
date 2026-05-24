# PersonaPlex Baseline Benchmark — Default System Prompt

**Date:** 2026-04-27
**Hardware:** M2 Pro, 16 GB unified memory
**Model:** aufklarer/PersonaPlex-7B-MLX-4bit (~5.3 GB)
**Mode:** Turn-based
**Voice:** Natural Male 0 (NATM0)
**Max Steps:** 75
**System Prompt:** Default ("helpful assistant, concise")

## Test Results

| # | Spoken Command | ASR Output | ASR (s) | Infer (s) | Total (s) | Audio In (s) | Audio Out (s) | RTF | Response Relevant? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | "Hello, can you hear me?" | "Can you hear me? Please say yes. You yes, if you end under." | 1.9 | 12.3 | 14.1 | 5.0 | 11.1 | 1.10 | NO (chicken recipe) |
| 2 | "Stop." | "Stop." | 0.5 | 7.0 | 7.5 | 1.2 | 7.3 | 0.96 | UNKNOWN |
| 3 | "Forward." | "Forward." | 0.1 | 7.0 | 7.0 | 1.4 | 7.5 | 0.93 | NO (worries about accidents) |
| 4 | "Move the robot to the home." | "Move the robot to the home." | 0.1 | 9.8 | 10.0 | 4.7 | 10.7 | 0.92 | UNKNOWN |
| 5 | "Rotate ninety degrees clockwise." | NOT TESTED | - | - | - | - | - | - | - |

## Observations

- ASR accuracy: Excellent for short commands (Tests 2-4: perfect transcription).
- First call overhead: Test 1 had RTF 1.10 due to Metal shader warmup; subsequent tests stabilized at RTF 0.92-0.96.
- Inference latency: Stable at ~7-10s for short commands; dominated by audio token generation.
- Response relevance: Default "helpful assistant" prompt produces tangential, off-topic responses (recipes, philosophical reflections) for robot-style commands. Custom system prompt required.
- Memory pressure: Reached critical level (15.23 GB used, 3.69 GB swap, red pressure indicator) after several turns, indicating 16 GB RAM is borderline for sustained use.

## Next Step

Replace default system prompt with industrial robot control assistant prompt and re-run identical test set.