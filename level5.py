import tkinter as tk
from PIL import Image, ImageTk
import cv2
import mediapipe as mp
import numpy as np
from level3 import show_result
class GripStrengthGame:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.grip_count = 0
        self.attempt_count = 0
        self.target_grips = 5
        self.completed = False
        self.grip_state = False 
        self.state_changed = False  

    def is_hand_closed(self, lm):
        wrist = np.array([lm.landmark[0].x, lm.landmark[0].y])
        
        fingertips_ids = [8, 12, 16, 20]  
        closed_fingers = 0
        
        for tip_id in fingertips_ids:
            tip = np.array([lm.landmark[tip_id].x, lm.landmark[tip_id].y])
            distance = np.linalg.norm(tip - wrist)
            if distance < 0.12:  
                closed_fingers += 1
        
        return closed_fingers >= 3  

    def update(self, img, hands_detector):
        h, w, _ = img.shape
        results = hands_detector.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            cx = int(lm.landmark[0].x * w)
            cy = int(lm.landmark[0].y * h)

            hand_closed = self.is_hand_closed(lm)

            if hand_closed and not self.grip_state:
                self.grip_count += 1
                self.attempt_count += 1
                self.grip_state = True
                self.state_changed = True
            elif not hand_closed and self.grip_state:
                self.grip_state = False
                self.state_changed = True

            if self.state_changed:
                self.state_changed = False

            color = (0, 255, 0) if hand_closed else (255, 255, 255)
            cv2.circle(img, (cx, cy), 50, color, -1)
            cv2.putText(img, f'Grips: {self.grip_count}/{self.target_grips}', (10, 40), self.font, 1, (0, 255, 255), 2)

            if self.grip_count >= self.target_grips:
                self.completed = True
                cv2.putText(img, 'Complete!', (10, 120), self.font, 1, (0, 255, 0), 3)

        return img

    def is_level_complete(self):
        return self.completed

    def get_accuracy(self):
        if self.attempt_count == 0:
            return 0
        return (self.grip_count / self.attempt_count) * 100



def run_game(root, GameClass, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)
    game = GameClass()

    def update():
        ret, frame = cap.read()
        if not ret:
            root.after(10, update)
            return

        frame = cv2.flip(frame, 1)
        frame = game.update(frame, hands)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk
        accuracy=5
        if game.is_level_complete():
            level_unlocked[6] = True
            cap.release()
            hands.close()
            show_result(root, 100.0, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback)
        else:
            root.after(10, update)

    update()