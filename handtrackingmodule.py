import mediapipe as mp
import cv2 as cv


class handDetector:
    def __init__(self, mode=False, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mode = mode
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.mpHand = mp.solutions.hands
        self.hands = self.mpHand.Hands(
            static_image_mode=self.mode, 
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        self.mpDraw = mp.solutions.drawing_utils
        
        

    def findshands(self,img,draw=True):
        
        imgRGB = cv.cvtColor(img,cv.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img,handLms,self.mpHand.HAND_CONNECTIONS)
        return img

    def findPosition(self,img,handNo=0,draw = True):
        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id,lm in enumerate(myHand .landmark):
                # print(id,lm)
                h,w,c = img.shape
                cx, cy = int(lm.x*w),int(lm.y*h)
                # print(id,cx,cy) 
                lmList.append([id,cx,cy])
                if draw:
                    cv.circle(img,(cx,cy),10,(255,0,255),cv.FILLED)
            
        return lmList
    
    
    
def main():
    cap = cv.VideoCapture(0)
    detector = handDetector()
    
    while True:
        success,img = cap.read()    
        img = detector.findshands(img)
        lmList = detector.findPosition(img)
        
        if len(lmList) != 0:
            print(lmList[4])
        
        cv.imshow('Image',img)
        cv.waitKey(1)
    
    
    
if __name__ == "__main__":
    main()