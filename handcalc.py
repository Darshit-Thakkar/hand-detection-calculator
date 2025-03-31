import cv2 as cv
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import time
import sys
import pyttsx3
import pyautogui
import numpy as np
import mysql.connector

operation_records = []
num1, num2 = 0, 0
detection_active = False
detection_done = False
detection_start_time = None

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root", 
        password="",
        database="hand_calculator"
    )
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            operation VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
except mysql.connector.Error as err:
    print(f"Error connecting to MySQL: {err}")
    db = None

wCam, hCam = 640, 490
cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, wCam)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, hCam)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.85, min_tracking_confidence=0.85, max_num_hands=2)

tipIds = [4, 8, 12, 16, 20]

engine = pyttsx3.init()

screen_width, screen_height = pyautogui.size()
prev_index_x, prev_index_y = 0, 0
smooth_factor = 3

root = tk.Tk()
root.title("Hand Gesture Calculator & Mouse Control")
root.geometry("1000x600")

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

left_panel = tk.Frame(root, width=400, height=600, bg="lightgray")
left_panel.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(left_panel, text="Enter First Number:", bg="lightgray").pack()
entry1 = tk.Entry(left_panel)
entry1.pack()

tk.Label(left_panel, text="Enter Second Number:", bg="lightgray").pack()
entry2 = tk.Entry(left_panel)
entry2.pack()

history_label = tk.Label(left_panel, text="Task History:", bg="lightgray", font=("Helvetica", 12))
history_label.pack()

history_text = tk.Text(left_panel, height=10, width=40)
history_text.pack()

def update_history(new_record):
    if new_record not in operation_records:
        operation_records.append(new_record)  
        history_text.insert(tk.END, new_record + "\n")
        
        with open("task_history.txt", "a") as file:
            file.write(new_record + "\n")
            
        if db is not None:
            try:
                sql = "INSERT INTO task_history (operation) VALUES (%s)"
                cursor.execute(sql, (new_record,))
                db.commit()
            except mysql.connector.Error as err:
                print(f"Error inserting into database: {err}")

def submit_numbers():
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

right_panel = tk.Frame(root, width=600, height=600)
right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

video_label = tk.Label(right_panel)
video_label.pack()

finger_count_label = tk.Label(right_panel, text="Please click Submit to start detection", font=("Helvetica", 14))
finger_count_label.pack()

numpad_frame = tk.Frame(right_panel)
numpad_frame.pack(side=tk.BOTTOM, pady=10)

def insert_number(num):
    if entry1.focus_get() == entry1:
        entry1.insert(tk.END, num)
    elif entry2.focus_get() == entry2:
        entry2.insert(tk.END, num)
    else:
        entry1.focus_set()
        entry1.insert(tk.END, num)

def clear_all():
    entry1.delete(0, tk.END)
    entry2.delete(0, tk.END)
    entry1.focus_set()
    history_text.delete(1.0, tk.END)
    operation_records.clear()
    
    open("task_history.txt", "w").close()
    
    if db is not None:
        try:
            cursor.execute("DELETE FROM task_history")
            db.commit()
            print("Database records cleared successfully")
        except mysql.connector.Error as err:
            print(f"Error clearing database records: {err}")

def erase_one():
    if entry1.focus_get() == entry1:
        if len(entry1.get()) > 0:
            entry1.delete(len(entry1.get())-1, tk.END)
    elif entry2.focus_get() == entry2:
        if len(entry2.get()) > 0:
            entry2.delete(len(entry2.get())-1, tk.END)

