"""Lightweight Piper TTS HTTP server for cascade-TTS baseline experiment."""

import argparse
import base64
import io
import json
import time
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler

from piper import PiperVoice

DEFAULT_MODEL = "models/piper/en_US-lessac-medium.onnx"
DEFAULT_PORT = 8082

voice: PiperVoice = None


class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._json_response({"status": "ok"})
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/synthesize":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        text = body.get("text", "")

        if not text:
            self._json_response({"error": "empty text"}, status=400)
            return

        t0 = time.time()
        chunks = list(voice.synthesize(text))
        synth_s = time.time() - t0

        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(chunks[0].sample_rate)
            for c in chunks:
                w.writeframes(c.audio_int16_bytes)

        wav_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        self._json_response({
            "audio_base64": wav_b64,
            "synth_ms": round(synth_s * 1000, 1),
            "text": text,
            "sample_rate": chunks[0].sample_rate,
        })

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[TTS] {args[0]}")


def main():
    global voice
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    print(f"[TTS] Loading model: {args.model}")
    t0 = time.time()
    voice = PiperVoice.load(args.model)
    print(f"[TTS] Model loaded in {time.time()-t0:.3f}s (sample_rate={voice.config.sample_rate})")

    server = HTTPServer(("0.0.0.0", args.port), TTSHandler)
    print(f"[TTS] Server listening on :{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
