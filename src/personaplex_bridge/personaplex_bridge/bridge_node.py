import asyncio
import base64
import json
import threading
import wave
import io

import aiohttp
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .nlu_module import NLUModule


MAC_HOST = "172.21.61.203"
ASR_PORT = 8080
PP_PORT = 8081
ASR_HTTP_BASE = f"http://{MAC_HOST}:{ASR_PORT}"
PP_HTTP_BASE = f"http://{MAC_HOST}:{PP_PORT}"

PERSONA_PROMPT = (
    "You are an industrial robot control assistant. "
    "You receive voice commands from operators and translate them "
    "into precise robot movements. Always confirm commands before execution. "
    "If you detect a safety concern, immediately warn the operator."
)
DEFAULT_VOICE = "NATF0"
SAMPLE_RATE = 24000
PP_MAX_STEPS = 60


def pcm16_to_wav_bytes(pcm16_b64: str, sample_rate: int = SAMPLE_RATE) -> bytes:
    pcm_bytes = base64.b64decode(pcm16_b64)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm_bytes)
    return buf.getvalue()


def wav_to_pcm16_b64(wav_bytes: bytes) -> str:
    with wave.open(io.BytesIO(wav_bytes), "rb") as r:
        frames = r.readframes(r.getnframes())
    return base64.b64encode(frames).decode("utf-8")


class PersonaPlexBridge(Node):
    def __init__(self):
        super().__init__("personaplex_bridge")
        self.text_publisher = self.create_publisher(String, "/voice_command/text", 10)
        self.parsed_publisher = self.create_publisher(String, "/voice_command/parsed", 10)
        self.audio_out_publisher = self.create_publisher(String, "/audio/to_unity", 10)
        self.agent_text_publisher = self.create_publisher(String, "/voice_command/agent_text", 10)
        self.subscription = self.create_subscription(
            String, "/audio/from_unity", self.audio_callback, 10
        )
        self.nlu = NLUModule()
        self.audio_queue = asyncio.Queue()
        self.get_logger().info("PersonaPlex Bridge node started")
        self.get_logger().info("ASR HTTP: " + ASR_HTTP_BASE)
        self.get_logger().info("PP HTTP: " + PP_HTTP_BASE)
        self.get_logger().info("Voice: " + DEFAULT_VOICE)

    def audio_callback(self, msg: String):
        try:
            self.audio_queue.put_nowait(msg.data)
            self.get_logger().info("Audio chunk received from Unity: " + str(len(msg.data)) + " bytes b64")
        except Exception as e:
            self.get_logger().error("Audio callback error: " + str(e))

    def publish_transcript(self, text: str):
        msg = String()
        msg.data = text
        self.text_publisher.publish(msg)
        self.get_logger().info("Published /voice_command/text: " + text)

    def publish_parsed(self, result_dict: dict):
        msg = String()
        msg.data = json.dumps(result_dict)
        self.parsed_publisher.publish(msg)
        intent = result_dict.get("intent")
        params = result_dict.get("parameters", {})
        self.get_logger().info("Published /voice_command/parsed: intent=" + str(intent) + " params=" + str(params))

    def publish_audio_to_unity(self, audio_b64: str):
        msg = String()
        msg.data = audio_b64
        self.audio_out_publisher.publish(msg)
        self.get_logger().info("Published /audio/to_unity: " + str(len(audio_b64)) + " bytes b64")

    def publish_agent_text(self, text: str):
        msg = String()
        msg.data = text
        self.agent_text_publisher.publish(msg)
        self.get_logger().info("Published /voice_command/agent_text: " + text)


async def transcribe_via_http(node: PersonaPlexBridge, http: aiohttp.ClientSession, audio_b64: str):
    try:
        wav_bytes = pcm16_to_wav_bytes(audio_b64)
        node.get_logger().info("POST ASR /transcribe...")
        async with http.post(
            ASR_HTTP_BASE + "/transcribe",
            data=wav_bytes,
            headers={"Content-Type": "audio/wav"},
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            if resp.status != 200:
                node.get_logger().error("ASR HTTP error: " + str(resp.status))
                return
            data = await resp.json()
            transcript = data.get("text", "")
            node.publish_transcript(transcript)
            nlu_result = node.nlu.parse(transcript)
            node.publish_parsed(nlu_result.to_dict())
    except Exception as e:
        node.get_logger().error("transcribe_via_http error: " + str(e))


async def respond_via_http(node: PersonaPlexBridge, http: aiohttp.ClientSession, audio_b64: str):
    try:
        wav_bytes = pcm16_to_wav_bytes(audio_b64)
        wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
        payload = {
            "audio_base64": wav_b64,
            "voice": DEFAULT_VOICE,
            "max_steps": str(PP_MAX_STEPS),
            "format": "json",
            "system_prompt": PERSONA_PROMPT
        }
        node.get_logger().info("POST PP /respond...")
        async with http.post(
            PP_HTTP_BASE + "/respond",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                node.get_logger().error("PP HTTP error " + str(resp.status) + ": " + text[:200])
                return
            data = await resp.json()

            agent_transcript = data.get("transcript", "")
            duration = data.get("duration", 0)
            audio_response_b64 = data.get("audio_base64", "")

            if agent_transcript:
                node.get_logger().info("Agent transcript: " + agent_transcript)
                node.publish_agent_text(agent_transcript)

            if audio_response_b64:
                response_wav_bytes = base64.b64decode(audio_response_b64)
                pcm16_only_b64 = wav_to_pcm16_b64(response_wav_bytes)
                node.get_logger().info("PP response duration: " + str(duration) + "s")
                node.publish_audio_to_unity(pcm16_only_b64)
    except Exception as e:
        node.get_logger().error("respond_via_http error: " + str(e))


async def main_loop(node: PersonaPlexBridge):
    async with aiohttp.ClientSession() as http:
        node.get_logger().info("HTTP session ready, waiting for audio...")
        while rclpy.ok():
            try:
                audio_b64 = await asyncio.wait_for(node.audio_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            node.get_logger().info("Dispatching: ASR (8080) + PP (8081) parallel HTTP")

            await asyncio.gather(
                transcribe_via_http(node, http, audio_b64),
                respond_via_http(node, http, audio_b64),
                return_exceptions=True
            )


def spin_thread(node):
    rclpy.spin(node)


def main():
    rclpy.init()
    node = PersonaPlexBridge()

    spin = threading.Thread(target=spin_thread, args=(node,), daemon=True)
    spin.start()

    try:
        asyncio.run(main_loop(node))
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
