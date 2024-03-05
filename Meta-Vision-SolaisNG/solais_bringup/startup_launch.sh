#!/bin/bash
source /home/robomaster/ros2_humble/install/local_setup.sh
source /home/robomaster/ros_ws/install/setup.sh
ros2 launch rm_vision_bringup vision_bringup.launch.py
