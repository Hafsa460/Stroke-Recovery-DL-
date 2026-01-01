import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import time
import random
import numpy as np
from smoothing_utils import ExponentialSmoother
# Optional DL integration
try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False
from level3 import show_result


def run_level9(root, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()
    label = tk.Label(root, text="Place your hand in the correct zone when prompted\n(Make a FIST in the RIGHT zone to confirm)", font=("Arial", 12))
    label.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    zones = {'left': (120, 240), 'right': (520, 240)}
    # Randomize sequence of left/right
    sequence = [random.choice(['left', 'right']) for _ in range(6)]
    current_index = 0
    correct = 0
    attempts = 6
    last_fist_time = 0

    def is_hand_closed(lm):
        """Detect if hand is in fist position"""
        wrist = np.array([lm.landmark[0].x, lm.landmark[0].y])
        fingertips_ids = [8, 12, 16, 20]  # index, middle, ring, pinky tips
        closed_fingers = 0
        
        for tip_id in fingertips_ids:
            tip = np.array([lm.landmark[tip_id].x, lm.landmark[tip_id].y])
            distance = np.linalg.norm(tip - wrist)
            if distance < 0.12:  # threshold for closed
                closed_fingers += 1
        
        return closed_fingers >= 3

    def init_dl():
        if DL_AVAILABLE and 'model_manager' not in globals():
            try:
                globals()['model_manager'] = DLModelManager('best.pt')
                globals()['metrics'] = MovementMetrics()
                globals()['logger'] = SessionLogger()
            except Exception:
                globals()['model_manager'] = None
                globals()['metrics'] = None
                globals()['logger'] = None

    def update():
        nonlocal current_index, correct, last_fist_time
        ret, frame = cap.read()
        if not ret:
            root.after(10, update)
            return
        frame = cv2.flip(frame, 1)
        init_dl()
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        current_target = sequence[current_index]

        # draw zones
        left_color = (0, 255, 0) if current_target == 'left' else (100, 100, 100)
        right_color = (0, 255, 0) if current_target == 'right' else (100, 100, 100)
        
        cv2.circle(frame, zones['left'], 60, left_color, 2)
        cv2.putText(frame, 'LEFT', (zones['left'][0]-30, zones['left'][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, left_color, 2)
        cv2.circle(frame, zones['right'], 60, right_color, 2)
        cv2.putText(frame, 'RIGHT', (zones['right'][0]-30, zones['right'][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, right_color, 2)
        
        cv2.putText(frame, f'Target: {current_target.upper()}  {correct}/{attempts}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(frame, f'Sequence: {" -> ".join(sequence)}', (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0]
            ix = int(lm.landmark[8].x * w)
            iy = int(lm.landmark[8].y * h)
            if globals().get('metrics') is not None:
                try:
                    globals()['metrics'].add_position(ix, iy)
                except Exception:
                    pass
            
            # Check zone distance
            dist_left = ((ix - zones['left'][0])**2 + (iy - zones['left'][1])**2)**0.5
            dist_right = ((ix - zones['right'][0])**2 + (iy - zones['right'][1])**2)**0.5
            chosen_zone = 'left' if dist_left < dist_right else 'right'
            
            # Check if hand is in target zone
            if chosen_zone == current_target:
                # For RIGHT zone: require fist gesture
                if current_target == 'right':
                    hand_closed = is_hand_closed(lm)
                    if hand_closed and (time.time() - last_fist_time > 0.5):
                        correct += 1
                        current_index += 1
                        last_fist_time = time.time()
                        cv2.putText(frame, '✓ CONFIRMED!', (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, 'Make a FIST to confirm', (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
                # For LEFT zone: just position
                else:
                    correct += 1
                    current_index += 1
                    cv2.putText(frame, '✓ CORRECT!', (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        if correct >= attempts:
            cap.release()
            hands.close()
            try:
                smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                score = min(100.0, (correct / attempts) * 100.0)
                globals()['logger'].log_session(level=9, duration_s=0.0, score=score, smoothness=smooth, grasp_quality=0.0, notes=f'Level9 correct:{correct}/{attempts}')
            except Exception:
                pass
            level_unlocked[9] = True
            show_result(root, score, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback)
        else:
            root.after(10, update)

    update()
