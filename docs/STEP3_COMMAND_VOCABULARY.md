# Roadmap Step 3 — Command Vocabulary Specification

**Date:** 29 April 2026
**Project:** Real-Time Full-Duplex Voice-Controlled Industrial Robot Arm Integrating PersonaPlex, ROS2 Humble and Unity
**Author:** Berat Atmaca (2019556012)
**Advisor:** Öğr. Gör. Dr. Yunus Emre Çogurcu

## 1. Objective

Define a structured voice command vocabulary that the Natural Language Understanding (NLU) module will recognise from PersonaPlex transcripts. The vocabulary follows the categorisation specified in the project roadmap and consists of thirteen commands grouped into three categories: motion, safety, and query.

## 2. Design Principles

The vocabulary is designed around the following principles:

1. **Roadmap fidelity.** The exact command set provided in the advisor's roadmap is used without expansion at this stage.
2. **English only.** PersonaPlex-7B-v1 is currently an English-only model. Multilingual support is left for future work.
3. **Intent-parameter separation.** Each command is represented as an `intent` plus a parameter dictionary, mirroring conventional NLU practice and allowing the same intent to carry different argument values.
4. **Priority levels.** Commands are assigned a priority that determines dispatch order in the safety supervisor (Step 7). Safety commands take precedence over motion and query commands.
5. **Deterministic mapping.** Each intent maps to exactly one MoveIt2 action or robot-state query. No ambiguous mappings are allowed at the NLU layer.

## 3. Command Set

### 3.1. Motion Commands

| # | Intent ID         | Trigger Keywords                          | Parameters                  | Example Transcript                  | MoveIt2 Action / Effect                                  |
| - | ----------------- | ----------------------------------------- | --------------------------- | ----------------------------------- | -------------------------------------------------------- |
| 1 | `motion.move_to`  | move to, go to                            | `target` (named pose or xyz)| "Move to position A"                | `MoveGroup` action with `goal` set to named pose `A`      |
| 2 | `motion.go_home`  | go home, return home, home position       | none                        | "Go home"                           | `MoveGroup` action with `goal` set to named pose `home`   |
| 3 | `motion.pick`     | pick, grab, take                          | `object` (optional)         | "Pick the object"                   | Pick sub-pipeline (planning + gripper close)              |
| 4 | `motion.place`    | place, put, drop                          | `target` (optional)         | "Place it on the table"             | Place sub-pipeline (planning + gripper open)              |
| 5 | `motion.rotate`   | rotate, turn, spin                        | `axis`, `angle` (optional)  | "Rotate the wrist"                  | Joint-space rotation on the specified axis                |

### 3.2. Safety Commands

| # | Intent ID                  | Trigger Keywords                              | Parameters | Example Transcript        | MoveIt2 Action / Effect                                              |
| - | -------------------------- | --------------------------------------------- | ---------- | ------------------------- | -------------------------------------------------------------------- |
| 6 | `safety.stop`              | stop, halt                                    | none       | "Stop"                    | Cancel current `MoveGroup` goal; hold pose                            |
| 7 | `safety.emergency_stop`    | emergency stop, e-stop, stop now              | none       | "Emergency stop"          | Cancel goal + send controller stop; latch state until manual reset    |
| 8 | `safety.slow_down`         | slow down, reduce speed                       | none       | "Slow down"               | Scale velocity/acceleration limits to 0.5x                            |
| 9 | `safety.pause`             | pause, hold                                   | none       | "Pause"                   | Pause current trajectory execution; remain at last commanded pose     |
| 10| `safety.resume`            | resume, continue                              | none       | "Resume"                  | Resume previously paused trajectory                                   |

### 3.3. Query Commands

| #  | Intent ID                   | Trigger Keywords                            | Parameters | Example Transcript           | MoveIt2 Action / Effect                                              |
| -- | --------------------------- | ------------------------------------------- | ---------- | ---------------------------- | -------------------------------------------------------------------- |
| 11 | `query.where_are_you`       | where are you                               | none       | "Where are you"              | Read end-effector pose; return as natural-language reply              |
| 12 | `query.status`              | what is your status, status, are you ok     | none       | "What is your status"        | Read controller state + safety supervisor state; return as reply      |
| 13 | `query.current_position`    | current position, position, joint angles    | none       | "Current position"           | Read joint states; return as reply                                    |

## 4. Priority and Pre-emption

When the NLU module detects multiple intents in a single transcript (for example: "Move to A — actually stop"), the highest-priority intent is dispatched first and lower-priority intents are discarded.

| Priority | Categories                              |
| -------- | --------------------------------------- |
| 1 (top)  | Safety: `emergency_stop`, `stop`         |
| 2        | Safety: `pause`, `slow_down`, `resume`   |
| 3        | Motion: `move_to`, `go_home`, `pick`, `place`, `rotate` |
| 4        | Query: `where_are_you`, `status`, `current_position` |

This ranking is enforced inside the NLU module and re-checked by the safety supervisor (Step 7) before any motion is sent to the controller.

## 5. Output Schema

The NLU module emits a JSON-serialisable Python dictionary with the following schema:

```json
{
  "intent": "motion.move_to",
  "parameters": {
    "target": "A"
  },
  "priority": 3,
  "raw_transcript": "Move to position A",
  "matched_keywords": ["move to"],
  "confidence": "exact_match"
}
```

The `confidence` field carries one of three values:

- `exact_match` — a trigger keyword was found verbatim in the transcript.
- `partial_match` — a synonym or variant was found (e.g. "halt" for `safety.stop`).
- `unknown` — no intent recognised; the message is reported to the bridge node and not dispatched.

## 6. Limitations and Future Extensions

The vocabulary above is intentionally minimal and matches the roadmap exactly. It does not yet support:

- Numeric parameters such as "move forward 30 centimetres".
- Compound commands such as "pick the object and place it on the table".
- Confirmation handshakes ("Are you sure you want to stop?").
- Languages other than English.

These are deferred to later phases of the project.

## 7. Step Status

This document defines the command vocabulary contract used by the NLU module implementation in `nlu_module.py`. With the vocabulary fixed, the next sub-step of Roadmap Step 3 is the implementation of the parser and its unit tests.