for i in range(10):
    btn = tk.Button(numpad_frame, text=str(i), width=5, height=2, command=lambda n=i: insert_number(n))
    btn.grid(row=(i-1)//3 if i!=0 else 3, column=(i-1)%3 if i!=0 else 1, padx=5, pady=5)

clear_btn = tk.Button(numpad_frame, text="AC", width=5, height=2, command=clear_all, bg="red", fg="white")
clear_btn.grid(row=3, column=0, padx=5, pady=5)

erase_btn = tk.Button(numpad_frame, text="⌫", width=5, height=2, command=erase_one, bg="orange")
erase_btn.grid(row=3, column=2, padx=5, pady=5)

def hand_detection():
    global num1, num2, detection_active, detection_done, detection_start_time
    global prev_index_x, prev_index_y

    success, img = cap.read()
    if not success:
        return

    img = cv.flip(img, 1)
    rgb_frame = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    frame_height, frame_width, _ = img.shape

    result = hands.process(rgb_frame)
    totalFingers = 0

    if result.multi_hand_landmarks:
        right_hand_idx = None
        if len(result.multi_hand_landmarks) > 1:
            for idx, handedness in enumerate(result.multi_handedness):
                if handedness.classification[0].label == "Right":
                    right_hand_idx = idx
                    break
        
        for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            if len(result.multi_hand_landmarks) == 1 or (right_hand_idx is not None and idx == right_hand_idx):
                index_finger = hand_landmarks.landmark[8]
                thumb_finger = hand_landmarks.landmark[4]
                
                index_x = int(index_finger.x * frame_width)
                index_y = int(index_finger.y * frame_height)
                thumb_x = int(thumb_finger.x * frame_width)
                thumb_y = int(thumb_finger.y * frame_height)

                cv.circle(img, (index_x, index_y), 10, (0, 255, 0), -1)
                cv.circle(img, (thumb_x, thumb_y), 10, (0, 0, 255), -1)

                screen_x = np.interp(index_x, (0, frame_width), (0, screen_width))
                screen_y = np.interp(index_y, (0, frame_height), (0, screen_height))
                
                curr_index_x = (prev_index_x * (smooth_factor - 1) + screen_x) / smooth_factor
                curr_index_y = (prev_index_y * (smooth_factor - 1) + screen_y) / smooth_factor
                
                pyautogui.moveTo(curr_index_x, curr_index_y, duration=0.1)
                prev_index_x, prev_index_y = curr_index_x, curr_index_y

                distance = np.hypot(thumb_x - index_x, thumb_y - index_y)
                if distance < 20:
                    pyautogui.click()
                    time.sleep(0.3)

            fingers = []
            hand_type = result.multi_handedness[idx].classification[0].label
            if hand_type == "Right":
                fingers.append(1 if hand_landmarks.landmark[tipIds[0]].x < hand_landmarks.landmark[tipIds[0] - 1].x else 0)
            else:
                fingers.append(1 if hand_landmarks.landmark[tipIds[0]].x > hand_landmarks.landmark[tipIds[0] - 1].x else 0)

            for id in range(1, 5):
                fingers.append(1 if hand_landmarks.landmark[tipIds[id]].y < hand_landmarks.landmark[tipIds[id] - 2].y else 0)

            if sum(fingers) == 0:
                clear_all()
                time.sleep(0.5)

            if detection_active and not detection_done:
                totalFingers = fingers.count(1)
                cv.putText(img, f"Fingers: {totalFingers}", (10, 70), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                finger_count_label.config(text=f"Fingers Detected: {totalFingers}")

    if detection_active and detection_start_time is not None and not detection_done:
        elapsed_time = time.time() - detection_start_time

        if elapsed_time >= 2:
            detection_active = False
            detection_done = True
            finger_count_label.config(text="Please click Submit to continue")
            
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
                    result_value = round(num1 / num2, 2)
                    operation = f"Division: {num1} / {num2} = {result_value}"
                else:
                    operation = "Division by zero is not allowed."

            print(operation)
            update_history(operation)
            engine.say(operation)
            engine.runAndWait()

    img = Image.fromarray(rgb_frame)
    img = ImageTk.PhotoImage(image=img)
    video_label.img = img
    video_label.config(image=img)
    video_label.after(10, hand_detection)

finger_operations_label = tk.Label(left_panel, text="Finger Count Operations:", font=("Helvetica", 12, "bold"), bg="lightgray")
finger_operations_label.pack()

finger_operations_text = tk.Label(left_panel, text=(
    "1 Finger  → Addition (+)\n"
    "2 Fingers → Subtraction (-)\n"
    "3 Fingers → Multiplication (×)\n"
    "4 Fingers → Division (÷)\n"
    "Fist      → Clear All\n"
), bg="lightgray", font=("Helvetica", 10), justify="left")
finger_operations_text.pack()

def quit_app():
    if db is not None:
        cursor.close()
        db.close()
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
