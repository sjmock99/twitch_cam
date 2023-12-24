import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
import cv2 as cv
import ffmpeg

# Initialize the CvBridge
bridge = CvBridge()

stream_key = "live_1007968364_0nzz0I6YcutaYVIKoUVKWGlYh2nS44"
stream_url = f"rtmp://jfk.contribute.live-video.net/app/{stream_key}"
class CvTest(Node):
    def __init__(self):
        super().__init__("cv_test")
        self.server_ = self.create_subscription(
            CompressedImage, "image_raw/compressed", self.image_callback, 10)
        self.get_logger().info("CV Test has been started.")
        self.ffmpeg_process = None

    # Define a callback to handle incoming images from the ROS topic
    def image_callback(self, msg):
        try:
            # compression_format = msg.format
            # print(compression_format)
            # Convert ROS Image message to OpenCV image
            cv_image = bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")  # Adjust the encoding type as per your image format
            cv_image = cv.rotate(cv_image, cv.ROTATE_180)

            # # Display the image (livestream locally)
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
                    .output(stream_url, format='flv', vcodec='libx264', pix_fmt='yuv420p', preset='ultrafast', tune='zerolatency', b='3M')
                    .overwrite_output()
                    .run_async(pipe_stdin=True)
                )

            # Write the frame bytes to the subprocess pipe
            self.ffmpeg_process.stdin.write(img_bytes)

        except Exception as e:
            print(e)

def main(args=None):
    rclpy.init(args=args)
    node = CvTest()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()