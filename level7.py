import cv2
import mediapipe as mp
import numpy as np
import math
import tkinter as tk
from PIL import Image, ImageTk
import random
import time
from level3 import show_result
from smoothing_utils import ExponentialSmoother
# Optional DL integration
try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False

def run_level7(root, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback):
    
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()
    label_stats = tk.Label(root, text="", font=("Arial", 14))
    label_stats.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    prev_x, prev_y = 0, 0
    ball_pos = [300, 300]
    target_pos = [random.randint(100, 540), random.randint(100, 380)]
    score = 0
    grabbed = False
    placed_balls = 0
    placements_required = 10

    def get_target_radius(level):
        return max(30 - level * 2, 10)

    def update():
        nonlocal prev_x, prev_y, ball_pos, target_pos, score, grabbed, placed_balls

        # Initialize DL components lazily
        if DL_AVAILABLE and 'model_manager' not in globals():
            try:
                globals()['model_manager'] = DLModelManager('best.pt')
                globals()['metrics'] = MovementMetrics()
                globals()['logger'] = SessionLogger()
            except Exception:
                globals()['model_manager'] = None
                globals()['metrics'] = None
                globals()['logger'] = None

        success, frame = cap.read()
        if not success:
            root.after(10, update)
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        h, w, _ = frame.shape

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            index_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]

            cx, cy = int(index_tip.x * w), int(index_tip.y * h)
            tx, ty = int(thumb_tip.x * w), int(thumb_tip.y * h)

            distance_pinch = math.hypot(cx - tx, cy - ty)
            is_grab = distance_pinch < 40

            if is_grab:
                if not grabbed and math.hypot(cx - ball_pos[0], cy - ball_pos[1]) < 40:
                    grabbed = True
            else:
                if grabbed:
                    grabbed = False
                    placement_error = math.hypot(ball_pos[0] - target_pos[0], ball_pos[1] - target_pos[1])
                    if placement_error < get_target_radius(7):
                        score += 1
                        placed_balls += 1
                        target_pos[:] = [random.randint(100, 540), random.randint(100, 380)]
                        ball_pos[:] = [300, 300]
                        prev_x, prev_y = ball_pos[0], ball_pos[1]
                    else:
                        prev_x, prev_y = ball_pos[0], ball_pos[1]

            if grabbed:
                smoothing_factor = 0.3
                ball_pos[0] = int(prev_x + smoothing_factor * (cx - prev_x))
                ball_pos[1] = int(prev_y + smoothing_factor * (cy - prev_y))
                prev_x, prev_y = ball_pos[0], ball_pos[1]
                # Track movement for metrics
                if DL_AVAILABLE and globals().get('metrics') is not None:
                    try:
                        globals()['metrics'].add_position(ball_pos[0], ball_pos[1])
                    except Exception:
                        pass

        cv2.circle(frame, tuple(target_pos), get_target_radius(7), (0, 0, 255), -1)
        cv2.circle(frame, tuple(ball_pos), 25, (0, 255, 0), -1)

        # Display counter at top
        cv2.putText(frame, f'Count: {placed_balls}/{placements_required}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

        stats_text = f"Placed: {placed_balls}/{placements_required}"
        label_stats.config(text=stats_text)

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        if placed_balls >= placements_required:
            cap.release()
            hands.close()
            try:
                smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                globals()['logger'].log_session(level=7, duration_s=0.0, score=100.0, smoothness=smooth, grasp_quality=0.0, notes=f'Level7 complete | placements:{placed_balls}/{placements_required}')
            except Exception:
                pass
            level_unlocked[8] = True
            show_result(root, 100.0, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback)
        else:
            root.after(10, update)

    update()