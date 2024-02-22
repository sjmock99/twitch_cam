#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32


# INSERT TWITCH PARSING... ETC...

class ServoController(Node):
    def __init__(self):
        super().__init__("servo_controller")

        self.number_publisher_ = self.create_publisher(Float32, "servo_pos", 10)
        self.number_timer_ = self.create_timer(1.0, self.publish_number)
        self.get_logger().info("Servo Position publisher has been started.")
        self.msg = 0.0

    def publish_number(self):
        msg = Float32()
        self.msg = self.msg + 1
        msg.data = self.msg
        self.get_logger().info(str(msg.data))
        self.number_publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ServoController()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
