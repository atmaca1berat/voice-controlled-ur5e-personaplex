# Voice-Controlled UR5e via NVIDIA PersonaPlex

Real-time full-duplex voice control of a simulated Universal Robots UR5e industrial manipulator, integrating **NVIDIA PersonaPlex** (MLX 4-bit on Apple Silicon), **Qwen3-ASR**, **ROS 2 Humble**, **MoveIt2**, **Gazebo**, and **Unity 2022.3**.

This repository accompanies the graduation thesis *"NVIDIA PersonaPlex for Real-Time Full-Duplex Voice-Controlled Industrial Robot Control"* and contains all source code, the modified inference-server patches, the natural language understanding (NLU) module with its 33-test suite, the Unity operator scripts, and the raw experimental logs from the measurement campaigns of 21 May 2026 (voice-to-motion and PersonaPlex latency) and 29 May 2026 (barge-in cancellation, safety gate, and sequence executor).

- **Author:** Berat Atmaca (2019556012), Çukurova University, Department of Computer Engineering
- **Supervisor:** Lect. PhD Yunus Emre Çoğurcu
- **License:** MIT

---

## Overview

The system lets an operator control a simulated UR5e with spoken English commands. A push-to-talk Unity client captures the operator's audio and publishes it to a ROS 2 bridge node. The bridge dispatches the audio **in parallel** to two inference endpoints running on an Apple Silicon host: a Qwen3-based ASR server (for the user transcript) and a PersonaPlex full-duplex speech-to-speech server (for the agent voice). A rule-based NLU module maps the transcript to one of thirteen structured intents, which a MoveIt2-based voice task executor turns into motion goals for the manipulator. A spoken stop command cancels an active trajectory (barge-in).

Measured end-to-end performance (n = 5 trials per scenario):

- Voice-to-motion latency (go home): **5.04 ± 0.75 s**
- Barge-in cancellation latency (full voice, spoken stop to halt): **3.54 ± 0.33 s** (controller-level preemption: 0.115 ± 0.004 s)

See the thesis (Section 4) and `benchmarks/` for the full results and raw logs.

---

## Hardware requirements

This is a **hybrid two-host** deployment connected over a local WiFi network.

**Host 1 — Apple Silicon (inference):**
- Apple Mac with Apple Silicon (developed on **Mac M2 Pro, 16 GB unified memory**)
- macOS with the MLX runtime
- ~6 GB free unified memory for the 4-bit quantized PersonaPlex model (~5.3 GB) plus the ASR backend

**Host 2 — Windows workstation (robotics):**
- Windows with **WSL2 (Ubuntu 22.04)**
- ROS 2 Humble Hawksbill, MoveIt2, Gazebo
- Unity 2022.3 (operator client)
- Discrete GPU recommended for Gazebo rendering (developed on RTX-class GPU)

The two hosts must be on the same network. The bridge reaches the inference servers over HTTP on ports `8080` (ASR) and `8081` (PersonaPlex).

---

## Repository layout

```
.
├── benchmarks/        Raw experimental logs (n5_tests_20260521/) and baseline benchmarks
├── docs/              Supporting documentation
├── nlu_module/        Rule-based NLU module (Python, 13 intents) + 33-test suite
├── patches/           Modifications applied to the upstream Apple Silicon PersonaPlex server
├── src/               ROS 2 bridge node, voice task executor, safety checker, sequence executor
├── test_scripts/      Test/measurement scripts and audio samples
├── unity_scripts/     Unity C# scripts (MicPublisher, AudioSubscriber, TranscriptDisplay)
├── LICENSE            MIT
├── Makefile           Convenience targets
└── README.md
```

---

## Dependencies

**Apple Silicon host (inference server, Swift)**
- Swift toolchain (Xcode with the Metal toolchain installed)
- MLX and the PersonaPlex MLX 4-bit build (~5.3 GB)
- Qwen3-ASR backend
- The modified `audio-server` from `patches/`, built within the upstream `ivan-digital/qwen3-asr-swift` fork (this server is Swift, not Python)

**Windows / WSL2 host**
- ROS 2 Humble Hawksbill
- MoveIt2, Gazebo, the Universal Robots ROS 2 description/driver packages
- Unity 2022.3 with the ROS-TCP-Connector package

ROS 2 package dependencies (from each `package.xml`):
- `personaplex_bridge`: `rclpy`, `std_msgs`, `python3-aiohttp`
- `voice_task_executor`: `rclpy`, `std_msgs`, `geometry_msgs`, `sensor_msgs`, `shape_msgs`, `moveit_msgs`

The `nlu_module` has **no external dependencies** (pure Python standard library).

---

## Installation

