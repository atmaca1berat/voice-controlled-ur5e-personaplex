import sys
import csv
import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import JointState
from action_msgs.msg import GoalStatusArray

CONTROLLER_STATUS_TOPIC = "/joint_trajectory_controller/follow_joint_trajectory/_action/status"
PARSED_TOPIC = "/voice_command/parsed"
STATUS = {0: "UNKNOWN", 1: "ACCEPTED", 2: "EXECUTING", 3: "CANCELING", 4: "SUCCEEDED", 5: "CANCELED", 6: "ABORTED"}

HOME_MSG = '{"intent": "motion.go_home", "parameters": {}, "priority": 3, "confidence": 1.0, "raw_transcript": "go home"}'
MOVE_A_MSG = '{"intent": "motion.move_to", "parameters": {"target": "a"}, "priority": 3, "confidence": 1.0, "raw_transcript": "move to position a"}'
STOP_MSG = '{"intent": "safety.stop", "parameters": {}, "priority": 1, "confidence": 1.0, "raw_transcript": "stop"}'

ARM_JOINTS = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
              "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
SPEED_THRESHOLD = 0.02
SPEED_WINDOW = 0.1
STILL_HOLD = 0.4


class BargeMeasure(Node):
    def __init__(self):
        super().__init__("barge_measure")
        self.pub = self.create_publisher(String, PARSED_TOPIC, 10)
        self.create_subscription(JointState, "/joint_states", self.js_cb, 50)
        self.create_subscription(GoalStatusArray, CONTROLLER_STATUS_TOPIC, self.status_cb, 50)
        self.history = []
        self.last_pos = None
        self.last_motion_time = None
        self.max_speed = 0.0
        self.last_terminal_status = None

    def arm_vector(self, msg: JointState):
        idx = {n: i for i, n in enumerate(msg.name)}
        if not all(j in idx for j in ARM_JOINTS):
            return None
        return [msg.position[idx[j]] for j in ARM_JOINTS]

    def js_cb(self, msg: JointState):
        vec = self.arm_vector(msg)
        if vec is None:
            return
        now = time.time()
        self.last_pos = vec
        self.history.append((now, vec))
        cutoff = now - SPEED_WINDOW - 0.05
        while len(self.history) > 2 and self.history[0][0] < cutoff:
            self.history.pop(0)
        ref = None
        for t, v in self.history:
            if now - t >= SPEED_WINDOW:
                ref = (t, v)
        if ref is not None:
            dt = now - ref[0]
            if dt > 0:
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, ref[1])))
                speed = dist / dt
                self.max_speed = max(self.max_speed, speed)
                if speed > SPEED_THRESHOLD:
                    self.last_motion_time = now

    def status_cb(self, msg: GoalStatusArray):
        for st in msg.status_list:
            if st.status in (4, 5, 6):
                self.last_terminal_status = st.status

    def publish(self, data):
        m = String()
        m.data = data
        self.pub.publish(m)

    def spin_for(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)

    def wait_until_moving(self, timeout):
        end = time.time() + timeout
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)
            if self.max_speed > SPEED_THRESHOLD:
                return True
        return False

    def wait_until_stopped(self, timeout):
        end = time.time() + timeout
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)
            if self.last_motion_time is not None and (time.time() - self.last_motion_time) > STILL_HOLD:
                return self.last_motion_time
        return self.last_motion_time


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    label = sys.argv[2] if len(sys.argv) > 2 else "run"
    csv_path = sys.argv[3] if len(sys.argv) > 3 else f"/tmp/barge_{label}.csv"

    rclpy.init()
    node = BargeMeasure()
    node.spin_for(1.0)

    rows = []
    for i in range(1, n_trials + 1):
        node.get_logger().info(f"===== TRIAL {i}/{n_trials} ({label}) =====")

        node.publish(HOME_MSG)
        node.spin_for(13.0)

        node.max_speed = 0.0
        node.last_motion_time = None
        node.last_terminal_status = None
        node.publish(MOVE_A_MSG)

        moving = node.wait_until_moving(6.0)
        if not moving:
            node.get_logger().warn(f"Trial {i}: robot never started moving")
        node.spin_for(3.0)

        pos_at_stop = list(node.last_pos) if node.last_pos else None
        t_stop_cmd = time.time()
        node.publish(STOP_MSG)
        node.get_logger().info(f"Trial {i}: STOP published")

        stop_time = node.wait_until_stopped(20.0)
        node.spin_for(1.5)
        final_pos = list(node.last_pos) if node.last_pos else None

        latency = (stop_time - t_stop_cmd) if stop_time is not None else float("nan")
        travel_after_stop = dist(final_pos, pos_at_stop) if (final_pos and pos_at_stop) else float("nan")
        final_status = node.last_terminal_status
        status_name = STATUS.get(final_status, str(final_status))

        node.get_logger().info(
            f"Trial {i}: latency={latency:.3f}s status={status_name} "
            f"travel_after_stop={travel_after_stop:.3f}rad max_speed={node.max_speed:.3f}"
        )
        rows.append({
            "trial": i,
            "label": label,
            "cancel_to_stop_latency_s": round(latency, 4) if latency == latency else "nan",
            "controller_final_status_code": final_status if final_status is not None else "",
            "controller_final_status": status_name,
            "travel_after_stop_rad": round(travel_after_stop, 4) if travel_after_stop == travel_after_stop else "nan",
            "max_speed_rad_s": round(node.max_speed, 4),
        })

    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    node.get_logger().info(f"Wrote {csv_path}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
