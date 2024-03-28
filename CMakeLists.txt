cmake_minimum_required(VERSION 3.5)
project(twitch_cam)
# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()
# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(twitch_cam_msgs REQUIRED)


# Install Python modules
ament_python_install_package(${PROJECT_NAME})
# Install Python executables
install(PROGRAMS
  twitch_cam/servo_controller.py
  twitch_cam/twitch_bot.py
  twitch_cam/twitch_bot_stream.py
  twitch_cam/open_cv_test.py
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()