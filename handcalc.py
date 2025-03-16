import cv2 as cv
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import time
import sys
import pyttsx3

# Store operation records
operation_records = []
num1, num2 = 0, 0
detection_active = False  
detection_done = False  
detection_start_time = None  

# Initialize OpenCV capture
wCam, hCam = 640, 490
cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, wCam)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, hCam)

# Initialize Mediapipe Hand Detector
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.85, min_tracking_confidence=0.85, max_num_hands=2)

# Finger landmark indexes
tipIds = [4, 8, 12, 16, 20]

# Initialize Text-to-Speech engine
engine = pyttsx3.init()

# Create the main Tkinter window
root = tk.Tk()
root.title("Hand Detection & Number Entry Panel")
root.geometry("1000x600")

# Dark mode toggle state
dark_mode = False

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg_color = "#2E2E2E" if dark_mode else "lightgray"
    fg_color = "white" if dark_mode else "black"
    
    left_panel.config(bg=bg_color)
    right_panel.config(bg=bg_color)
    history_label.config(bg=bg_color, fg=fg_color)
    finger_count_label.config(bg=bg_color, fg=fg_color)
    toggle_mode_button.config(text="Light Mode" if dark_mode else "Dark Mode")
    finger_operations_label.config(bg=bg_color, fg=fg_color)
    finger_operations_text.config(bg=bg_color, fg=fg_color)

# Left Panel - Number Entry & Operations
left_panel = tk.Frame(root, width=400, height=600, bg="lightgray")
left_panel.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(left_panel, text="Enter First Number:", bg="lightgray").pack()
entry1 = tk.Entry(left_panel)
entry1.pack()

tk.Label(left_panel, text="Enter Second Number:", bg="lightgray").pack()
entry2 = tk.Entry(left_panel)
entry2.pack()

# Display operation history
history_label = tk.Label(left_panel, text="Task History:", bg="lightgray", font=("Helvetica", 12))
history_label.pack()

history_text = tk.Text(left_panel, height=10, width=40)
history_text.pack()

def update_history(new_record):
    """Updates the history panel and saves the record to a file."""
    if new_record not in operation_records:  # Prevent duplicates
        operation_records.append(new_record)  
        history_text.insert(tk.END, new_record + "\n")  
        with open("task_history.txt", "a") as file:
            file.write(new_record + "\n")

def submit_numbers():
    """Gets numbers from the entry fields and starts detection."""
    global num1, num2, detection_active, detection_start_time, detection_done
    try:
        num1 = int(entry1.get())
        num2 = int(entry2.get())
        detection_active = True  
        detection_start_time = time.time()  
        detection_done = False  
        finger_count_label.config(text="Detecting fingers...")  
        print(f"Numbers updated: {num1}, {num2}. Hand detection activated.")
    except ValueError:
        num1, num2 = 0, 0
        print("Invalid input. Please enter valid numbers.")

submit_button = tk.Button(left_panel, text="Submit", command=submit_numbers)
submit_button.pack()

# Right Panel - Hand Detection Display
right_panel = tk.Frame(root, width=600, height=600)
right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

video_label = tk.Label(right_panel)
video_label.pack()

finger_count_label = tk.Label(right_panel, text="Please click Submit to start detection", font=("Helvetica", 14))
finger_count_label.pack()

def hand_detection():
    """Detects the number of fingers and performs arithmetic operations."""
    global num1, num2, detection_active, detection_done, detection_start_time

    success, img = cap.read()
    if not success:
        return

    img = cv.flip(img, 1)  # Flip for mirror effect
    rgb_frame = cv.cvtColor(img, cv.COLOR_BGR2RGB)

    # Detect hands
    result = hands.process(rgb_frame)

    totalFingers = 0  

    if detection_active and detection_start_time is not None and not detection_done:
        elapsed_time = time.time() - detection_start_time

        if elapsed_time >= 2:  
            detection_active = False
            detection_done = True  
            finger_count_label.config(text="Please click Submit to continue")  
            print("Detection stopped after 2 seconds.")

        if result.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
                # Identify Left or Right Hand
                hand_type = result.multi_handedness[idx].classification[0].label  # 'Left' or 'Right'

                fingers = []

                # Thumb detection fix (for left and right hand)
                if hand_type == "Right":
                    if hand_landmarks.landmark[tipIds[0]].x < hand_landmarks.landmark[tipIds[0] - 1].x:
                        fingers.append(1)
                    else:
                        fingers.append(0)
                else:  
                    if hand_landmarks.landmark[tipIds[0]].x > hand_landmarks.landmark[tipIds[0] - 1].x:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                # Other four fingers detection
                for id in range(1, 5):
                    if hand_landmarks.landmark[tipIds[id]].y < hand_landmarks.landmark[tipIds[id] - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                totalFingers = fingers.count(1)
                cv.putText(img, f"Fingers: {totalFingers}", (10, 70), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                finger_count_label.config(text=f"Fingers Detected: {totalFingers}")

                # Perform arithmetic operation
                operation = "No operation performed."
                result_value = None

                if totalFingers == 1:
                    result_value = num1 + num2
                    operation = f"Addition: {num1} + {num2} = {result_value}"
                elif totalFingers == 2:
                    result_value = num1 - num2
                    operation = f"Subtraction: {num1} - {num2} = {result_value}"
                elif totalFingers == 3:
                    result_value = num1 * num2
                    operation = f"Multiplication: {num1} * {num2} = {result_value}"
                elif totalFingers == 4:
                    if num2 != 0:
                        result_value = num1 / num2
                        operation = f"Division: {num1} / {num2} = {result_value}"
                    else:
                        operation = "Division by zero is not allowed."

                if detection_done:
                    print(operation)
                    update_history(operation)
                    engine.say(operation)
                    engine.runAndWait()
    
    img = Image.fromarray(rgb_frame)
    img = ImageTk.PhotoImage(image=img)

    video_label.img = img
    video_label.config(image=img)
    video_label.after(10, hand_detection)

# Add Finger Operation List
finger_operations_label = tk.Label(left_panel, text="Finger Count Operations:", font=("Helvetica", 12, "bold"), bg="lightgray")
finger_operations_label.pack()

finger_operations_text = tk.Label(left_panel, text=(
    "1 Finger  → Addition (+)\n"
    "2 Fingers → Subtraction (-)\n"
    "3 Fingers → Multiplication (×)\n"
    "4 Fingers → Division (÷)\n"
), bg="lightgray", font=("Helvetica", 10), justify="left")
finger_operations_text.pack()

def quit_app():
    root.quit()
    cap.release()
    cv.destroyAllWindows()
    sys.exit()

quit_button = tk.Button(left_panel, text="Quit", command=quit_app)
quit_button.pack()

toggle_mode_button = tk.Button(left_panel, text="Dark Mode", command=toggle_dark_mode)
toggle_mode_button.pack()

hand_detection()
root.mainloop()
