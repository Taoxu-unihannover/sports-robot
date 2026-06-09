import mujoco
import numpy as np


class MuJoCoCameraAdapter:
    def __init__(self, model, data, width=640, height=480, camera_name=None):
        self.model = model
        self.data = data
        self.width = width
        self.height = height
        self.renderer = mujoco.Renderer(model, height=height, width=width)
        self.camera_name = camera_name

    def capture(self):
        if self.camera_name:
            self.renderer.update_scene(self.data, camera_id=self.camera_name)
        else:
            self.renderer.update_scene(self.data)
        return self.renderer.render()


class BallDetector:
    def __init__(self, ball_hsv_low=None, ball_hsv_high=None):
        self.ball_hsv_low = ball_hsv_low or np.array([30, 100, 100])
        self.ball_hsv_high = ball_hsv_high or np.array([60, 255, 255])

    def detect(self, image):
        try:
            import cv2
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            mask = cv2.inRange(hsv, self.ball_hsv_low, self.ball_hsv_high)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                    return (cx, cy, 1.0)
        except ImportError:
            pass
        return (0.0, 0.0, 0.0)


class VisionStateAdapter:
    def __init__(self, detector=None, camera_adapter=None):
        self.detector = detector or BallDetector()
        self.camera = camera_adapter

    def get_observation(self):
        if self.camera is None:
            return np.zeros(2)
        image = self.camera.capture()
        detection = self.detector.detect(image)
        return np.array([detection[0], detection[1]])
