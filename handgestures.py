import cv2 as cv
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import time

class GestureHandler:

    # mp_hands = mp.solutions.hands

    BaseOptions = mp.tasks.BaseOptions
    GestureRecognizer = mp.tasks.vision.GestureRecognizer
    GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
    GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
    VisionRunningMode = mp.tasks.vision.RunningMode




    def __init__(self,callback) -> None:
        # self.hands = GestureHandler.mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        model_path = os.path.abspath('gesture_recognizer.task')
        base_options = GestureHandler.BaseOptions(model_asset_buffer=bytes(open(model_path, 'rb').read()))
        options = GestureHandler.GestureRecognizerOptions(base_options=base_options, running_mode=GestureHandler.VisionRunningMode.LIVE_STREAM, result_callback=self.print_result)
        self.gesture_recognizer = GestureHandler.GestureRecognizer.create_from_options(options)
        self.callback = callback
        self.frame = None

    def print_result(self,result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        self.callback(result,self.frame)

    def getLandmarksNGesture(self, frame):
        self.frame = frame
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(frame,dtype=np.uint8))
        self.gesture_recognizer.recognize_async(mp_image, int(time.time()*1000))
