#!/usr/bin/env python3
import rclpy
import threading
from rclpy.node import Node
from std_msgs.msg import Float32
from twitch_cam_msgs.srv import ServoMotion
from twitch_cam_msgs.msg import ServoPos
from twitchio.ext import commands
import threading
from example_interfaces.msg import Int64
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
import time
import asyncio

# Shared Variable 
servo1_pos = 90 # Starting Position
servo2_pos = 90 # Starting Position
servo_num = 0
motion_ready = False
mutex = threading.Lock()

client_cb_group = MutuallyExclusiveCallbackGroup() # Different callback groups such that a service within a service is not blocking the execution of the callback - not 100% sure why this is acting this way to be honest.
timer_cb_group = MutuallyExclusiveCallbackGroup()

# INSERT TWITCH PARSING... ETC...

class TwitchBot(Node):
    def __init__(self):
        super().__init__("twitch_bot")
        self.client = self.create_client(ServoMotion, '/servo_motion', callback_group=client_cb_group)  # Service client
        print("ROS2 node launched")
        self.number_timer_ = self.create_timer(5.0, self.ctrl_loop_callback, callback_group=timer_cb_group)
        self.servo_pos_publisher_ = self.create_publisher(ServoPos, '/servo_position', 10)

    def ctrl_loop_callback(self):
        while True: # Weird way of keeping everything in the same loop / thread without needing to rely on a control loop callback
           # print("CONTROL LOOP ...")
            global motion_ready
            global servo_num
            global servo1_pos
            global servo2_pos

                # print(servo1_pos)
                # print(servo2_pos)
                # print(motion_ready)
            if motion_ready == True:
                    print("MOTION BEGIN!")

                    if servo_num == 1:
                        servo1_request = ServoMotion.Request()
                        servo1_request.servo_number = 1
                        servo1_request.servo_pos = servo1_pos
                        print("SERVO 1 GO!")
                        future = self.client.call_async(servo1_request)
                    elif servo_num == 2:
                        servo2_request = ServoMotion.Request()
                        servo2_request.servo_number = 2
                        servo2_request.servo_pos = servo2_pos
                        print("SERVO2 GO!")
                        future = self.client.call_async(servo2_request)

                    while rclpy.ok():
                        print("PROCESSING!")
                        if future.done():  # Check if the future is completed
                            print("Async Call End")
                            try:
                                response = future.result()  # Get the response
                                print(response.end_pos)
                                print(response.success)

                                if response.success == True:
                                    if servo_num == 1:
                                        servo1_pos = response.end_pos # Giving the actual values 
                                    elif servo_num == 2:
                                        servo2_pos = response.end_pos # Giving the actual values 

                                servo_pos_msg = ServoPos()
                                servo_pos_msg.servo1_pos = servo1_pos
                                servo_pos_msg.servo2_pos = servo2_pos
                                self.servo_pos_publisher_.publish(servo_pos_msg)

                                with mutex:
                                    motion_ready = False
                                break

                            except Exception as e:
                                self.get_logger().error(f'Service call failed: {e}')

                        self.get_logger().info('Waiting for service response...')
                        rclpy.spin_once(self, timeout_sec=0.1)  # Allow the node to process callbacks
            time.sleep(0.1)

class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token='***REMOVED***', prefix = '!', initial_channels=['smockodockoiot'])

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        # Print the contents of our message to console...
        print(message.content)

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    @commands.command()
    async def move_servo(self, ctx: commands.Context, servo_num_msg: int, servo_pos_msg: int):
        # Here we have a command hello, we can invoke our command with our prefix and command name
        # e.g ?hello
        # We can also give our commands aliases (different names) to invoke with.

        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        
        global servo1_pos
        global servo2_pos
        global servo_num
        global motion_ready

       # print(servo_num_msg)
       # print(servo_pos_msg)

        if servo_num_msg == 1 or servo_num_msg == 2:

            print("MODIFYING MOTION READY?")
            print(motion_ready)

            if motion_ready == False: # OKAY TO READ A MUTEX LOCKED VARIABLE
                with mutex:
                    servo_num = servo_num_msg
                    if servo_num == 1:
                        servo1_pos = servo_pos_msg
                    elif servo_num == 2:
                        servo2_pos = servo_pos_msg 
                    motion_ready = True
                    print("TWITCH MSG PARSED... READY FOR CONTROL LOOP!")
                    await ctx.send(f'Robot is in motion! Moving Servo {servo_num_msg} to {servo_pos_msg} degrees!')

                # Attempt at a blocking call while it is mutex locked from the other thread...
                while motion_ready == True:
                    print("WAITING!")
                    await asyncio.sleep(0.1) # By doing await asyncio.sleep, it frees the event loop such that the other asynchronous functions (that might be incorrect) can complete, so that commands are not in a queue.
                await ctx.send(f'Robot Motion is complete.')

def spin_ros_node(node):
    rclpy.spin(node)
    # executor = MultiThreadedExecutor()
    # executor.add_node(node)
    # executor.spin() 

#     async def event_command_error(self, context: commands.Context, error: Exception):

#         if isinstance(error, commands.ArgumentParsingFailed):
#             print("arg error")
#         else:
#             print(error)


def main(args=None):
    rclpy.init(args=args)
    node = TwitchBot()
    twitch_bot = Bot()

    # # Start the ROS2 node in the main thread
    twitch_bot_thread = threading.Thread(target=twitch_bot.run)
    ros_thread = threading.Thread(target=spin_ros_node, args=(node, ))

    print("ROS2 NODE START")
    print("TWITCH BOT START")
    ros_thread.start()
    twitch_bot_thread.start()

    ros_thread.join()
    twitch_bot_thread.join()

    rclpy.shutdown()

if __name__ == "__main__":
    main()
