import cv2 as cv
import numpy as np
import mediapipe as mp

cap = cv.VideoCapture(0)

mpHands = mp.solutions.hands # mediapipe hands module
hands = mpHands.Hands(static_image_mode=False, max_num_hands=2,
                      min_detection_confidence=0.5, min_tracking_confidence=0.5)
mpDraw = mp.solutions.drawing_utils 

WIDTH = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
HEIGHT = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

traversed_points = []

while True:
    isActive = False # True if the active hand is facing the camera
    ret, frame = cap.read()
    frame = cv.flip(frame, 1) # flip the frame horizontally

    if not ret:
        break

    frameRGB = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = hands.process(frameRGB) # inference

    if results.multi_hand_landmarks: #get the landmarks from the active hand
        for handLms in results.multi_hand_landmarks:
            if results.multi_handedness[0].classification[0].label == "Right" and handLms.landmark[2].x < handLms.landmark[17].x:
                isActive = True
            mpDraw.draw_landmarks(frame, handLms, mpHands.HAND_CONNECTIONS)

    if isActive: # if active, draw the path
        traversed_points.append([int(results.multi_hand_landmarks[0].landmark[8].x * WIDTH), int(results.multi_hand_landmarks[0].landmark[8].y * HEIGHT)])
        if len(traversed_points) > 10:
            traversed_points.pop(0)
        for i in range(len(traversed_points)-1):
            cv.line(frame, (traversed_points[i][0],traversed_points[i][1]),( traversed_points[i+1][0], traversed_points[i+1][1]),(255,0,0), 5)
        cv.putText(frame, "Active", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else: # if not active, clear the prev path
        traversed_points = []
    cv.imshow("frame", frame)


    if cv.waitKey(10) & 0xFF == 27:
        break

cap.release()
cv.destroyAllWindows()
