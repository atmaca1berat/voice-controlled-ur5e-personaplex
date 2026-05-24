#!/usr/bin/env python3
import sys
import time
import wave
import base64
import argparse

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class AudioPublisher(Node):
    def __init__(self, audio_b64: str, topic: str = "/audio/from_unity"):
        super().__init__("test_audio_publisher")
        self.audio_b64 = audio_b64
        self.topic = topic
        self.publisher = self.create_publisher(String, topic, 10)
        self.published = False
        self.timer = self.create_timer(0.5, self.publish_once)

    def publish_once(self):
        if self.published:
            return
        n_subs = self.publisher.get_subscription_count()
        if n_subs == 0:
            self.get_logger().info(f"Waiting for subscriber on {self.topic}...")
            return
        msg = String()
        msg.data = self.audio_b64
        self.publisher.publish(msg)
        wall_time = time.time()
        self.get_logger().info(
            f"PUBLISHED at wall_time={wall_time:.6f} | "
            f"topic={self.topic} | bytes_b64={len(self.audio_b64)} | "
            f"subscribers={n_subs}"
        )
        self.published = True


def wav_to_pcm16_b64(wav_path: str) -> tuple[str, dict]:
    with wave.open(wav_path, "rb") as w:
        channels = w.getnchannels()
        sample_width = w.getsampwidth()
        sample_rate = w.getframerate()
        n_frames = w.getnframes()
        frames = w.readframes(n_frames)
    info = {
        "channels": channels,
        "sample_width": sample_width,
        "sample_rate": sample_rate,
        "n_frames": n_frames,
        "duration_s": n_frames / sample_rate,
        "raw_bytes": len(frames),
    }
    b64 = base64.b64encode(frames).decode("utf-8")
    return b64, info


def main():
    parser = argparse.ArgumentParser(description="Publish a WAV file to ROS2 as base64 PCM16")
    parser.add_argument("wav_path", help="Path to WAV file (24kHz mono PCM16)")
    parser.add_argument("--topic", default="/audio/from_unity", help="ROS2 topic name")
    parser.add_argument("--timeout", type=float, default=15.0, help="Max wait for subscribers (s)")
    args = parser.parse_args()

    print(f"Loading {args.wav_path}...")
    audio_b64, info = wav_to_pcm16_b64(args.wav_path)
    print(f"  channels:     {info['channels']}")
    print(f"  sample_width: {info['sample_width']} bytes ({info['sample_width']*8}-bit)")
    print(f"  sample_rate:  {info['sample_rate']} Hz")
    print(f"  n_frames:     {info['n_frames']}")
    print(f"  duration:     {info['duration_s']:.3f} s")
    print(f"  raw_bytes:    {info['raw_bytes']}")
    print(f"  base64_chars: {len(audio_b64)}")

    if info["channels"] != 1:
        print("WARNING: expected mono")
    if info["sample_width"] != 2:
        print("WARNING: expected 16-bit PCM")
    if info["sample_rate"] != 24000:
        print(f"WARNING: expected 24000 Hz, got {info['sample_rate']}")

    rclpy.init()
    node = AudioPublisher(audio_b64, args.topic)

    start = time.time()
    try:
        while rclpy.ok() and not node.published:
            rclpy.spin_once(node, timeout_sec=0.5)
            if time.time() - start > args.timeout:
                node.get_logger().error(f"Timeout waiting for subscriber on {args.topic}")
                break
    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(0.5)
        node.destroy_node()
        rclpy.shutdown()
        print(f"Published: {node.published}")


if __name__ == "__main__":
    main()
