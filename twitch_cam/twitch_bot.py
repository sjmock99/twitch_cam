#!/usr/bin/env python3
import rclpy
import threading
from rclpy.node import Node
from std_msgs.msg import Float32
from twitch_cam_msgs.srv import ServoMotion
from twitchio.ext import commands
import threading
from example_interfaces.msg import Int64


# Shared Variable 
servo1_pos = 0
servo2_pos = 0
motion_ready = False
mutex = threading.Lock()


# INSERT TWITCH PARSING... ETC...

class TwitchBot(Node):
    def __init__(self):
        super().__init__("twitch_bot")
        self.client = self.create_client(ServoMotion, '/servo_motion')  # Service client
        print("ROS2 node launched")
        self.number_timer_ = self.create_timer(1.0, self.ctrl_loop_callback)


    def ctrl_loop_callback(self):
        print("CONTROL LOOP ...")
        global motion_ready
        global servo1_pos
        global servo2_pos

        with mutex:
            # print(servo1_pos)
            # print(servo2_pos)
            # print(motion_ready)
            if motion_ready == True:
                print("MOTION BEGIN!")
                servo1_request = ServoMotion.Request()
                servo1_request.servo_number = 1
                servo1_request.servo_pos = servo1_pos
                print("SERVO 1 GO!")
                response = self.client.call(servo1_pos) # Blocking call
                print(response.end_pos)
                print(response.success)

                servo2_request = ServoMotion.Request()
                servo2_request.servo_number = 2
                servo2_request.servo_pos = servo2_pos
                print("SERVO2 GO!")
                response = self.client.call(servo2_pos) # Blocking call
                print(response.end_pos)
                print(response.success)

                motion_ready = False



class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token='uiqe254kmy0xhszzh5dekk56s19nq9', prefix = '!', initial_channels=['smockodockoiot'])

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
    async def move_servo(self, ctx: commands.Context, servo1_pos_msg: int, servo2_pos_msg: int):
        # Here we have a command hello, we can invoke our command with our prefix and command name
        # e.g ?hello
        # We can also give our commands aliases (different names) to invoke with.

        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        
        global servo1_pos
        global servo2_pos
        global motion_ready

        print(servo1_pos_msg)
        print(servo2_pos_msg)

        if motion_ready == False: # OKAY TO READ A MUTEX LOCKED VARIABLE
            with mutex:
                servo1_pos = servo1_pos_msg
                servo2_pos = servo2_pos_msg
                motion_ready = True
                print("TWITCH MSG PARSED... READY FOR CONTROL LOOP!")
        

        # await ctx.send(f'Hello {ctx.author.name}!')

def spin_ros_node(node):
    rclpy.spin(node)
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
