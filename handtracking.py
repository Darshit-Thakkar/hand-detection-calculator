import mediapipe as mp
import cv2 as cv
import time 

cap = cv.VideoCapture(0)
mpHand = mp.solutions.hands
hands = mpHand.Hands()
mpDraw = mp.solutions.drawing_utils


while True:
    success,img = cap.read()
    imgRGB = cv.cvtColor(img,cv.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    # print(results.multi_hand_landmarks)
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            for id,lm in enumerate(handLms.landmark):
                # print(id,lm)
                h,w,c = img.shape
                cx, cy = int(lm.x*w),int(lm.y*h)
                print(id,cx,cy)
                if id == 0:
                    cv.circle(img,(cx,cy),25,(255,0,255),cv.FILLED)
            mpDraw.draw_landmarks(img,handLms,mpHand.HAND_CONNECTIONS)

    
    cv.imshow('Image',img)
    cv.waitKey(1)