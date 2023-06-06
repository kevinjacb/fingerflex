import cv2 as cv
import numpy as np
import handgestures as hg
import mouse
from sympy import symbols, Eq, solve
import screeninfo
import time

cap = cv.VideoCapture(0)

WIDTH = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
HEIGHT = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
RESIZE_BY = 1

traversed_points = []
last_click = -1
last_active = -1
drag_enabled = False
last_coordinates = [0,0]

next_frame = None

def callback(result, frame):
    global traversed_points, next_frame, last_click, last_active, drag_enabled, last_coordinates
    #hand index
    index = -1
    isActive = False
    initiateClick = False
    drag = False
    scroll_up = False
    scroll_down = False

    try:
    #get handedness from result
        if result.hand_landmarks: #get the landmarks from the active hand
            for i,handLms in enumerate(result.hand_landmarks):
                if result.handedness[i][0].display_name == "Right" and handLms[2].x < handLms[17].x:
                    if result.gestures[i][0].category_name == "Open_Palm":
                        isActive = True
                        index = i
                    elif result.gestures[i][0].category_name == "Closed_Fist":
                        initiateClick = True
                        index = i
                    elif result.gestures[i][0].category_name == "Victory":
                        index = i
                        drag = True
                    elif result.gestures[i][0].category_name == "Thumb_Up":
                        scroll_up = True
                        index = i
                    elif result.gestures[i][0].category_name == "Thumb_Down":
                        index = i
                        scroll_down = True

        if isActive or drag: # if active, draw the path
            if drag or isActive:
                last_coordinates = traversed_points[-1] if len(traversed_points) > 0 else [0,0]
                if drag and not drag_enabled:
                    drag_enabled = True
                elif not drag and drag_enabled:
                    drag_enabled = False
            last_active = time.time()
            traversed_points.append([int(result.hand_landmarks[index][8].x * WIDTH), int(result.hand_landmarks[0][8].y * HEIGHT)])
            if len(traversed_points) > 10:
                traversed_points.pop(0)
            for i in range(len(traversed_points)-1):
                cv.line(frame, (traversed_points[i][0],traversed_points[i][1]),( traversed_points[i+1][0], traversed_points[i+1][1]),(255,0,0), 5)
            cv.putText(frame, "Active", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # handleMouseDrag(traversed_points[-2], traversed_points[-1])
            if len(traversed_points) > 1:
                simpleMouseDrag(last_coordinates, traversed_points[-1],drag=drag_enabled)
        elif scroll_up:
            mouse.wheel(10)
        elif scroll_down:
            mouse.wheel(-10)
        elif initiateClick and time.time() - last_click > 1:
            mouse.click('left')
            last_click = time.time()
        elif not isActive and time.time() - last_active > 5: # if not active, clear the prev path
            traversed_points = []
        # print(traversed_points,'\n')
    except Exception as e:
        print("Error occured ",e)
    finally:
        next_frame = frame

GestureHandler = hg.GestureHandler(callback=callback)


def handleMouseDrag(prev_point, curr_point): 
    '''SOLUTION USING TRIGONOMETRY'''
    #TODO
    curr_mouse_pos = mouse.get_position()
    slope = (curr_point[1] - prev_point[1]) / (curr_point[0] - prev_point[0]) # slope of the line
    magnitude = np.sqrt((curr_point[1] - prev_point[1])**2 + (curr_point[0] - prev_point[0])**2) # distance between the two points

    next_x, next_y = -1,-1
    # solve for the next mouse point
    x = symbols('x')
    solve_for_x = Eq((x - curr_mouse_pos[0])**2 + (slope*(x - curr_mouse_pos[0]) + curr_mouse_pos[1])**2, magnitude**2)
    solutions = solve(solve_for_x)
    
    # select appropriate solution
    for soln in solutions:
        if soln > curr_mouse_pos[0] and soln < WIDTH:
            next_x = soln
            break

    next_y = slope*(next_x - curr_mouse_pos[0]) + curr_mouse_pos[1]
    mouse.move(next_x, next_y, absolute=True, duration=0.1)

def simpleMouseDrag(prev_point, curr_point, drag = False):
    screenWidth, screenHeight = screeninfo.get_monitors()[0].width, screeninfo.get_monitors()[0].height

    #map the points to the screen size
    prev_point = (int(prev_point[0] * screenWidth / WIDTH), int(prev_point[1] * screenHeight / HEIGHT))
    curr_point = (int(curr_point[0] * screenWidth / WIDTH), int(curr_point[1] * screenHeight / HEIGHT))

    #move the mouse
    if drag:
        mouse.drag(prev_point[0], prev_point[1],curr_point[0], curr_point[1], absolute=True, duration=0)
    else:
        mouse.move(curr_point[0], curr_point[1], absolute=True, duration=0)

while True:
    isActive = False # True if the active hand is facing the camera
    ret, frame = cap.read()

    # resize frame
    frame = cv.resize(frame, (int(WIDTH/RESIZE_BY),int( HEIGHT/RESIZE_BY)), interpolation=cv.INTER_AREA)

    frame = cv.flip(frame, 1) # flip the frame horizontally

    if not ret:
        break

    GestureHandler.getLandmarksNGesture(cv.cvtColor(frame,cv.COLOR_BGR2RGB)) # get the landmarks from the active hand
    
    if next_frame is not None:
        cv.imshow("frame", cv.cvtColor(next_frame,cv.COLOR_RGB2BGR)) 
        next_frame = None  

    if cv.waitKey(10) & 0xFF == 27:
        break

cap.release()
cv.destroyAllWindows()
