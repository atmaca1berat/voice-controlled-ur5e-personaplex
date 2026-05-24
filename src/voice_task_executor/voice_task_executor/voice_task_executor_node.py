import json
import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import Pose, PoseStamped
from sensor_msgs.msg import JointState
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest,
    Constraints,
    JointConstraint,
    PositionConstraint,
    OrientationConstraint,
    BoundingVolume,
)
from shape_msgs.msg import SolidPrimitive


PLANNING_GROUP = "ur_manipulator"
BASE_FRAME = "base_link"
END_EFFECTOR_LINK = "tool0"

NAMED_JOINT_TARGETS = {
    "home": [0.0, -math.pi / 2.0, 0.0, -math.pi / 2.0, 0.0, 0.0],
    "ready": [0.0, -math.pi / 3.0, math.pi / 3.0, -math.pi / 2.0, -math.pi / 2.0, 0.0],
    "a": [math.pi, -math.pi / 4.0, math.pi / 4.0, -math.pi / 4.0, math.pi / 2.0, math.pi / 2.0],
}

NAMED_POSE_TARGETS = {
    "b": (0.4, -0.2, 0.4),
    "c": (0.3, 0.0, 0.6),
}

JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]


class VoiceTaskExecutor(Node):
    def __init__(self):
        super().__init__("voice_task_executor")
        self.subscription = self.create_subscription(
            String, "/voice_command/parsed", self.parsed_callback, 10
        )
        self.move_group_client = ActionClient(self, MoveGroup, "/move_action")
        self.current_goal_handle = None
        self.get_logger().info("Voice Task Executor started")
        self.get_logger().info("Planning group: " + PLANNING_GROUP)
        self.get_logger().info("Waiting for /move_action server...")
        self.move_group_client.wait_for_server()
        self.get_logger().info("MoveIt2 action server connected")

    def parsed_callback(self, msg: String):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self.get_logger().error("JSON decode error: " + str(e))
            return

        intent = payload.get("intent")
        params = payload.get("parameters", {})
        priority = payload.get("priority")

        if intent is None:
            self.get_logger().info("No intent recognized, ignoring")
            return

        self.get_logger().info(
            "Intent: " + intent + " priority=" + str(priority) + " params=" + str(params)
        )

        if intent == "motion.go_home":
            self.execute_named_joint("home")
        elif intent == "motion.move_to":
            target = params.get("target", "")
            if target in NAMED_POSE_TARGETS:
                self.execute_named_pose(target)
            elif target in NAMED_JOINT_TARGETS:
                self.execute_named_joint(target)
            else:
                self.get_logger().warn("Unknown move target: " + str(target))
        elif intent == "safety.stop" or intent == "safety.emergency_stop":
            self.cancel_current_goal()
        elif intent == "safety.pause":
            self.cancel_current_goal()
            self.get_logger().info("Paused (current goal cancelled)")
        elif intent == "safety.resume":
            self.get_logger().info("Resume requested (no stored goal in v1, ignored)")
        elif intent == "safety.slow_down":
            self.get_logger().info("Slow down requested (velocity scaling not implemented in v1)")
        elif intent == "motion.pick" or intent == "motion.place" or intent == "motion.rotate":
            self.get_logger().warn("Intent " + intent + " not implemented in v1")
        elif intent.startswith("query."):
            self.get_logger().info("Query intent " + intent + " (no MoveIt action)")
        else:
            self.get_logger().warn("Unhandled intent: " + intent)

    def cancel_current_goal(self):
        if self.current_goal_handle is None:
            self.get_logger().info("No active goal to cancel")
            return
        self.get_logger().info("Cancelling current goal")
        future = self.current_goal_handle.cancel_goal_async()
        future.add_done_callback(self._cancel_done_callback)

    def _cancel_done_callback(self, future):
        result = future.result()
        if result is None:
            self.get_logger().error("Cancel call returned None")
            return
        if len(result.goals_canceling) > 0:
            self.get_logger().info("Goal cancelled successfully")
        else:
            self.get_logger().info("Goal not active or already finished")
        self.current_goal_handle = None

    def execute_named_joint(self, name: str):
        if name not in NAMED_JOINT_TARGETS:
            self.get_logger().warn("Unknown joint target: " + name)
            return
        joint_values = NAMED_JOINT_TARGETS[name]
        self.get_logger().info("Sending joint goal '" + name + "': " + str(joint_values))
        goal = self._build_joint_goal(joint_values)
        self._send_goal(goal)

    def execute_named_pose(self, name: str):
        if name not in NAMED_POSE_TARGETS:
            self.get_logger().warn("Unknown pose target: " + name)
            return
        x, y, z = NAMED_POSE_TARGETS[name]
        self.get_logger().info(
            "Sending pose goal '" + name + "': x=" + str(x) + " y=" + str(y) + " z=" + str(z)
        )
        goal = self._build_pose_goal(x, y, z)
        self._send_goal(goal)

    def _build_joint_goal(self, joint_values):
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

    def _build_pose_goal(self, x: float, y: float, z: float):
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

        from geometry_msgs.msg import Pose as PoseMsg
        sphere_pose = PoseMsg()
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

    def _send_goal(self, goal):
        if self.current_goal_handle is not None:
            self.get_logger().info("Cancelling previous goal before sending new one")
            self.current_goal_handle.cancel_goal_async()
            self.current_goal_handle = None

        send_future = self.move_group_client.send_goal_async(goal)
        send_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected by MoveIt2")
            return
        self.get_logger().info("Goal accepted, executing...")
        self.current_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        result = future.result().result
        error_code = result.error_code.val
        if error_code == 1:
            self.get_logger().info("Goal completed successfully")
        else:
            self.get_logger().warn("Goal finished with error code: " + str(error_code))
        self.current_goal_handle = None


def main():
    rclpy.init()
    node = VoiceTaskExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
