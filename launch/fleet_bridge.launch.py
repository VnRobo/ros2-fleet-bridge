"""Launch file for vnrobo_fleet_bridge.

Usage:
    ros2 launch vnrobo_fleet_bridge fleet_bridge.launch.py api_key:=YOUR_KEY robot_id:=my_robot

Optional overrides:
    robot_name:=Turtlebot3-01
    heartbeat_interval:=30
    topic_battery:=/battery_state
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("api_key", description="VnRobo API key from app.vnrobo.com"),
        DeclareLaunchArgument("robot_id", description="Unique robot identifier"),
        DeclareLaunchArgument("robot_name", default_value="", description="Human-readable robot name (auto-detected if empty)"),
        DeclareLaunchArgument("heartbeat_interval", default_value="30", description="Heartbeat interval in seconds"),
        DeclareLaunchArgument("endpoint", default_value="https://app.vnrobo.com/api/heartbeat"),
        DeclareLaunchArgument("topic_battery", default_value="/battery_state"),
        DeclareLaunchArgument("topic_diagnostics", default_value="/diagnostics"),
        DeclareLaunchArgument("topic_cmd_vel", default_value="/cmd_vel"),
        DeclareLaunchArgument("topic_odom", default_value="/odom"),

        Node(
            package="vnrobo_fleet_bridge",
            executable="fleet_bridge",
            name="vnrobo_fleet_bridge",
            output="screen",
            parameters=[{
                "api_key": LaunchConfiguration("api_key"),
                "robot_id": LaunchConfiguration("robot_id"),
                "robot_name": LaunchConfiguration("robot_name"),
                "heartbeat_interval": LaunchConfiguration("heartbeat_interval"),
                "endpoint": LaunchConfiguration("endpoint"),
                "topic_battery": LaunchConfiguration("topic_battery"),
                "topic_diagnostics": LaunchConfiguration("topic_diagnostics"),
                "topic_cmd_vel": LaunchConfiguration("topic_cmd_vel"),
                "topic_odom": LaunchConfiguration("topic_odom"),
            }],
        ),
    ])
