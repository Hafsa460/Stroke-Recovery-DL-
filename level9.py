import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
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


def run_level9(root, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()
    label = tk.Label(root, text="Place your hand in the correct zone when prompted", font=("Arial", 14))
    label.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    zones = {'left': (120, 240), 'right': (520, 240)}
    current_target = 'left'
    correct = 0
    attempts = 6

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
        nonlocal current_target, correct
        ret, frame = cap.read()
        if not ret:
            root.after(10, update)
            return
        frame = cv2.flip(frame, 1)
        init_dl()
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        # draw zones
        cv2.circle(frame, zones['left'], 60, (255, 0, 0), 2)
        cv2.putText(frame, 'LEFT', (zones['left'][0]-30, zones['left'][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
        cv2.circle(frame, zones['right'], 60, (0, 255, 0), 2)
        cv2.putText(frame, 'RIGHT', (zones['right'][0]-30, zones['right'][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.putText(frame, f'Target: {current_target.upper()}  {correct}/{attempts}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0]
            ix = int(lm.landmark[8].x * w)
            iy = int(lm.landmark[8].y * h)
            if globals().get('metrics') is not None:
                try:
                    globals()['metrics'].add_position(ix, iy)
                except Exception:
                    pass
            # check zone
            dist_left = ((ix - zones['left'][0])**2 + (iy - zones['left'][1])**2)**0.5
            dist_right = ((ix - zones['right'][0])**2 + (iy - zones['right'][1])**2)**0.5
            chosen = 'left' if dist_left < dist_right else 'right'
            if chosen == current_target:
                correct += 1
                current_target = 'right' if current_target == 'left' else 'left'

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
