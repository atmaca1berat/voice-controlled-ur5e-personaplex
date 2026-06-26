# Measurement Conditions — n=15 Revision Campaign

Date: 2026-06-24

## Host Configuration

- **Host 1 (inference):** MacBook Pro M2 Pro, 16 GB unified memory, macOS 26.5
  - ASR server: `audio-server --host 0.0.0.0 --port 8080 --mode asr` (release build, lazy loading, continuous)
  - PersonaPlex server: `audio-server --host 0.0.0.0 --port 8081 --mode pp` (release build, lazy loading, restarted per trial)
- **Host 2 (robotic control):** Windows 11 + WSL2 Ubuntu 22.04, ROS 2 Humble, MoveIt2, Gazebo Classic
  - Nodes: bridge_node, voice_safety_checker, voice_task_executor
  - Controller: joint_trajectory_controller (active)
- **Network:** WiFi LAN, Mac 192.168.1.102, Windows 192.168.1.108

## Protocol

- go_home scenario: n=15 trials
- Pre-recorded WAV (go_home.wav, 24 kHz mono PCM16) published via publish_audio.py
- PersonaPlex server restarted between each trial (pp_restart_loop.sh)
- ASR server continuous (no restart)
- Bridge PP timeout: 300 s

## Measurement Definitions

- **Voice-to-motion latency:** "Audio chunk received from Unity" (bridge log) → "Goal completed successfully" (executor log)
- **ASR latency:** "POST ASR /transcribe..." → "Published /voice_command/text:" (bridge log)
- **PP-wall latency:** "POST PP /respond..." → "Agent transcript:" (bridge log)
- Consistent with thesis Section 4 definitions for comparability with original n=5 results (5.04 ± 0.75 s)

## Results

- V2M: 4.83 ± 0.75 s, 95% CI [4.42, 5.24]
- ASR: 3.94 ± 0.68 s, 95% CI [3.56, 4.32]
- PP-wall: 12.38 ± 0.33 s, 95% CI [12.20, 12.56]
- 15/15 succeeded, 100% accuracy

## Known Issue

Bridge logundaki "PP response duration: 6.08s" satiri 15 trial boyunca sabit kaliyor ve hatalı. Gercek PP-wall suresi (POST PP → Agent transcript) olcum ile 12.38 s'dir. 6.08s'i kullanma.

## Raw Data

- dual_n15_gohome.csv — per-trial V2M, ASR, PP-wall
- bridge_dual_n15_20260624_202003.log — bridge node log
- executor_revision_20260624_195107.log — executor node log
