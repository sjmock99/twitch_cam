#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from twitch_cam_msgs.msg import ServoPos
from cv_bridge import CvBridge
import cv2 as cv
import ffmpeg

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
        self.servo1_pos = 90
        self.servo2_pos = 90

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

            # font 
            font = cv.FONT_HERSHEY_SIMPLEX 
            
            # org 
            org1 = (50, 50) 
            org2 = (50, 75)
            # fontScale 
            fontScale = 0.5
            
            # Blue color in BGR 
            color = (255, 0, 0) 
            
            # Line thickness of 1 px 
            thickness = 1

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