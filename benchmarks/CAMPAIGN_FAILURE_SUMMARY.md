# Inference-Layer Failure Summary Across All Measurement Campaigns

## Table 1 — Campaigns with restart-per-trial protocol (0 failures)

| Campaign | Directory | Date | Trials | Successes | Failures | Protocol |
|----------|-----------|------|--------|-----------|----------|----------|
| go_home n=15 | n15_revision_20260624/ | 2026-06-24 | 15 | 15 | 0 | PP restart-per-trial, ASR continuous |
| barge-in n=15 | barge_n15_20260627/ | 2026-06-27 | 30 | 30 | 0 | PP restart-per-trial, ASR continuous |
| ASR diag S3 (isolated) | asr_diagnosis_20260627/ | 2026-06-24 | 17 | 17 | 0 | PP off, ASR only |
| cascade-TTS n=15 | cascade_tts_n15_20260628/ | 2026-06-28 | 15 | 15 | 0 | PP off, ASR + Piper TTS |
| stop-at-rest n=15 | stop_at_rest_n15_20260628/ | 2026-06-28 | 15 | 15 | 0 | PP off, ASR only |
| isolated controller n=15 | isolated_n15_20260628/ | 2026-06-28 | 30 | 30 | 0 | No Mac servers (direct topic publish) |
| **Subtotal** | | | **122** | **122** | **0** | |

## Table 2 — Campaigns without restart-per-trial protocol (70 failures)

| Campaign | Directory | Log file | Date | Dispatches | Successes | Logged errors | Lost trials | Protocol |
|----------|-----------|----------|------|------------|-----------|---------------|-------------|----------|
| ASR diag S1 | asr_diagnosis_20260627/ | bridge_revision_20260624_114337.log | 2026-06-24 | 23 | 23 | 0 | 0 | PP co-resident, no restart |
| ASR diag S2 | asr_diagnosis_20260627/ | bridge_revision_20260624_122017.log | 2026-06-24 | 14 | 8 | 6 | 0 | PP co-resident, no restart |
| n5 session 1533 | n5_tests_20260521/ | bridge_20260521_1533.log | 2026-05-21 | 4 | 2 | 0 | 2 | PP co-resident, no restart |
| n5 go_home 1541 | n5_tests_20260521/ | bridge_n5_gohome_20260521_1541.log | 2026-05-21 | 6 | 2 | 2 | 2 | PP co-resident, no restart |
| n5 cycles 1611 | n5_tests_20260521/ | bridge_n5_cycles_1611.log | 2026-05-21 | 88 | 30 | 28 | 30 | PP co-resident, no restart |
| **Subtotal** | | | | **135** | **65** | **36** | **34** | |

Lost trials = dispatches − successes − logged errors (dispatch sent, no Published text, no ERROR line).

## Table 3 — Confirmed failure mode breakdown (from logged errors only)

| Failure mode | Count | Source logs |
|--------------|-------|-------------|
| Memory accumulation (Server disconnected) | 15 | bridge_n5_cycles_1611.log (11), bridge_n5_gohome_20260521_1541.log (2), bridge_revision_20260624_122017.log (1 PP-side) + 1 implicit ASR |
| Dual-process termination (Cannot connect 8080 + 8081) | 10 | bridge_n5_cycles_1611.log (4 pairs), bridge_revision_20260624_122017.log (6 — ASR + PP both unreachable) |
| Idle / silent termination (blank error or no error) | 11 | bridge_n5_cycles_1611.log (9 blank ERROR lines), bridge_n5_gohome_20260521_1541.log (2 blank ERROR lines) |
| **Confirmed total** | **36** | |
| Unconfirmed lost trials (no error logged) | 34 | bridge_n5_cycles_1611.log (30), bridge_20260521_1533.log (2), bridge_n5_gohome_20260521_1541.log (2) |
| **All failures** | **70** | |

## Table 4 — Cumulative failure rates

| Scope | Failed | Total dispatches | Rate |
|-------|--------|-----------------|------|
| Confirmed failures only (logged errors) | 36 | 257 | 14.0% |
| All failures including lost trials | 70 | 257 | 27.2% |
