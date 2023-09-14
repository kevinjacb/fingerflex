import cv2 as cv
import numpy as np
import handgestures as hg
import mouse
from sympy import symbols, Eq, solve
import screeninfo
import time
import tkinter
import customtkinter
import threading
import traceback
import pyautogui
import os
from datetime import datetime

cap = cv.VideoCapture(2)

WIDTH = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
HEIGHT = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
RESIZE_BY = 1

enable_sys = False

traversed_points = []
last_click = -1
last_active = -1
drag_enabled = False
last_coordinates = [0,0]
screen_shot_frames = 0 # find how many frames with ss
without_ss_frames = 0 # find how many frames without ss

screen_shot_folder = "screenshots" # current folder as default

next_frame = None

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue") 
viewport_scaling = 1.18


last_key_press = 0
key_press_delay = 1.5

cursor = 1 # 1 for normal cursor/ 0 for presentation



def callback(result, frame):
    global traversed_points, next_frame, last_click, last_active, drag_enabled, last_coordinates,screen_shot_frames,without_ss_frames, last_key_press
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
                    click_pinch_dist = GestureHandler.getDistance(result.hand_landmarks[i][4], result.hand_landmarks[i][12]) # thumb and middle finger
                    drag_pinch_dist = GestureHandler.getDistance(result.hand_landmarks[i][4], result.hand_landmarks[i][8]) # thumb and index finger
                    # ref_dist = GestureHandler.getDistance(result.hand_landmarks[i][4], result.hand_landmarks[i][7])
                    thumb_size = GestureHandler.getDistance(result.hand_landmarks[i][4], result.hand_landmarks[i][3])  

                    if result.gestures[i][0].category_name != "Closed_Fist" and screen_shot_frames > 0: # handle frames inbetween where gesture detection goes wrong
                        without_ss_frames += 1
                        if without_ss_frames == 15:
                            screen_shot_frames = 0
                            without_ss_frames = 0

                    if result.gestures[i][0].category_name == "Open_Palm" and cursor:
                        cv.putText(frame, "Active", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        isActive = True
                        index = i
                    elif result.gestures[i][0].category_name == "Closed_Fist" and False:   # put apple vision pro to shame
                        cv.putText(frame, "Click", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        initiateClick = True
                        index = i
                    elif result.gestures[i][0].category_name == "Thumb_Up" and cursor:
                        cv.putText(frame, "Scroll Up", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        scroll_up = True
                        index = i
                    elif result.gestures[i][0].category_name == "Thumb_Down" and cursor:
                        cv.putText(frame, "Scroll Down", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        index = i
                        scroll_down = True  
                    elif result.gestures[i][0].category_name == "Closed_Fist": # screen shot gesture
                        screen_shot_frames += 1
                        if screen_shot_frames == 60:
                            print("Screenshoted")
                            screen_shot_frames = 0
                            without_ss_frames = 0

                            img = pyautogui.screenshot()
                            img = cv.cvtColor(np.array(img),cv.COLOR_RGB2BGR)

                            # Get current datetime
                            current_datetime = datetime.now()

                            # Get formatted datetime string
                            datetime_string = current_datetime.strftime("%Y-%m-%d %H-%M-%S")

                            # Save screenshot with datetime in the filename
                            datetime_string = f'{datetime_string}.png'
                            cv.imwrite(os.path.join(screen_shot_folder,datetime_string),img)

                        
                    elif drag_pinch_dist < thumb_size*0.85 and click_pinch_dist > thumb_size * 1.5 and cursor:
                        cv.putText(frame, "Drag", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        index = i
                        drag = True
                    elif click_pinch_dist < thumb_size*0.85 and cursor: # handle click using apple pro vision big deal gesture
                        '''landmarks ->  8(index)  as ref
                            landmarks -> 4(index), 12 as click                  
                        check if the index finger and thumb are close enough 
                        use depth of wrist to determine the closeness of the fingers
                        if yes, initiate click
                        ''' 
                        initiateClick = True
                        index = i
                if result.handedness[i][0].display_name == "Right" and  not cursor: # for presentation control
                    ''' keypoints 4, 3, and 2 should be in a straightline, and 
                    keypoints 5, 6, 7, and 8 should also be in a straightline,
                    keypoints 9, 10, 11, and 12 should be in a straightline,
                    first set should be perpendicular to the second for a valid gesture
                    '''
                    thumb_is_straight = GestureHandler.isStraightLine([result.hand_landmarks[i][4], result.hand_landmarks[i][3], result.hand_landmarks[i][2]])
                    index_is_straight = GestureHandler.isStraightLine([result.hand_landmarks[i][5], result.hand_landmarks[i][6], result.hand_landmarks[i][7], result.hand_landmarks[i][8]])
                    middle_is_straight = GestureHandler.isStraightLine([result.hand_landmarks[i][9], result.hand_landmarks[i][10], result.hand_landmarks[i][11], result.hand_landmarks[i][12]])
                    # print (thumb_is_straight, index_is_straight, middle_is_straight)
                    if thumb_is_straight and index_is_straight and middle_is_straight:
                        # get angle between the two lines
                        # print(GestureHandler.getAngle([result.hand_landmarks[i][4],result.hand_landmarks[i][2]],[result.hand_landmarks[i][5],result.hand_landmarks[i][8]]))
                        # print(GestureHandler.getAngle([result.hand_landmarks[i][4],result.hand_landmarks[i][2]],[result.hand_landmarks[i][9],result.hand_landmarks[i][12]]))
                        if GestureHandler.getAngle([result.hand_landmarks[i][4],result.hand_landmarks[i][2]],[result.hand_landmarks[i][5],result.hand_landmarks[i][8]]) > 70 \
                            and GestureHandler.getAngle([result.hand_landmarks[i][4],result.hand_landmarks[i][2]],[result.hand_landmarks[i][9],result.hand_landmarks[i][12]]) >70:
                            # check which direction the hand is pointing to
                            if result.hand_landmarks[i][2].x < result.hand_landmarks[i][8].x and result.hand_landmarks[i][2].x < result.hand_landmarks[i][12].x and \
                                time.time() - last_key_press > key_press_delay:
                                last_key_press = time.time()
                                cv.putText(frame, "Next", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                pyautogui.press('right')
                                print("Next")
                            elif result.hand_landmarks[i][2].x > result.hand_landmarks[i][8].x and result.hand_landmarks[i][2].x > result.hand_landmarks[i][12].x and \
                                time.time() - last_key_press > key_press_delay:
                                last_key_press = time.time()
                                cv.putText(frame, "Previous", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                pyautogui.press('left')
                                print("Previous")
                        

                elif result.handedness[i][0].display_name == "Left":
                    if result.gestures[i][0].category_name == "Thumbs_Up":
                        cv.putText(frame, "Scroll Up", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        scroll_up = True
                        index = i
                    elif result.gestures[i][0].category_name == "Thumbs_Down":
                        cv.putText(frame, "Scroll Down", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        index = i
                        scroll_down = True
                
                    

        if isActive or drag: # if active, draw the path
            if drag or isActive:
                landmarks = [result.hand_landmarks[index][2], result.hand_landmarks[index][5], result.hand_landmarks[index][9], result.hand_landmarks[index][13], result.hand_landmarks[index][17], result.hand_landmarks[index][0]]
                coordinates =  GestureHandler.getAvg(landmarks)
                last_coordinates = traversed_points[-1] if len(traversed_points) > 0 else [int(coordinates[0] * WIDTH), int(coordinates[1] * HEIGHT)]
                if drag and not drag_enabled:
                    drag_enabled = True
                elif not drag and drag_enabled:
                    drag_enabled = False
            last_active = time.time()

            # set traversed points as the average of landmarks 2,5.9.13,17 and 0
            # print([int(coordinates[0] * WIDTH), int(coordinates[1] * HEIGHT)])
            traversed_points.append([int(coordinates[0] * WIDTH), int(coordinates[1] * HEIGHT)])
            if len(traversed_points) > 10:
                traversed_points.pop(0)
            # for i in range(len(traversed_points)-1):
            #     cv.line(frame, (traversed_points[i][0],traversed_points[i][1]),( traversed_points[i+1][0], traversed_points[i+1][1]),(255,0,0), 5)
            # cv.putText(frame, "Active", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # handleMouseDrag(traversed_points[-2], traversed_points[-1])
            # print(traversed_points)
            if len(traversed_points) > 1:
                simpleMouseDrag(traversed_points[-2].copy(), traversed_points[-1].copy(),drag=drag_enabled)
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
        traceback.print_exc()
    finally:
        frame = GestureHandler.drawLandMarks(frame,  result)
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
    SCREEN_OFFSET = 2
    POINT_OFFSET = viewport_scaling 
    # prev_point = np.array(prev_point)/SCREEN_OFFSET
    # curr_point = np.array(curr_point)/SCREEN_OFFSET
    screenWidth, screenHeight = screeninfo.get_monitors()[0].width, screeninfo.get_monitors()[0].height
    prev_point[0] = max(prev_point[0] - WIDTH/2.5,0)*POINT_OFFSET
    prev_point[1] = max(prev_point[1] - HEIGHT/2.5,0)*POINT_OFFSET
    curr_point[0] = max(curr_point[0] - WIDTH/2.5,0)*POINT_OFFSET
    curr_point[1] = max(curr_point[1] - HEIGHT/2.5,0)*POINT_OFFSET
    #map the points to the screen size
    adjust = (1 -SCREEN_OFFSET)/2 * 0
    prev_point = (int(((prev_point[0] * screenWidth / WIDTH)*SCREEN_OFFSET) + screenWidth*adjust), int(((prev_point[1] * screenHeight/ HEIGHT)*SCREEN_OFFSET + screenHeight*adjust)))
    curr_point = (int(((curr_point[0] * screenWidth   / WIDTH)*SCREEN_OFFSET) + screenWidth*adjust), int(((curr_point[1] * screenHeight / HEIGHT)*SCREEN_OFFSET+ screenHeight*adjust)))

    # print("dragging from ", prev_point, " to ", curr_point, "") # debug
    #move the mouse
    if drag:
        mouse.drag(prev_point[0], prev_point[1],curr_point[0], curr_point[1], absolute=True, duration=0)
    else:
        mouse.move(curr_point[0], curr_point[1], absolute=True, duration=0)

def setupWindow():
    app = customtkinter.CTk()
    app.title("FingerFlex")
    app.geometry("500x200")
    app.grid_columnconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=1)
    app.grid_columnconfigure(2, weight=1)
    app.grid_columnconfigure(3, weight=1)
    app.grid_rowconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=1)
    app.grid_rowconfigure(2, weight=1)

    switch = customtkinter.CTkSwitch(app, text="Enable Vision", command=toggleVision)
    switch.grid(row=0, column=0, rowspan=2, columnspan=2, sticky='')

    def toggleMode():
        global cursor
        cursor = 1 -cursor
        mode_switch.configure(text="Cursor Mode" if  cursor else "Presentation Mode")

    mode_switch = customtkinter.CTkSwitch(app,text="Cursor Mode" if  cursor else "Presentation Mode",command=toggleMode)
    mode_switch.grid(row=1,column=0,rowspan=2,columnspan=2,sticky='')

    # Slider current values
    sense_value = customtkinter.DoubleVar()
    viewport_value = customtkinter.DoubleVar(value=viewport_scaling)

    def get_current_value(arg):
        global viewport_scaling, sense
        if arg == 1:
            sense = round(float(sense_value.get()), 2)
            return sense
        elif arg == 2:
            viewport_scaling  = round(float(viewport_value.get()), 2)
            return viewport_scaling 

    def slider_changed(arg):
        if arg == 1:
            value_label.configure(text=get_current_value(1))
        elif arg == 2:
            value_label2.configure(text=get_current_value(2))

    # Label for the slider
    slider_label = customtkinter.CTkLabel(
        app,
        text='Sensitivity : '
    )
    slider_label.grid(
        column=2,
        row=0,
        sticky='se',
    )

    slider = customtkinter.CTkSlider(master=app,
                                     width=160,
                                     height=16,
                                     border_width=5.5,
                                     command=lambda event: slider_changed(1),
                                     variable=sense_value)

    slider.grid(
        column=2,
        row=1,
        columnspan=2,
        sticky='n',
    )

    # Value label
    value_label = customtkinter.CTkLabel(
        app,
        text=get_current_value(1)
    )
    value_label.grid(
        row=0,
        column=3,
        sticky='sw',
    )

    slider_label2 = customtkinter.CTkLabel(
        app,
        text='Viewport : '
    )
    slider_label2.grid(
        column=2,
        row=1,
        sticky='se',
    )

    slider2 = customtkinter.CTkSlider(master=app,
                                      width=160,
                                      height=16,
                                      border_width=5.5,
                                      from_ = 0,
                                      to = 5,
                                      command=lambda event: slider_changed(2),
                                      variable=viewport_value)

    slider2.grid(
        column=2,
        row=2,
        columnspan=2,
        sticky='n',
    )

    # Value label
    value_label2 = customtkinter.CTkLabel(
        app,
        text=get_current_value(2)
    )
    value_label2.grid(
        row=1,
        column=3,
        sticky='sw',
    )

    app.mainloop()



def toggleVision():
    global enable_sys
    enable_sys = not enable_sys

if __name__ == "__main__":

    if not os.path.exists(screen_shot_folder): # create screen shots folder if not exists
        os.mkdir(screen_shot_folder)

    threading.Thread(target=setupWindow).start()
 
    while True:
        isActive = False # True if the active hand is facing the camera
        ret, frame = cap.read()

        # resize frame
        frame = cv.resize(frame, (int(WIDTH/RESIZE_BY),int( HEIGHT/RESIZE_BY)), interpolation=cv.INTER_AREA)

        frame = cv.flip(frame, 1) # flip the frame horizontally

        if not ret:
            break

        if enable_sys:
            GestureHandler.getLandmarksNGesture(cv.cvtColor(frame,cv.COLOR_BGR2RGB)) # get the landmarks from the active hand
        
        if next_frame is not None:
            cv.imshow("frame", cv.cvtColor(next_frame,cv.COLOR_RGB2BGR)) 
            next_frame = None  

        if cv.waitKey(10) & 0xFF == 27:
            break
        
    cap.release()
    cv.destroyAllWindows()
