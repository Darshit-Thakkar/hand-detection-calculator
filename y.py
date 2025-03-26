import cv2
import mediapipe as mp
import pyautogui
import numpy as np

# Initialize video capture and hand detector
cap = cv2.VideoCapture(0)
hand_detector = mp.solutions.hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)
drawing_utils = mp.solutions.drawing_utils
screen_width, screen_height = pyautogui.size()

# Variables for smoothing movement
prev_index_x, prev_index_y = 0, 0
smooth_factor = 3  # Controls movement smoothness

while True:
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    output = hand_detector.process(rgb_frame)
    hands = output.multi_hand_landmarks

    if hands:
        for hand in hands:
            drawing_utils.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
            landmarks = hand.landmark
            
            # Extract index finger tip and thumb tip coordinates
            index_finger = landmarks[8]
            thumb_finger = landmarks[4]

            index_x = int(index_finger.x * frame_width)
            index_y = int(index_finger.y * frame_height)
            thumb_x = int(thumb_finger.x * frame_width)
            thumb_y = int(thumb_finger.y * frame_height)

            # Draw circles on index finger tip and thumb tip
            cv2.circle(frame, (index_x, index_y), 10, (0, 255, 0), -1)  # Green for index
            cv2.circle(frame, (thumb_x, thumb_y), 10, (0, 0, 255), -1)  # Red for thumb

            # Map coordinates to screen size
            screen_x = np.interp(index_x, (0, frame_width), (0, screen_width))
            screen_y = np.interp(index_y, (0, frame_height), (0, screen_height))

            # Smooth movement by averaging previous positions
            curr_index_x = (prev_index_x * (smooth_factor - 1) + screen_x) / smooth_factor
            curr_index_y = (prev_index_y * (smooth_factor - 1) + screen_y) / smooth_factor

            # Move the cursor
            pyautogui.moveTo(curr_index_x, curr_index_y, duration=0.1)
            prev_index_x, prev_index_y = curr_index_x, curr_index_y

            # Check for click (distance between thumb and index tip)
            distance = np.hypot(thumb_x - index_x, thumb_y - index_y)
            if distance < 10:  # If fingers are very close, click
                pyautogui.click()
                pyautogui.sleep(0.5)  # Small delay to avoid multiple clicks

    # Display the frame
    cv2.imshow('Virtual Mouse', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
        break

cap.release()
cv2.destroyAllWindows()
