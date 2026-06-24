# Measurement Conditions — n=15 Revision Campaign

Date: 2026-06-24

## Host Configuration

- **Host 1 (inference):** MacBook Pro M2 Pro, 16 GB unified memory, macOS 26.5
  - ASR server: `audio-server --host 0.0.0.0 --port 8080 --mode asr` (release build, lazy loading)
  - PersonaPlex: offline during go_home trials (RAM constraint; single 16 GB host cannot run ASR + PP as separate processes)
- **Host 2 (robotic control):** Windows 11 + WSL2 Ubuntu 22.04, ROS 2 Humble, MoveIt2, Gazebo Classic
  - Nodes: bridge_node, voice_safety_checker, voice_task_executor (with controller-level cancel patch)
  - Controller: joint_trajectory_controller (active)
- **Network:** WiFi LAN, Mac 192.168.1.102, Windows 192.168.1.108

## Protocol

- go_home scenario: n=15 trials, 45 s inter-trial interval
- Pre-recorded WAV (go_home.wav, 24 kHz mono PCM16) published via publish_audio.py
- One warmup call before trial 1 (excluded from analysis) to trigger lazy model loading
- No server restart between trials
- PP timeout set to 2 s (connection refused returns immediately; does not affect voice-to-motion path)

## Measurement Definitions

- **Voice-to-motion latency:** "Audio chunk received from Unity" (bridge log) → "Goal completed successfully" (executor log)
- **ASR latency:** "POST ASR /transcribe..." → "Published /voice_command/text:" (bridge log)
- Consistent with thesis Section 4 definitions for comparability with original n=5 results (5.04 ± 0.75 s)

## Server Mode Notes

- go_home, safety gate: ASR-only mode (`--mode asr`), PersonaPlex offline
- barge-in, PersonaPlex latency: will use `--mode all` on port 8080 (single process, both endpoints)
