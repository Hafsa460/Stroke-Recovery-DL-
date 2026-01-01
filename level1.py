import tkinter as tk
from PIL import Image, ImageTk
import cv2
import mediapipe as mp
import time
import numpy as np
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
# ---------------- BalanceAndHold Class ---------------- #

class BalanceAndHold:
    def __init__(self, hold_time=5):
        self.hold_time = hold_time
        self.hold_start = None
        self.completed = False
        self.target_pos = (320, 240)
        self.radius = 30
        self.count = 0
        self.target_count = 1
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.smoother = ExponentialSmoother(alpha=0.7)  # Smoothing

    def update(self, img, hands_detector):
        h, w, _ = img.shape
        results = hands_detector.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        cv2.circle(img, self.target_pos, self.radius, (0, 255, 0), 2)
        
        # Display counter at top
        cv2.putText(img, f'Count: {self.count}/{self.target_count}', (10, 40), self.font, 1.2, (255, 255, 0), 3)

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            index_tip = lm.landmark[8]
            x = int(index_tip.x * w)
            y = int(index_tip.y * h)
            
            # Apply smoothing
            x, y = self.smoother.smooth(x, y)
            x, y = int(x), int(y)
            
            cv2.circle(img, (x, y), 8, (255, 255, 255), -1)
            cv2.putText(img, f'Pinch and hold inside the circle', (10, 80), self.font, 0.8, (0, 255, 0), 2)
          
            dist = np.linalg.norm(np.array([x, y]) - np.array(self.target_pos))
            if dist < self.radius:
                if self.hold_start is None:
                    self.hold_start = time.time()
                elapsed = time.time() - self.hold_start
                cv2.putText(img, f'Holding... {int(elapsed)}s', (10, 120), self.font, 1, (0, 255, 0), 2)
                if elapsed >= self.hold_time:
                    # Completed one hold
                    self.count += 1
                    self.hold_start = None
                    if self.count >= self.target_count:
                        self.completed = True
            else:
                self.hold_start = None
        else:
            self.hold_start = None

        return img

    def is_level_complete(self):
        return self.completed


def run_level1(root, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)
    game = BalanceAndHold()

    def update():
        ret, frame = cap.read()
        if not ret:
            root.after(10, update)
            return
        frame = cv2.flip(frame, 1)
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

        frame = game.update(frame, hands)

        if DL_AVAILABLE and globals().get('metrics') is not None:
            try:
                res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if res.multi_hand_landmarks:
                    lm = res.multi_hand_landmarks[0]
                    h, w, _ = frame.shape
                    ix = int(lm.landmark[8].x * w)
                    iy = int(lm.landmark[8].y * h)
                    globals()['metrics'].add_position(ix, iy)
            except Exception:
                pass

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        if game.is_level_complete():
            level_unlocked[2] = True
            cap.release()
            hands.close()
            try:
                smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                globals()['logger'].log_session(level=1, duration_s=0.0, score=100.0, smoothness=smooth, grasp_quality=0.0, notes='Level1 complete')
            except Exception:
                pass
            show_result(root, 100.0, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback)
        else:
            root.after(10, update)

    update()



