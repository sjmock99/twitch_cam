#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from twitch_cam_msgs.msg import ServoPos
from cv_bridge import CvBridge
import cv2 as cv
import ffmpeg
import os

# Initialize the CvBridge
bridge = CvBridge()

stream_key = "***REMOVED***"
stream_url = f"rtmp://jfk.contribute.live-video.net/app/{stream_key}"
class TwitchBotStream(Node):
    def __init__(self):
        super().__init__("twitch_bot_stream")
        self.server_ = self.create_subscription(
            CompressedImage, "image_raw/compressed", self.image_callback, 10)
        self.servo_pos_sub_ = self.create_subscription(ServoPos, "/servo_position", self.position_callback, 10)
        self.get_logger().info("CV Test has been started.")
        self.ffmpeg_process = None
        self.servo1_pos = 0 # Starts at origin
        self.servo2_pos = 0 # Starts at origin

    # Define a callback in order to get information about the position of the servo --> put it in the image_callback
    def position_callback(self, msg):
        self.servo1_pos = msg.servo1_pos
        self.servo2_pos = msg.servo2_pos

    # Define a callback to handle incoming images from the ROS topic
    def image_callback(self, msg):
        try:
            # compression_format = msg.format
            # print(compression_format)
            # Convert ROS Image message to OpenCV image
            cv_image = bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")  # Adjust the encoding type as per your image format
            cv_image = cv.rotate(cv_image, cv.ROTATE_180)

            current_dir = os.getcwd()
            image_path = os.path.join(current_dir, 'src/twitch_cam/twitch_cam/axis.png')
            # Scale the image to be significantly smaller
            axis_img = cv.imread(image_path)

            # Define the scaling factors
            scale_x = 0.30  # Scale factor for width
            scale_y = 0.30  # Scale factor for height

            # Calculate the new dimensions
            new_width = int(axis_img.shape[1] * scale_x)
            new_height = int(axis_img.shape[0] * scale_y)

            # Resize the smaller image
            axis_img = cv.resize(axis_img, (new_width, new_height))

            # # Determine the dimensions of the smaller image
            smaller_height, smaller_width, _ = axis_img.shape

            # # Determine the dimensions of the larger image
            # larger_height, larger_width, _ = cv_image.shape

            # Print out the dimensions and ratio
            # print("Dimensions of the smaller image:", smaller_width, "x", smaller_height)
            # print("Dimensions of the larger image:", larger_width, "x", larger_height)

            top_right_y = 0
            top_right_x = cv_image.shape[1] - smaller_width

            # Update the larger image with the smaller image in the region of interest
            cv_image[top_right_y:top_right_y + smaller_height, top_right_x:top_right_x + smaller_width] = axis_img

            # font 
            font = cv.FONT_HERSHEY_SIMPLEX 
            
            # org 
            org1 = (50, 50) 
            org2 = (50, 75)
            # fontScale 
            fontScale = 0.75
            
            # Blue color in BGR 
            color = (255, 0, 0) 
            
            # Line thickness of 1 px 
            thickness = 2

            msg1 = 'Servo 1 Pos: ' + str(self.servo1_pos) + " deg"
            msg2 = 'Servo 2 Pos: ' + str(self.servo2_pos) + " deg"
            cv_image = cv.putText(cv_image, msg1, org1, font,  
                   fontScale, color, thickness, cv.LINE_AA) 
            cv_image = cv.putText(cv_image, msg2, org2, font,  
                   fontScale, color, thickness, cv.LINE_AA) 

            # # # Display the image (livestream locally)
            # cv.imshow("Livestream", cv_image)
            # cv.waitKey(1)  # Wait for a short duration to display the next frame (adjust as needed)

            # Convert the OpenCV image to bytes
            _, img_encoded = cv.imencode('.jpg', cv_image)
            img_bytes = img_encoded.tobytes()

            # img_bytes = cv_image.tobytes()

            # Check if ffmpeg process is not running or has terminated
            if self.ffmpeg_process is None or self.ffmpeg_process.poll() is not None:
                # Start a new ffmpeg process for streaming
                self.ffmpeg_process = (
                    ffmpeg
                    # .input('pipe:', format='rawvideo', pix_fmt='bgr8', s=f'{cv_image.shape[1]}x{cv_image.shape[0]}')
                    # .input('pipe:', format='mjpeg', pix_fmt='bgr8', s=f'{cv_image.shape[1]}x{cv_image.shape[0]}')
                    .input('pipe:', format='image2pipe', framerate='30', vcodec='mjpeg', pix_fmt='bgr8') 
                    .output(stream_url, format='flv', vcodec='libx264', pix_fmt='yuv420p', preset='ultrafast', tune='zerolatency', b='3M', g='30', crf='20')
                    .overwrite_output()
                    .run_async(pipe_stdin=True)
                )

            # Write the frame bytes to the subprocess pipe
            self.ffmpeg_process.stdin.write(img_bytes)

        except Exception as e:
            print(e)

def main(args=None):
    rclpy.init(args=args)
    node = TwitchBotStream()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()