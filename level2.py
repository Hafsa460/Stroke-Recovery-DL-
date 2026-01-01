import cv2
import numpy as np
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
from level3 import show_result
import os
from smoothing_utils import ExponentialSmoother

# Optional DL integration
try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False

# ------------------- Set paths relative to this script -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ball_path = os.path.join(BASE_DIR, 'ball.png')
box_path = os.path.join(BASE_DIR, 'box.png')
target_ball_path = os.path.join(BASE_DIR, 'ball.png')
target_box_path = os.path.join(BASE_DIR, 'box.png')

# Load images
ball_img = cv2.imread(ball_path, cv2.IMREAD_UNCHANGED)
box_img = cv2.imread(box_path, cv2.IMREAD_UNCHANGED)
target_img = cv2.imread(target_ball_path)
target_img1 = cv2.imread(target_box_path)

# Resize images
ball_img = cv2.resize(ball_img, (60, 60))
box_img = cv2.resize(box_img, (60, 60))
target_img = cv2.resize(target_img, (80, 80))
target_img1 = cv2.resize(target_img1, (80, 80))

# ------------------- Helper functions -------------------
def overlay_image(background, overlay, x, y):
    h, w = overlay.shape[:2]
    if x + w > background.shape[1] or y + h > background.shape[0] or x < 0 or y < 0:
        return background
    roi = background[y:y+h, x:x+w]
    overlay_img = overlay[:, :, :3]
    mask = overlay[:, :, 3:] / 255.0
    background[y:y+h, x:x+w] = (1.0 - mask) * roi + mask * overlay_img
    return background

def lerp(a, b, f):
    return int(a + (b - a) * f)

# ------------------- Main Level 2 function -------------------
def run_level2(root, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback):
    # Clear previous widgets
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()

    cap = cv2.VideoCapture(0)

    # -------- Initialize MediaPipe Hands --------
    mp_hands = mp.solutions.hands
    hands_module = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils
    # --------------------------------------------

    # Initial positions
    ball_pos = [50, 100]
    box_pos = [50, 300]
    target_ball_pos = [500, 100]
    target_box_pos = [500, 300]

    dragging_ball = False
    dragging_box = False
    ball_scored = False
    box_scored = False
    score = 0
    result_shown = False

    # ------------------- Update Loop -------------------
    def update():
        nonlocal ball_pos, box_pos, dragging_ball, dragging_box
        nonlocal ball_scored, box_scored, score, result_shown

        # Lazy init DL modules
        if DL_AVAILABLE and 'model_manager' not in globals():
            try:
                globals()['model_manager'] = DLModelManager('best.pt')
                globals()['metrics'] = MovementMetrics()
                globals()['logger'] = SessionLogger()
            except Exception:
                globals()['model_manager'] = None
                globals()['metrics'] = None
                globals()['logger'] = None
        # start session timer
        if DL_AVAILABLE and globals().get('metrics') is not None and globals()['metrics'].session_start is None:
            try:
                import time
                globals()['metrics'].start_session(time.time())
            except Exception:
                pass

        ret, frame = cap.read()
        if not ret:
            root.after(10, update)
            return

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # -------- Hand detection --------
        results = hands_module.process(rgb)
        index_finger_pos = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                index_tip = hand_landmarks.landmark[8]
                x = int(index_tip.x * w)
                y = int(index_tip.y * h)
                index_finger_pos = (x, y)

        # -------- Dragging logic --------
        if index_finger_pos:
            ix, iy = index_finger_pos
            if not ball_scored and abs(ix - ball_pos[0]) < 60 and abs(iy - ball_pos[1]) < 60:
                dragging_ball = True
            elif not box_scored and abs(ix - box_pos[0]) < 60 and abs(iy - box_pos[1]) < 60:
                dragging_box = True

            if dragging_ball:
                ball_pos[0] = lerp(ball_pos[0], ix - 30, 0.4)
                ball_pos[1] = lerp(ball_pos[1], iy - 30, 0.4)
                if DL_AVAILABLE and globals().get('metrics') is not None:
                    try:
                        globals()['metrics'].add_position(ball_pos[0], ball_pos[1])
                    except Exception:
                        pass
            if dragging_box:
                box_pos[0] = lerp(box_pos[0], ix - 30, 0.4)
                box_pos[1] = lerp(box_pos[1], iy - 30, 0.4)
                if DL_AVAILABLE and globals().get('metrics') is not None:
                    try:
                        globals()['metrics'].add_position(box_pos[0], box_pos[1])
                    except Exception:
                        pass
        else:
            dragging_ball = False
            dragging_box = False

        # -------- Draw target images --------
        frame[target_ball_pos[1]:target_ball_pos[1]+80, target_ball_pos[0]:target_ball_pos[0]+80] = target_img
        frame[target_box_pos[1]:target_box_pos[1]+80, target_box_pos[0]:target_box_pos[0]+80] = target_img1

        # -------- Score checking --------
        if not ball_scored and target_ball_pos[0] < ball_pos[0] < target_ball_pos[0] + 60 and \
           target_ball_pos[1] < ball_pos[1] < target_ball_pos[1] + 60:
            ball_scored = True
            score += 1
            if DL_AVAILABLE and globals().get('metrics') is not None:
                try:
                    import time
                    ts = time.time()
                    globals()['metrics'].add_grasp_event(True, ts=ts)
                    globals()['metrics'].record_first_success(ts)
                except Exception:
                    pass

        if not box_scored and target_box_pos[0] < box_pos[0] < target_box_pos[0] + 60 and \
           target_box_pos[1] < box_pos[1] < target_box_pos[1] + 60:
            box_scored = True
            score += 1
            if DL_AVAILABLE and globals().get('metrics') is not None:
                try:
                    import time
                    ts = time.time()
                    globals()['metrics'].add_grasp_event(True, ts=ts)
                    globals()['metrics'].record_first_success(ts)
                except Exception:
                    pass

        # -------- Overlay draggable images --------
        if not ball_scored:
            frame = overlay_image(frame, ball_img, ball_pos[0], ball_pos[1])
        if not box_scored:
            frame = overlay_image(frame, box_img, box_pos[0], box_pos[1])

        # -------- Check level completion --------
        if ball_scored and box_scored:
            cv2.putText(frame, "Level 2 Completed!", (150, 460), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            if not result_shown:
                result_shown = True
                cap.release()
                hands_module.close()
                # Log session
                try:
                    smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                    grasp = globals()['metrics'].grasp_quality() if globals().get('metrics') is not None else 0.0
                    reaction = globals()['metrics'].reaction_time() if globals().get('metrics') is not None else None
                    notes = 'Level2 complete'
                    if reaction is not None:
                        notes += f' | reaction_s:{reaction:.2f}'
                    globals()['logger'].log_session(level=2, duration_s=0.0, score=score, smoothness=smooth, grasp_quality=grasp, notes=notes)
                except Exception:
                    pass
                level_unlocked[3] = True
                show_result(root, 100, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback)
                return

        # -------- Draw score --------
        cv2.putText(frame, f"Score: {score}", (450, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        root.after(10, update)

    update()
