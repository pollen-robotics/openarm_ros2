import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # Load the pre-generated URDF directly (no xacro needed)
    urdf_path = os.path.join(
        get_package_share_directory("openarm_gripette_description"),
        "urdf", "openarm_right_gripette.urdf"
    )

    with open(urdf_path, "r") as f:
        robot_description = f.read()

    rviz_config_path = os.path.join(
        get_package_share_directory("openarm_description"),
        "rviz", "openarm_gripette.rviz"
    )

    return LaunchDescription([
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),
        Node(
            package="joint_state_publisher_gui",
            executable="joint_state_publisher_gui",
            name="joint_state_publisher_gui",
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["--display-config", rviz_config_path],
            output="screen",
        ),
    ])
