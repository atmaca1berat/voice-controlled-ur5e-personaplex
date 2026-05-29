import json
import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import String


JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]

JOINT_LIMITS = [
    (-2.0 * math.pi, 2.0 * math.pi),
    (-2.0 * math.pi, 2.0 * math.pi),
    (-2.0 * math.pi, 2.0 * math.pi),
    (-2.0 * math.pi, 2.0 * math.pi),
    (-2.0 * math.pi, 2.0 * math.pi),
    (-2.0 * math.pi, 2.0 * math.pi),
]

NAMED_JOINT_TARGETS = {
    "home": [0.0, -math.pi / 2.0, 0.0, -math.pi / 2.0, 0.0, 0.0],
    "ready": [0.0, -math.pi / 3.0, math.pi / 3.0, -math.pi / 2.0, -math.pi / 2.0, 0.0],
    "a": [math.pi, -math.pi / 4.0, math.pi / 4.0, -math.pi / 4.0, math.pi / 2.0, math.pi / 2.0],
}

NAMED_POSE_TARGETS = {
    "b": (0.4, -0.2, 0.4),
    "c": (0.3, 0.0, 0.6),
}

MAX_REACH = 0.85
MIN_REACH = 0.18
MIN_Z = 0.0

FORBIDDEN_BOX = {
    "x": (0.20, 0.50),
    "y": (-0.50, -0.30),
    "z": (0.00, 0.50),
}

MAX_VELOCITY_SCALING = 0.1
MAX_ACCELERATION_SCALING = 0.1

PARSED_TOPIC = "/voice_command/parsed"
CHECKED_TOPIC = "/voice_command/checked"


class VoiceSafetyChecker(Node):
    def __init__(self):
        super().__init__("voice_safety_checker")
        self.subscription = self.create_subscription(
            String, PARSED_TOPIC, self.parsed_callback, 10
        )
        self.checked_publisher = self.create_publisher(String, CHECKED_TOPIC, 10)
        self.get_logger().info("Voice Safety Checker started")
        self.get_logger().info("Input: " + PARSED_TOPIC + " Output: " + CHECKED_TOPIC)

    def parsed_callback(self, msg: String):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self.get_logger().error("JSON decode error: " + str(e))
            return

        intent = payload.get("intent")
        params = payload.get("parameters", {})

        if intent is None:
            self.get_logger().info("No intent, ignoring")
            return

        if intent.startswith("safety.") or intent.startswith("query."):
            self.get_logger().info("Passthrough (non-motion): " + intent)
            self.forward(msg.data)
            return

        if not intent.startswith("motion."):
            self.get_logger().warn("Rejected: unknown intent class " + intent)
            return

        ok, reason = self.check_velocity(params)
        if not ok:
            self.get_logger().warn("Rejected " + intent + ": " + reason)
            return

        targets, resolve_error = self.resolve_targets(intent, params)
        if resolve_error is not None:
            self.get_logger().warn("Rejected " + intent + ": " + resolve_error)
            return

        for kind, value, label in targets:
            ok, reason = self.check_target(kind, value)
            if not ok:
                self.get_logger().warn(
                    "Rejected " + intent + " target '" + label + "': " + reason
                )
                return

        self.get_logger().info("Accepted " + intent + " params=" + str(params))
        self.forward(msg.data)

    def forward(self, data: str):
        out = String()
        out.data = data
        self.checked_publisher.publish(out)

    def check_velocity(self, params):
        v = params.get("velocity_scaling")
        if v is not None and float(v) > MAX_VELOCITY_SCALING:
            return False, "velocity_scaling " + str(v) + " exceeds max " + str(MAX_VELOCITY_SCALING)
        a = params.get("acceleration_scaling")
        if a is not None and float(a) > MAX_ACCELERATION_SCALING:
            return False, "acceleration_scaling " + str(a) + " exceeds max " + str(MAX_ACCELERATION_SCALING)
        return True, ""

    def resolve_targets(self, intent, params):
        if "target_joints" in params:
            jv = params["target_joints"]
            if not isinstance(jv, list) or len(jv) != len(JOINT_NAMES):
                return [], "target_joints must be a list of " + str(len(JOINT_NAMES)) + " values"
            return [("joint", [float(x) for x in jv], "target_joints")], None

        if "target_pose" in params:
            tp = params["target_pose"]
            if not isinstance(tp, list) or len(tp) != 3:
                return [], "target_pose must be [x, y, z]"
            return [("pose", tuple(float(x) for x in tp), "target_pose")], None

        if intent == "motion.go_home":
            return [("joint", NAMED_JOINT_TARGETS["home"], "home")], None

        if intent == "motion.move_to":
            name = params.get("target", "")
            return self.named_target(name)

        if intent == "motion.waypoint":
            names = params.get("waypoints", [])
            if not isinstance(names, list) or len(names) == 0:
                return [], "waypoints must be a non-empty list of named targets"
            out = []
            for name in names:
                resolved, err = self.named_target(name)
                if err is not None:
                    return [], err
                out.extend(resolved)
            return out, None

        if intent == "motion.pick_place":
            out = []
            for key in ("pick", "place"):
                name = params.get(key, "")
                resolved, err = self.named_target(name)
                if err is not None:
                    return [], "pick_place " + key + ": " + err
                out.extend(resolved)
            return out, None

        if intent in ("motion.pick", "motion.place"):
            name = params.get("target", params.get("object", ""))
            return self.named_target(name)

        return [], "no validatable target for intent " + intent

    def named_target(self, name):
        if name in NAMED_POSE_TARGETS:
            return [("pose", NAMED_POSE_TARGETS[name], name)], None
        if name in NAMED_JOINT_TARGETS:
            return [("joint", NAMED_JOINT_TARGETS[name], name)], None
        return [], "unknown named target '" + str(name) + "'"

    def check_target(self, kind, value):
        if kind == "joint":
            for i, q in enumerate(value):
                low, high = JOINT_LIMITS[i]
                if q < low or q > high:
                    return False, (
                        JOINT_NAMES[i] + " " + str(round(q, 4)) + " outside ["
                        + str(round(low, 4)) + ", " + str(round(high, 4)) + "]"
                    )
            return True, ""

        x, y, z = value
        radius = math.sqrt(x * x + y * y + z * z)
        if radius > MAX_REACH:
            return False, "reach " + str(round(radius, 4)) + " exceeds MAX_REACH " + str(MAX_REACH)
        if radius < MIN_REACH:
            return False, "reach " + str(round(radius, 4)) + " below MIN_REACH " + str(MIN_REACH)
        if z < MIN_Z:
            return False, "z " + str(round(z, 4)) + " below floor " + str(MIN_Z)
        bx = FORBIDDEN_BOX["x"]
        by = FORBIDDEN_BOX["y"]
        bz = FORBIDDEN_BOX["z"]
        if bx[0] <= x <= bx[1] and by[0] <= y <= by[1] and bz[0] <= z <= bz[1]:
            return False, (
                "inside forbidden zone x=" + str(round(x, 3))
                + " y=" + str(round(y, 3)) + " z=" + str(round(z, 3))
            )
        return True, ""


def main():
    rclpy.init()
    node = VoiceSafetyChecker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
