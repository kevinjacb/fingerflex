import cv2 as cv
import numpy as np
import mediapipe as mp
from mediapipe import solutions
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
import os
import time

class GestureHandler:

    mp_hands = mp.solutions.hands

    BaseOptions = mp.tasks.BaseOptions
    GestureRecognizer = mp.tasks.vision.GestureRecognizer
    GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
    GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
    VisionRunningMode = mp.tasks.vision.RunningMode

        
    MARGIN = 10  # pixels
    FONT_SIZE = 1
    FONT_THICKNESS = 1
    HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green




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

    # def drawLandMarks(self,frame,hand_landmarks):
    #     '''draw the landmarks in the frame and connect the points with lines'''
    #     mp.solutions.drawing_utils.draw_landmarks(
    #         frame, hand_landmarks, GestureHandler.mp_hands.HAND_CONNECTIONS)
    #     return frame
    
    def drawLandMarks(self,rgb_image, detection_result):
        hand_landmarks_list = detection_result.hand_landmarks
        handedness_list = detection_result.handedness
        annotated_image = np.copy(rgb_image)

        # Loop through the detected hands to visualize.
        for idx in range(len(hand_landmarks_list)):
            hand_landmarks = hand_landmarks_list[idx]
            handedness = handedness_list[idx]

            # Draw the hand landmarks.
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
            ])
            solutions.drawing_utils.draw_landmarks(
            annotated_image,
            hand_landmarks_proto,
            solutions.hands.HAND_CONNECTIONS,
            solutions.drawing_styles.get_default_hand_landmarks_style(),
            solutions.drawing_styles.get_default_hand_connections_style())

            # Get the top left corner of the detected hand's bounding box.
            height, width, _ = annotated_image.shape
            x_coordinates = [landmark.x for landmark in hand_landmarks]
            y_coordinates = [landmark.y for landmark in hand_landmarks]
            text_x = int(min(x_coordinates) * width)
            text_y = int(min(y_coordinates) * height) - GestureHandler.MARGIN

            # Draw handedness (left or right hand) on the image.
            cv.putText(annotated_image, f"{handedness[0].category_name}",
                        (text_x, text_y), cv.FONT_HERSHEY_DUPLEX,
                        GestureHandler.FONT_SIZE,GestureHandler.HANDEDNESS_TEXT_COLOR, GestureHandler.FONT_THICKNESS, cv.LINE_AA)

        return annotated_image
    

    def getLandmarksNGesture(self, frame):
        self.frame = frame
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(frame,dtype=np.uint8))
        self.gesture_recognizer.recognize_async(mp_image, int(time.time()*1000))
