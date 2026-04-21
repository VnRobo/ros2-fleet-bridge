"""Main ROS 2 node — subscribes to standard topics and sends telemetry to VnRobo."""

import threading
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from sensor_msgs.msg import BatteryState
from nav_msgs.msg import Odometry
from diagnostic_msgs.msg import DiagnosticArray
from geometry_msgs.msg import Twist
from std_msgs.msg import String

from vnrobo_fleet_bridge.vnrobo_client import VnRoboClient


LATCHED_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class FleetBridgeNode(Node):
    """Bridges any ROS 2 robot to VnRobo Fleet Monitor.

    Automatically subscribes to standard topics:
      /battery_state  → battery level
      /diagnostics    → error/warn detection
      /cmd_vel        → moving vs idle detection
      /odom           → position fallback
      /robot_description → robot name auto-detection

    All topic names are configurable via ROS 2 parameters.
    """

    def __init__(self):
        super().__init__("vnrobo_fleet_bridge")

        # --- Parameters ---
        self.declare_parameter("api_key", "")
        self.declare_parameter("robot_id", "")
        self.declare_parameter("robot_name", "")          # fallback if no /robot_description
        self.declare_parameter("heartbeat_interval", 30)
        self.declare_parameter("endpoint", "https://app.vnrobo.com/api/heartbeat")

        self.declare_parameter("topic_battery", "/battery_state")
        self.declare_parameter("topic_diagnostics", "/diagnostics")
        self.declare_parameter("topic_cmd_vel", "/cmd_vel")
        self.declare_parameter("topic_odom", "/odom")
        self.declare_parameter("topic_robot_description", "/robot_description")

        api_key = self.get_parameter("api_key").value
        robot_id = self.get_parameter("robot_id").value
        robot_name = self.get_parameter("robot_name").value
        interval = self.get_parameter("heartbeat_interval").value
        endpoint = self.get_parameter("endpoint").value

        if not api_key:
            self.get_logger().error(
                "api_key parameter is required. "
                "Pass: --ros-args -p api_key:=YOUR_KEY"
            )
            raise RuntimeError("Missing api_key")

        if not robot_id:
            self.get_logger().error(
                "robot_id parameter is required. "
                "Pass: --ros-args -p robot_id:=my_robot"
            )
            raise RuntimeError("Missing robot_id")

        self._client = VnRoboClient(
            api_key=api_key,
            robot_id=robot_id,
            endpoint=endpoint,
        )
        self._robot_name = robot_name or robot_id
        self._interval = interval

        # Telemetry state (updated by topic callbacks, read by heartbeat timer)
        self._battery_pct: Optional[float] = None
        self._status: str = "online"
        self._location: Optional[dict] = None
        self._moving: bool = False
        self._last_cmd_vel_time: Optional[float] = None
        self._lock = threading.Lock()

        # --- Subscriptions ---
        bat_topic = self.get_parameter("topic_battery").value
        diag_topic = self.get_parameter("topic_diagnostics").value
        vel_topic = self.get_parameter("topic_cmd_vel").value
        odom_topic = self.get_parameter("topic_odom").value
        desc_topic = self.get_parameter("topic_robot_description").value

        self.create_subscription(BatteryState, bat_topic, self._on_battery, 10)
        self.create_subscription(DiagnosticArray, diag_topic, self._on_diagnostics, 10)
        self.create_subscription(Twist, vel_topic, self._on_cmd_vel, 10)
        self.create_subscription(Odometry, odom_topic, self._on_odom, 10)
        self.create_subscription(String, desc_topic, self._on_robot_description, LATCHED_QOS)

        # --- Heartbeat timer ---
        self.create_timer(float(interval), self._send_heartbeat)

        self.get_logger().info(
            f"VnRobo Fleet Bridge started | robot_id={robot_id} | "
            f"interval={interval}s | endpoint={endpoint}"
        )
        self.get_logger().info(
            f"Subscribed to: {bat_topic}, {diag_topic}, {vel_topic}, {odom_topic}"
        )

    # ------------------------------------------------------------------ #
    # Topic callbacks                                                       #
    # ------------------------------------------------------------------ #

    def _on_battery(self, msg: BatteryState):
        with self._lock:
            # percentage field: 0.0–1.0 in sensor_msgs/BatteryState
            if msg.percentage >= 0:
                self._battery_pct = round(msg.percentage * 100.0, 1)
            elif msg.voltage > 0:
                # Rough estimate from voltage if percentage not available
                self._battery_pct = None
            self.get_logger().debug(f"Battery: {self._battery_pct}%")

    def _on_diagnostics(self, msg: DiagnosticArray):
        with self._lock:
            has_error = any(
                s.level >= 2  # ERROR or STALE
                for status in msg.status
                for s in [status]
            )
            if has_error and self._status != "offline":
                self._status = "error"
            elif not has_error and self._status == "error":
                self._status = "online"

    def _on_cmd_vel(self, msg: Twist):
        with self._lock:
            moving = (
                abs(msg.linear.x) > 0.01
                or abs(msg.linear.y) > 0.01
                or abs(msg.angular.z) > 0.01
            )
            self._moving = moving
            self._last_cmd_vel_time = self.get_clock().now().nanoseconds / 1e9

    def _on_odom(self, msg: Odometry):
        with self._lock:
            # Store as generic x/y — user maps to GPS in their setup
            self._location = {
                "x": round(msg.pose.pose.position.x, 3),
                "y": round(msg.pose.pose.position.y, 3),
            }

    def _on_robot_description(self, msg: String):
        # Extract robot name from URDF <robot name="...">
        import re
        match = re.search(r'<robot\s+name=["\']([^"\']+)["\']', msg.data)
        if match:
            with self._lock:
                self._robot_name = match.group(1)
            self.get_logger().info(f"Detected robot name from URDF: {self._robot_name}")

    # ------------------------------------------------------------------ #
    # Heartbeat                                                             #
    # ------------------------------------------------------------------ #

    def _send_heartbeat(self):
        with self._lock:
            # Derive status from moving state if not in error
            if self._status not in ("error", "offline"):
                now = self.get_clock().now().nanoseconds / 1e9
                if self._last_cmd_vel_time and (now - self._last_cmd_vel_time) < self._interval * 2:
                    status = "busy" if self._moving else "idle"
                else:
                    status = "online"
            else:
                status = self._status

            payload = dict(
                status=status,
                battery=self._battery_pct,
                location=self._location,
                metadata={"robot_name": self._robot_name, "framework": "ros2"},
            )

        ok = self._client.send(**payload)
        if ok:
            self.get_logger().debug(f"Heartbeat sent: status={payload['status']}")
        else:
            self.get_logger().warning("Heartbeat failed — check API key and network")


def main(args=None):
    rclpy.init(args=args)
    try:
        node = FleetBridgeNode()
        rclpy.spin(node)
    except RuntimeError as e:
        print(f"[vnrobo_fleet_bridge] Fatal: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
