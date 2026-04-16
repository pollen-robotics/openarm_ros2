"""Bringup launch for OpenArm + Gripette end-effector (right arm, real hardware).

Loads the pre-generated URDF from openarm_gripette_description (joint names
already match openarm_hardware/OpenArm_v10HW conventions), starts ros2_control,
and spawns joint_state_broadcaster + joint_trajectory_controller.

Usage:
    ros2 launch openarm_bringup openarm_gripette.launch.py
    ros2 launch openarm_bringup openarm_gripette.launch.py can_interface:=can0
    ros2 launch openarm_bringup openarm_gripette.launch.py robot_controller:=forward_position_controller
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def robot_nodes_spawner(context: LaunchContext, can_interface, controllers_file):
    can_interface_str = context.perform_substitution(can_interface)
    controllers_file_str = context.perform_substitution(controllers_file)

    urdf_path = os.path.join(
        get_package_share_directory("openarm_gripette_description"),
        "urdf", "openarm_right_gripette.urdf",
    )
    with open(urdf_path, "r") as f:
        robot_description = f.read()

    # The URDF has can_interface baked in as "can0"; substitute the launch argument.
    robot_description = robot_description.replace(
        '<param name="can_interface">can0</param>',
        f'<param name="can_interface">{can_interface_str}</param>',
    )

    robot_description_param = {"robot_description": robot_description}

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description_param],
    )

    # ros2_control_node reads robot_description for the hardware interface plugin
    # and controllers_file for controller configuration.
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="both",
        parameters=[robot_description_param, controllers_file_str],
    )

    return [robot_state_pub_node, control_node]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            "can_interface",
            default_value="can0",
            description="CAN interface for OpenArm hardware (e.g. can0).",
        ),
        DeclareLaunchArgument(
            "robot_controller",
            default_value="joint_trajectory_controller",
            choices=["forward_position_controller", "joint_trajectory_controller"],
            description="Controller to activate after bringup.",
        ),
        DeclareLaunchArgument(
            "runtime_config_package",
            default_value="openarm_bringup",
            description="Package containing the controllers yaml.",
        ),
    ]

    can_interface = LaunchConfiguration("can_interface")
    robot_controller = LaunchConfiguration("robot_controller")
    runtime_config_package = LaunchConfiguration("runtime_config_package")

    controllers_file = PathJoinSubstitution([
        FindPackageShare(runtime_config_package),
        "config", "v10_controllers", "openarm_v10_controllers.yaml",
    ])

    robot_nodes_func = OpaqueFunction(
        function=robot_nodes_spawner,
        args=[can_interface, controllers_file],
    )

    rviz_config_file = PathJoinSubstitution([
        FindPackageShare("openarm_description"),
        "rviz", "openarm_gripette.rviz",
    ])

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
    )

    # Spawn controllers after ros2_control_node has had time to start
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[robot_controller, "-c", "/controller_manager"],
    )

    # Note: gripper_controller is intentionally NOT spawned here —
    # openarm_v10_controllers.yaml references openarm_finger_joint1 which
    # is the standard gripper, absent from the Gripette URDF.

    return LaunchDescription(
        declared_arguments + [
            robot_nodes_func,
            rviz_node,
            TimerAction(period=1.0, actions=[joint_state_broadcaster_spawner]),
            TimerAction(period=1.0, actions=[robot_controller_spawner]),
        ]
    )
