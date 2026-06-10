"""
HSV Quickstart — Interactive HSV color calibration and detection

Usage:
    python detect_hsv.py --image /path/to/image.jpg
    python detect_hsv.py --video /path/to/video.mp4
"""

import argparse
from typing import Optional, Tuple

import cv2
import numpy as np

from detector import HSVColorDetector, DetectionResult


DEFAULT_LOWER = (10, 100, 100)
DEFAULT_UPPER = (25, 255, 255)
WINDOW_NAME = "HSV Ball Detector - Calibration"


def interactive_calibrate(image: np.ndarray) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    lower = list(DEFAULT_LOWER)
    upper = list(DEFAULT_UPPER)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    def on_trackbar(val):
        pass

    cv2.createTrackbar("H_min", WINDOW_NAME, lower[0], 179, on_trackbar)
    cv2.createTrackbar("S_min", WINDOW_NAME, lower[1], 255, on_trackbar)
    cv2.createTrackbar("V_min", WINDOW_NAME, lower[2], 255, on_trackbar)
    cv2.createTrackbar("H_max", WINDOW_NAME, upper[0], 179, on_trackbar)
    cv2.createTrackbar("S_max", WINDOW_NAME, upper[1], 255, on_trackbar)
    cv2.createTrackbar("V_max", WINDOW_NAME, upper[2], 255, on_trackbar)

    print("Adjust HSV sliders to isolate the ball. Press 'q' to confirm.")

    while True:
        h_min = cv2.getTrackbarPos("H_min", WINDOW_NAME)
        s_min = cv2.getTrackbarPos("S_min", WINDOW_NAME)
        v_min = cv2.getTrackbarPos("V_min", WINDOW_NAME)
        h_max = cv2.getTrackbarPos("H_max", WINDOW_NAME)
        s_max = cv2.getTrackbarPos("S_max", WINDOW_NAME)
        v_max = cv2.getTrackbarPos("V_max", WINDOW_NAME)

        detector = HSVColorDetector(
            lower_hsv=(h_min, s_min, v_min),
            upper_hsv=(h_max, s_max, v_max),
        )

        display = image.copy()
        result = detector.detect(image)

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max]))
        mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        if result is not None:
            cx, cy = int(result.x), int(result.y)
            x1, y1, x2, y2 = int(result.bbox[0]), int(result.bbox[1]), int(result.bbox[2]), int(result.bbox[3])
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(display, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(display, f"conf: {result.confidence:.2f}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        combined = np.hstack([display, mask_colored])
        cv2.imshow(WINDOW_NAME, combined)

        if cv2.waitKey(30) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()

    final_lower = (
        cv2.getTrackbarPos("H_min", WINDOW_NAME),
        cv2.getTrackbarPos("S_min", WINDOW_NAME),
        cv2.getTrackbarPos("V_min", WINDOW_NAME),
    )
    final_upper = (
        cv2.getTrackbarPos("H_max", WINDOW_NAME),
        cv2.getTrackbarPos("S_max", WINDOW_NAME),
        cv2.getTrackbarPos("V_max", WINDOW_NAME),
    )

    return final_lower, final_upper


def detect_image(image_path: str, calibrate: bool = False):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Cannot load image: {image_path}")
        return

    if calibrate:
        lower, upper = interactive_calibrate(image)
        print(f"\nCalibrated HSV range:")
        print(f"  lower_hsv = {lower}")
        print(f"  upper_hsv = {upper}")
    else:
        lower, upper = DEFAULT_LOWER, DEFAULT_UPPER

    detector = HSVColorDetector(lower_hsv=lower, upper_hsv=upper)
    result = detector.detect(image)

    if result:
        print(f"Detected: center=({result.x:.1f}, {result.y:.1f}), confidence={result.confidence:.2f}")
    else:
        print("No ball detected")


def detect_video(video_path: str, calibrate: bool = False):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open video: {video_path}")
        return

    ret, first_frame = cap.read()
    if not ret:
        print("Cannot read video")
        return

    if calibrate:
        lower, upper = interactive_calibrate(first_frame)
        print(f"Calibrated HSV range: lower={lower}, upper={upper}")
    else:
        lower, upper = DEFAULT_LOWER, DEFAULT_UPPER

    detector = HSVColorDetector(lower_hsv=lower, upper_hsv=upper)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result = detector.detect(frame)
        if result:
            cx, cy = int(result.x), int(result.y)
            x1, y1, x2, y2 = int(result.bbox[0]), int(result.bbox[1]), int(result.bbox[2]), int(result.bbox[3])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

        cv2.imshow("HSV Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="HSV ball detection")
    parser.add_argument("--image", type=str, help="Input image path")
    parser.add_argument("--video", type=str, help="Input video path")
    parser.add_argument("--calibrate", action="store_true", help="Interactive calibration mode")
    args = parser.parse_args()

    if args.image:
        detect_image(args.image, args.calibrate)
    elif args.video:
        detect_video(args.video, args.calibrate)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
