# twitch_cam

A pan/tilt camera robot that Twitch chat controls live. Viewers type `!move_servo <servo> <angle>` in chat, the
camera turns, and the stream shows the new view. Inspired by Twitch Plays Pokémon; built winter 2023-24.

This is the ROS 2 (Python) package that runs on the Raspberry Pi. The servo interfaces are in
[twitch_cam_msgs](https://github.com/sjmock99/twitch_cam_msgs).

## How it works

```
Twitch chat --> twitch_bot --(/servo_motion service)--> micro-ROS agent --UART--> Teensy --PWM--> 2x SG90 servos
                    |                                                                      (pan, tilt)
                    +--(/servo_position topic)--> twitch_bot_stream --ffmpeg/RTMP--> Twitch
Pi camera --> v4l2_camera node --(compressed image)--------^
```

- **Raspberry Pi** (Ubuntu, ROS 2) runs four nodes: the camera driver (`v4l2_camera`), the micro-ROS agent,
  `twitch_bot` and `twitch_bot_stream`.
- **`twitch_bot.py`** reads chat with [twitchio](https://github.com/TwitchIO/TwitchIO), checks the command
  (servo 1 or 2, angle -90 to 90), and calls the `/servo_motion` service. It waits for the move to finish before
  taking the next command, then publishes both positions on `/servo_position`. Chat and ROS run in separate
  threads that share state under a lock.
- **`twitch_bot_stream.py`** turns the compressed camera images into OpenCV frames, rotates them, draws the servo
  positions on top, and streams them to Twitch with ffmpeg.
- **Teensy** (Arduino C++ with micro-ROS) serves `/servo_motion`: it moves the servo and replies with the end
  position, counting it a success within 2°.

Angles are given in the camera's frame, so straight ahead is [0, 0] for viewers.

> **Not included:** the Teensy firmware isn't in this repo.

Other files: `twitch_bot_test.py` (chat bot on its own, no ROS), `open_cv_test.py` (stream test),
`servo_controller.py` (an early publisher test).

## Setup

On the Pi (ROS 2, with `v4l2_camera` and the micro-ROS agent installed):

```bash
sudo apt install ffmpeg
pip install -U twitchio ffmpeg-python

# in a ROS 2 workspace's src/
git clone https://github.com/sjmock99/twitch_cam_msgs
git clone https://github.com/sjmock99/twitch_cam
cd .. && colcon build && source install/setup.bash
```

Credentials are read from the environment, never stored in the code:

```bash
export TWITCH_TOKEN=...                  # the chat bot account's access token, pasted as given
export TWITCH_CHANNEL=yourchannel        # the channel whose chat the bot reads
export TWITCH_STREAM_KEY=live_...        # Twitch dashboard > Settings > Stream
```

## Run

Each in its own terminal (or tmux pane):

```bash
ros2 run v4l2_camera v4l2_camera_node --ros-args -p image_size:="[640,480]"
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0
ros2 run twitch_cam twitch_bot.py
ros2 run twitch_cam twitch_bot_stream.py
```

Then in chat: `!help`, or `!move_servo 1 45` (pan) / `!move_servo 2 -20` (tilt).

## Result

Ran for a week straight without crashes or network drops. Project write-up:
[sjmock99.github.io](https://sjmock99.github.io/projects/twitchcam-v1.html).
