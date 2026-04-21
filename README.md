# ros2-fleet-bridge

[![ROS 2](https://img.shields.io/badge/ROS%202-Humble%20%7C%20Iron%20%7C%20Jazzy-blue)](https://docs.ros.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Monitor any ROS 2 robot on **[VnRobo Fleet Monitor](https://app.vnrobo.com)** with a single launch command — no code required.

```bash
ros2 launch vnrobo_fleet_bridge fleet_bridge.launch.py \
    api_key:=YOUR_KEY \
    robot_id:=my_robot
```

That's it. Your robot appears on the dashboard immediately.

## What It Does

Automatically subscribes to standard ROS 2 topics and sends telemetry to VnRobo:

| Topic | Data sent |
|-------|-----------|
| `/battery_state` | Battery percentage |
| `/diagnostics` | Error / warning detection |
| `/cmd_vel` | Moving vs idle status |
| `/odom` | Robot position |
| `/robot_description` | Auto-detects robot name from URDF |

All topic names are configurable via parameters.

## Install

### From source (ROS 2 workspace)

```bash
cd ~/ros2_ws/src
git clone https://github.com/VnRobo/ros2-fleet-bridge
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select vnrobo_fleet_bridge
source install/setup.bash
```

### Dependency

```bash
pip install requests
```

## Usage

### Launch file (recommended)

```bash
ros2 launch vnrobo_fleet_bridge fleet_bridge.launch.py \
    api_key:=YOUR_API_KEY \
    robot_id:=turtlebot3-01
```

### With custom topic names

```bash
ros2 launch vnrobo_fleet_bridge fleet_bridge.launch.py \
    api_key:=YOUR_KEY \
    robot_id:=go2-01 \
    topic_battery:=/go2/battery \
    topic_cmd_vel:=/go2/cmd_vel \
    heartbeat_interval:=15
```

### Via params file

```bash
ros2 run vnrobo_fleet_bridge fleet_bridge \
    --ros-args --params-file config/default_params.yaml
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | `""` | **Required.** API key from app.vnrobo.com |
| `robot_id` | `""` | **Required.** Unique robot identifier |
| `robot_name` | `""` | Display name (auto-detected from URDF if empty) |
| `heartbeat_interval` | `30` | Seconds between heartbeats |
| `endpoint` | `https://app.vnrobo.com/api/heartbeat` | API endpoint |
| `topic_battery` | `/battery_state` | BatteryState topic |
| `topic_diagnostics` | `/diagnostics` | DiagnosticArray topic |
| `topic_cmd_vel` | `/cmd_vel` | Twist topic |
| `topic_odom` | `/odom` | Odometry topic |

## Tested Robots

| Robot | ROS 2 distro | Status |
|-------|-------------|--------|
| TurtleBot3 Burger/Waffle | Humble | ✅ |
| Unitree Go2 | Humble | ✅ |
| Unitree G1 | Humble | ✅ |
| UR5e (Universal Robots) | Iron | ✅ |
| Clearpath Husky | Humble | ✅ |
| Custom robots | Any | ✅ (configure topic names) |

## Get API Key

1. Create a free account at **[app.vnrobo.com](https://app.vnrobo.com)** (free for 3 robots)
2. Add a robot in the dashboard
3. Copy the API key

## Contributing

Issues and PRs welcome.

```bash
git clone https://github.com/VnRobo/ros2-fleet-bridge
cd ros2-fleet-bridge
# Source your ROS 2 workspace, then:
colcon build --packages-select vnrobo_fleet_bridge
```

## License

MIT — see [LICENSE](LICENSE).

---

**Monitor your fleet for free → [app.vnrobo.com](https://app.vnrobo.com)**
