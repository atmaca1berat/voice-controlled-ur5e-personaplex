import json
import math
import queue
import threading
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from std_msgs.msg import String
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest,
    Constraints,
    JointConstraint,
    PositionConstraint,
    OrientationConstraint,
    BoundingVolume,
)
from geometry_msgs.msg import Pose
from shape_msgs.msg import SolidPrimitive


PLANNING_GROUP = "ur_manipulator"
BASE_FRAME = "base_link"
END_EFFECTOR_LINK = "tool0"

JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
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

GRASP_HOLD_SECONDS = 1.5
GOAL_TIMEOUT_SECONDS = 60.0


class VoiceSequenceExecutor(Node):
    def __init__(self):
        super().__init__("voice_sequence_executor")
        self.cb_group = ReentrantCallbackGroup()
        self.subscription = self.create_subscription(
            String, "/voice_command/parsed", self.parsed_callback, 10,
            callback_group=self.cb_group
        )
        self.move_group_client = ActionClient(
            self, MoveGroup, "/move_action", callback_group=self.cb_group
        )
        self.work_queue = queue.Queue()
        self.get_logger().info("Voice Sequence Executor started")
        self.get_logger().info("Waiting for /move_action server...")
        self.move_group_client.wait_for_server()
        self.get_logger().info("MoveIt2 action server connected")
        self.worker = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker.start()

    def parsed_callback(self, msg: String):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self.get_logger().error("JSON decode error: " + str(e))
            return
        intent = payload.get("intent")
        params = payload.get("parameters", {})
        if intent == "motion.waypoint":
            self.work_queue.put(("waypoint", params))
        elif intent == "motion.pick_place":
            self.work_queue.put(("pick_place", params))

    def worker_loop(self):
        while rclpy.ok():
            try:
                kind, params = self.work_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if kind == "waypoint":
                self.run_waypoint(params)
            elif kind == "pick_place":
                self.run_pick_place(params)

    def run_waypoint(self, params):
        names = params.get("waypoints", [])
        if not names:
            self.get_logger().warn("Waypoint: empty list")
            return
        self.get_logger().info("Waypoint sequence: " + str(names))
        for i, name in enumerate(names):
            self.get_logger().info("Waypoint " + str(i + 1) + "/" + str(len(names)) + ": " + name)
            status = self.go_to_named(name)
            self.get_logger().info("Waypoint '" + name + "' result: " + status)
            if status != "SUCCEEDED":
                self.get_logger().warn("Waypoint sequence aborted at '" + name + "'")
                return
        self.get_logger().info("Waypoint sequence complete")

    def run_pick_place(self, params):
        pick = params.get("pick", "a")
        place = params.get("place", "ready")
        self.get_logger().info("Pick-place: pick='" + pick + "' place='" + place + "'")

        status = self.go_to_named(pick)
        self.get_logger().info("Move to pick '" + pick + "' result: " + status)
        if status != "SUCCEEDED":
            self.get_logger().warn("Pick-place aborted: could not reach pick pose")
            return

        self.get_logger().info("Simulated grasp (no gripper in sim): closing on object at '" + pick + "'")
        time.sleep(GRASP_HOLD_SECONDS)
        self.get_logger().info("Simulated grasp complete (object attached: simulated)")

        status = self.go_to_named(place)
        self.get_logger().info("Move to place '" + place + "' result: " + status)
        if status != "SUCCEEDED":
            self.get_logger().warn("Pick-place aborted: could not reach place pose")
            return

        self.get_logger().info("Simulated release (no gripper in sim): opening at '" + place + "'")
        time.sleep(GRASP_HOLD_SECONDS)
        self.get_logger().info("Pick-place complete (simulated grasp)")

    def go_to_named(self, name):
        if name in NAMED_POSE_TARGETS:
            x, y, z = NAMED_POSE_TARGETS[name]
            goal = self.build_pose_goal(x, y, z)
        elif name in NAMED_JOINT_TARGETS:
            goal = self.build_joint_goal(NAMED_JOINT_TARGETS[name])
        else:
            self.get_logger().warn("Unknown named target: " + str(name))
            return "UNKNOWN_TARGET"
        return self.send_and_wait(goal)

    def send_and_wait(self, goal):
        send_future = self.move_group_client.send_goal_async(goal)
        if not self.wait_for_future(send_future, GOAL_TIMEOUT_SECONDS):
            return "SEND_TIMEOUT"
        goal_handle = send_future.result()
        if goal_handle is None or not goal_handle.accepted:
            return "REJECTED"
        result_future = goal_handle.get_result_async()
        if not self.wait_for_future(result_future, GOAL_TIMEOUT_SECONDS):
            return "RESULT_TIMEOUT"
        result = result_future.result().result
        if result.error_code.val == 1:
            return "SUCCEEDED"
        return "ERROR_" + str(result.error_code.val)

    def wait_for_future(self, future, timeout):
        end = time.time() + timeout
        while time.time() < end:
            if future.done():
                return True
            time.sleep(0.02)
        return False

    def build_joint_goal(self, joint_values):
        request = MotionPlanRequest()
        request.group_name = PLANNING_GROUP
        request.num_planning_attempts = 5
        request.allowed_planning_time = 5.0
        request.max_velocity_scaling_factor = 0.1
        request.max_acceleration_scaling_factor = 0.1
        constraints = Constraints()
        for i, value in enumerate(joint_values):
            jc = JointConstraint()
            jc.joint_name = JOINT_NAMES[i]
            jc.position = float(value)
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)
        request.goal_constraints.append(constraints)
        goal = MoveGroup.Goal()
        goal.request = request
        return goal

    def build_pose_goal(self, x, y, z):
        request = MotionPlanRequest()
        request.group_name = PLANNING_GROUP
        request.num_planning_attempts = 5
        request.allowed_planning_time = 5.0
        request.max_velocity_scaling_factor = 0.1
        request.max_acceleration_scaling_factor = 0.1
        constraints = Constraints()
        pc = PositionConstraint()
        pc.header.frame_id = BASE_FRAME
        pc.link_name = END_EFFECTOR_LINK
        pc.target_point_offset.x = 0.0
        pc.target_point_offset.y = 0.0
        pc.target_point_offset.z = 0.0
        pc.weight = 1.0
        bv = BoundingVolume()
        sp = SolidPrimitive()
        sp.type = SolidPrimitive.SPHERE
        sp.dimensions = [0.02]
        bv.primitives.append(sp)
        sphere_pose = Pose()
        sphere_pose.position.x = float(x)
        sphere_pose.position.y = float(y)
        sphere_pose.position.z = float(z)
        sphere_pose.orientation.w = 1.0
        bv.primitive_poses.append(sphere_pose)
        pc.constraint_region = bv
        constraints.position_constraints.append(pc)
        oc = OrientationConstraint()
        oc.header.frame_id = BASE_FRAME
        oc.link_name = END_EFFECTOR_LINK
        oc.orientation.w = 1.0
        oc.absolute_x_axis_tolerance = 0.5
        oc.absolute_y_axis_tolerance = 0.5
        oc.absolute_z_axis_tolerance = 3.14
        oc.weight = 1.0
        constraints.orientation_constraints.append(oc)
        request.goal_constraints.append(constraints)
        goal = MoveGroup.Goal()
        goal.request = request
        return goal


def main():
    rclpy.init()
    node = VoiceSequenceExecutor()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
