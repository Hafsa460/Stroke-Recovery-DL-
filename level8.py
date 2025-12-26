import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import random
import time
# Optional DL integration
try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False
from level3 import show_result


def run_level8(root, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()
    label = tk.Label(root, text="Touch the targets that appear", font=("Arial", 14))
    label.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    targets_required = 8
    targets_hit = 0
    target = (random.randint(80, 560), random.randint(80, 400))
    target_radius = 35
    last_change = time.time()

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
        nonlocal targets_hit, target, last_change
        ret, frame = cap.read()
        if not ret:
            root.after(10, update)
            return
        frame = cv2.flip(frame, 1)
        init_dl()
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0]
            ix = int(lm.landmark[8].x * w)
            iy = int(lm.landmark[8].y * h)
            if globals().get('metrics') is not None:
                try:
                    globals()['metrics'].add_position(ix, iy)
                except Exception:
                    pass
            dist = ((ix - target[0]) ** 2 + (iy - target[1]) ** 2) ** 0.5
            if dist < target_radius:
                targets_hit += 1
                target = (random.randint(80, 560), random.randint(80, 400))
                last_change = time.time()

        # draw target
        cv2.circle(frame, target, target_radius, (0, 0, 255), -1)
        cv2.putText(frame, f'{targets_hit}/{targets_required}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        if targets_hit >= targets_required:
            cap.release()
            hands.close()
            try:
                smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                score = min(100.0, (targets_hit / targets_required) * 100.0)
                globals()['logger'].log_session(level=8, duration_s=0.0, score=score, smoothness=smooth, grasp_quality=0.0, notes=f'Level8 targets:{targets_hit}/{targets_required}')
            except Exception:
                pass
            level_unlocked[8] = True
            show_result(root, score, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback)
        else:
            root.after(10, update)

    update()
