import time
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

JOINTS = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
          "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
ACTION = "/joint_trajectory_controller/follow_joint_trajectory"
STATUS = {1: "ACCEPTED", 2: "EXECUTING", 3: "CANCELING", 4: "SUCCEEDED", 5: "CANCELED", 6: "ABORTED"}


class C(Node):
    def __init__(self):
        super().__init__("cancel_test")
        self.cli = ActionClient(self, FollowJointTrajectory, ACTION)

    def goal(self, secs):
        jt = JointTrajectory()
        jt.joint_names = JOINTS
        p = JointTrajectoryPoint()
        p.positions = [3.14, -0.78, 0.78, -0.78, 1.57, 1.57]
        p.time_from_start = Duration(sec=secs)
        jt.points = [p]
        g = FollowJointTrajectory.Goal()
        g.trajectory = jt
        return g


def main():
    rclpy.init()
    n = C()
    n.cli.wait_for_server(timeout_sec=15.0)
    t0 = time.time()
    fut = n.cli.send_goal_async(n.goal(20))
    rclpy.spin_until_future_complete(n, fut)
    gh = fut.result()
    n.get_logger().info(f"[t={time.time()-t0:.3f}] goal accepted, executing")
    end = time.time() + 5.0
    while time.time() < end:
        rclpy.spin_once(n, timeout_sec=0.1)
    n.get_logger().info(f"[t={time.time()-t0:.3f}] >>> CANCEL (robot moving) <<<")
    cfut = gh.cancel_goal_async()
    rclpy.spin_until_future_complete(n, cfut)
    cres = cfut.result()
    n.get_logger().info(f"[t={time.time()-t0:.3f}] cancel response: goals_canceling={len(cres.goals_canceling)}")
    rfut = gh.get_result_async()
    rclpy.spin_until_future_complete(n, rfut, timeout_sec=25.0)
    st = rfut.result().status
    n.get_logger().info(f"[t={time.time()-t0:.3f}] FINAL STATUS = {STATUS.get(st, st)} ({st})")
    n.get_logger().info("REAL PREEMPTION" if st == 5 else "CANCEL INEFFECTIVE (completed)" if st == 4 else f"status={st}")
    n.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