Clone the repository on both hosts:

```bash
git clone https://github.com/atmaca1berat/voice-controlled-ur5e-personaplex.git
cd voice-controlled-ur5e-personaplex
```

**Apple Silicon host** — the inference server is the Swift `audio-server` from the upstream `ivan-digital/qwen3-asr-swift` fork, with the modifications in `patches/` applied. It is **built in the upstream fork, not in this repository**. After replacing `Sources/AudioServerCLI/AudioServerCommand.swift` and `Sources/AudioServer/AudioServer.swift` with the versions in `patches/` (see `patches/README.md`):

```bash
swift build --product audio-server -c release --disable-sandbox
./scripts/build_mlx_metallib.sh release
```

**Windows / WSL2 host** — build the ROS 2 workspace:

```bash
# from your ROS 2 workspace
colcon build --packages-select personaplex_bridge voice_task_executor
source install/setup.bash
```

From the repository root, the `Makefile` provides convenience targets: `make build` (colcon build of both packages), `make test` (run the NLU test suite), and `make clean` (remove `build/ install/ log/`).

Import the scripts in `unity_scripts/` into a Unity 2022.3 project configured with the ROS-TCP-Connector, and set the ROS IP/port in the scene's `ROSConnectionManager`.

---

## Running

**1. Start the two inference servers on the Apple Silicon host** (two isolated processes, run from the built fork directory):

```bash
.build/release/audio-server --mode asr --port 8080 --host 0.0.0.0
.build/release/audio-server --mode pp  --port 8081 --host 0.0.0.0
```

**2. Launch the ROS 2 stack on the Windows / WSL2 host** (Gazebo + MoveIt2 + UR5e), then start the bridge and the executor:

```bash
ros2 run personaplex_bridge bridge_node
ros2 run voice_task_executor voice_task_executor_node
ros2 run voice_task_executor voice_safety_checker_node
ros2 run voice_task_executor voice_sequence_executor_node
```

**3. Open the Unity operator client**, confirm the ROS connection, hold the push-to-talk key (Space), speak a command (for example, *"go home"*), and release. To interrupt an active motion, hold the key and speak *"stop"*.

---

## Supported commands

Thirteen intents across three categories (see the thesis, Appendix A):

- **Motion (5):** `go_home`, `move_to`, `pick`, `place`, `rotate`
- **Safety (5):** `stop`, `emergency_stop`, `pause`, `resume`, `slow_down`
- **Query (3):** `where_are_you`, `status`, `current_position`

Safety intents are dispatched at the highest priority and pre-empt a co-occurring motion command within the same utterance.

The system additionally includes a **pre-execution safety gate** (`voice_safety_checker_node`) that validates commands against joint limits, workspace reach, forbidden-zone bounds, and velocity/acceleration envelopes before forwarding them to the executor, and a **sequence executor** (`voice_sequence_executor_node`) that chains named-joint waypoint goals and simulated pick-and-place operations.

---

## Demo videos

Five demonstration clips are available as release assets on the [v1.0-final release](https://github.com/atmaca1berat/voice-controlled-ur5e-personaplex/releases/tag/v1.0-final):

1. Voice-controlled go_home (23 s)
2. Voice-controlled move_to_a (22 s)
3. Barge-in cancellation (13 s)
4. Safety gate rejection (28 s)
5. Waypoint sequence (44 s)

---

## Tests

The NLU module ships with a suite of **33 deterministic unit tests**, all passing (plain Python, no pytest required):

```bash
cd nlu_module && python3 nlu_test.py
# or, from the repository root:
make test
```

---

## Note on velocity scaling

`voice_task_executor_node.py` is configured with `max_velocity_scaling_factor=0.1` (10%) to provide a sufficiently long motion window for the barge-in cancellation measurements. This is a deliberate experimental setting documented in Section 4 of the thesis, not a performance limitation. For demonstrations without cancellation timing measurements, this value can safely be raised.

---

## Known limitations

The inference layer exhibits three documented failure modes under sustained operation (thesis Section 4.9): a per-inference memory accumulation that can drive the host out of memory after three to five consecutive responses, an idle silent termination after extended dormancy, and a dual-process termination under close-in-time concurrent operation. The measurement protocol uses a restart-between-trials procedure to work within this envelope. The HTTP transport between the bridge and the inference servers is unencrypted and is intended for an isolated local network only.

---

## Citation

If you use this work, please cite the thesis:

> Atmaca, B. (2026). *NVIDIA PersonaPlex for Real-Time Full-Duplex Voice-Controlled Industrial Robot Control* [Graduation thesis]. Çukurova University, Department of Computer Engineering.

---

## License

Released under the [MIT License](LICENSE).
