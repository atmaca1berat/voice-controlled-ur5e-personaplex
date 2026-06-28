# Mac Server Modifications

These files contain Berat Atmaca's modifications applied to the upstream ivan-digital/qwen3-asr-swift fork to support the parallel HTTP architecture described in Section 3.7 of the thesis.

Upstream repository: https://github.com/ivan-digital/qwen3-asr-swift

Key changes:
- AudioServerCommand: added --mode flag (all/asr/pp) to allow running the ASR and PersonaPlex inference engines in separate processes on distinct TCP ports (8080 and 8081). This isolation was required to mitigate the MLX-Swift allocator instability described in the thesis.
- AudioServerCommand: added --preload flag for eager model loading at server startup.
- AudioServer: per-mode endpoint registration so that each process exposes only the endpoints relevant to its loaded model.
- AudioServer: added system_prompt parameter to /respond endpoint for configurable PersonaPlex behavior.
- AudioServer: added personaplex_full_duplex mode for /v1/realtime WebSocket, enabling real-time speech-to-speech via WebSocket alongside the existing transcribe-only mode.

To use:
1. Clone the upstream repository.
2. Replace the matching files in the Sources/AudioServerCLI and Sources/AudioServer directories with the modified versions in this folder.
3. Build with `swift build --product audio-server -c release --disable-sandbox` and run scripts/build_mlx_metallib.sh to produce the Metal shader library.
