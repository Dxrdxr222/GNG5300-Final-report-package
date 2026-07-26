# motion_api.py

import cv2


class MotionAPI:
    def __init__(self):
        self.previous_gray = None

    def estimate_motion(self, frame):
        """
        Estimate visual motion by comparing current frame with previous frame.

        Return:
            motion_score between 0 and 1

        Example:
            0.00 = almost no motion
            0.10 = about 10% of pixels changed
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous_gray is None:
            self.previous_gray = gray
            return 0.0

        frame_delta = cv2.absdiff(self.previous_gray, gray)

        _, thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)

        changed_pixels = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]

        motion_score = changed_pixels / total_pixels

        self.previous_gray = gray

        return motion_score