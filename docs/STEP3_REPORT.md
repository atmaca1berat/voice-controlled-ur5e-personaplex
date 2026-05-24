# Roadmap Step 3 — Command Vocabulary and NLU Module Development

**Date:** 29 April 2026
**Project:** Real-Time Full-Duplex Voice-Controlled Industrial Robot Arm Integrating PersonaPlex, ROS2 Humble and Unity
**Author:** Berat Atmaca (2019556012)
**Advisor:** Öğr. Gör. Dr. Yunus Emre Çogurcu

## 1. Objective

Implement a Natural Language Understanding (NLU) module that parses transcripts produced by PersonaPlex into structured robot commands. The module must recognise the thirteen commands defined in the project roadmap, classify them across three categories (motion, safety, query), and output a deterministic intent-and-parameter representation suitable for downstream consumption by the PersonaPlex-ROS2 bridge node and the MoveIt2 task executor.

## 2. Deliverables

This step produced four artifacts in `~/Documents/tez-projesi/nlu_module/`:

1. **`STEP3_COMMAND_VOCABULARY.md`** — Vocabulary specification document defining the thirteen commands, their trigger keywords, parameters, priority levels, and MoveIt2 mapping.
2. **`nlu_module.py`** — Python implementation of the NLU parser (193 lines, no third-party dependencies beyond the standard library).
3. **`nlu_test.py`** — Unit test suite covering all thirteen intents, their alternative trigger keywords, compound (barge-in) inputs, and edge cases (33 assertions).
4. **`STEP3_REPORT.md`** — This document.

## 3. Implementation Approach

The NLU module follows a regex-and-keyword-matching design as specified in the roadmap. Three considerations drove the implementation:

### 3.1. Priority-based dispatch

Each intent declares a priority value (1 to 4, lower is higher priority). When the transcript contains keywords belonging to multiple intents, the module returns the highest-priority intent only and discards the rest. This is necessary for safety reasons: an utterance such as *"Move to A, actually stop"* must be dispatched as `safety.stop` rather than `motion.move_to`. The same priority ordering will be re-checked by the safety supervisor in Step 7.

### 3.2. Parameter extraction by regex

Where an intent carries a parameter (for example `motion.move_to` carries a `target` parameter), a per-intent regex pattern extracts the relevant value from the normalised transcript. This produces a deterministic, JSON-serialisable parameter dictionary without invoking a heavier semantic parser.

### 3.3. Confidence reporting

The module tags every result with a confidence label. The current implementation reports `exact_match` when at least one trigger keyword is found and `unknown` otherwise. The schema reserves `partial_match` as a future-work category for fuzzy matches. The bridge node will use the confidence label to decide whether to dispatch the command, ask for clarification, or simply log the failure.

## 4. Output Schema

For every transcript the module returns a dataclass that serialises to:

```json
{
  "intent": "motion.move_to",
  "parameters": {
    "target": "a"
  },
  "priority": 3,
  "raw_transcript": "Move to position A",
  "matched_keywords": ["move to", "position"],
  "confidence": "exact_match"
}
```

Unknown commands return:

```json
{
  "intent": null,
  "parameters": {},
  "priority": null,
  "raw_transcript": "Tell me a joke",
  "matched_keywords": [],
  "confidence": "unknown"
}
```

## 5. Test Results

The unit test suite (`nlu_test.py`) defines 33 assertions across the following groups:

| Group                            | Assertions | Status |
| -------------------------------- | ---------- | ------ |
| Motion intents (primary keywords)| 5          | Pass   |
| Motion intents (synonyms)        | 5          | Pass   |
| Safety intents (primary keywords)| 5          | Pass   |
| Safety intents (synonyms)        | 6          | Pass   |
| Query intents                    | 5          | Pass   |
| Compound / barge-in inputs       | 3          | Pass   |
| Edge cases (unknown, empty)      | 4          | Pass   |
| **Total**                        | **33**     | **Pass** |

The barge-in test cases are particularly relevant for the final demonstration scenarios in Step 8. For example:

- *"Move to A, actually stop"* → resolved to `safety.stop` (priority 1).
- *"Pause and then resume"* → resolved to `safety.pause` (priority 2; the `resume` keyword is ignored as it has equal priority and appears later).
- *"Go home but slow down"* → resolved to `safety.slow_down` (priority 2 over motion priority 3).

These demonstrate that the priority ordering works as intended at the NLU layer, even before the safety supervisor is added in Step 7.

## 6. Limitations and Future Work

The current vocabulary is intentionally aligned with the roadmap and does not yet support:

- **Numeric parameters** (e.g. *"move forward 30 centimetres"*).
- **Compound commands as separate sequential goals** (e.g. *"pick the object and place it on the table"* currently dispatches only the higher-priority pick).
- **Confirmation handshakes** (e.g. *"Are you sure you want to stop?"*).
- **Languages other than English** (PersonaPlex itself is English-only).
- **Fuzzy or partial matches** (the `partial_match` confidence level is reserved but not yet used).

These limitations are acknowledged in the vocabulary specification document and will be addressed in subsequent steps or in future-work proposals.

## 7. Step Status

Roadmap Step 3 — Command Vocabulary and NLU Module Development — is considered **complete**.

Outputs:

1. Thirteen-command vocabulary specified and documented.
2. NLU module implemented as a standalone Python module with no external dependencies.
3. Unit test suite implemented with 33 passing assertions, including barge-in scenarios.
4. Output schema documented and ready for consumption by Step 4.

## 8. Next Steps

According to the project roadmap, the next step is:

**Step 4 — PersonaPlex-ROS2 Bridge Node Development**

This involves writing a ROS2 node (`personaplex_bridge_node`) that streams audio to and from the PersonaPlex WebSocket server, publishes raw transcripts on `/voice_command/text`, invokes the NLU module developed in this step, and publishes structured commands on `/voice_command/parsed`. The NLU module produced here will be imported and called by the bridge node without modification.
