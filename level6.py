import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import mediapipe as mp
import time
from level3 import show_result
try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False
class Level6_HandOpenClose:
    def __init__(self, hands_detector):
        self.hands_detector = hands_detector
        self.state = 0  
        self.sequence_count = 0
        self.total_sequences = 5
        self.last_state_change = time.time()
        self.completed = False
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def detect_hand_state(self, landmarks, w, h):
        index_tip = landmarks.landmark[8]
        thumb_tip = landmarks.landmark[4]
        dist = np.linalg.norm(
            np.array([index_tip.x * w, index_tip.y * h]) -
            np.array([thumb_tip.x * w, thumb_tip.y * h])
        )
        return "open" if dist > 60 else "closed"

    def update(self, img):
        if self.completed:
            cv2.putText(img, "Exercise Complete!", (150, 240), self.font, 1.2, (0, 255, 0), 3)
            return img

        h, w, _ = img.shape
        results = self.hands_detector.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        prompt = ["Open your hand", "Close your hand (make a fist)", "Open your hand again"]

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            hand_state = self.detect_hand_state(lm, w, h)
            
            if self.state == 0 and hand_state == "open":
                self.state = 1
                self.last_state_change = time.time()
            elif self.state == 1 and hand_state == "closed":
                self.state = 2
                self.last_state_change = time.time()
            elif self.state == 2 and hand_state == "open":
                self.sequence_count += 1
                self.state = 0
                self.last_state_change = time.time()
                if self.sequence_count >= self.total_sequences:
                    self.completed = True

        cv2.putText(img, f"Step: {prompt[self.state]}", (10, 30), self.font, 1, (0, 255, 255), 2)
        cv2.putText(img, f"Reps: {self.sequence_count}/{self.total_sequences}", (10, 70), self.font, 1, (255, 255, 255), 2)

        return img

    def is_level_complete(self):
        return self.completed

def run_level6(root, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    game = Level6_HandOpenClose(hands)

    def update():
        success, frame = cap.read()
        if not success:
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

        frame = game.update(frame)

        # Collect index position for metrics
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
            cap.release()
            hands.close()
            try:
                smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                globals()['logger'].log_session(level=6, duration_s=0.0, score=100.0, smoothness=smooth, grasp_quality=0.0, notes='Level6 complete')
            except Exception:
                pass
            show_result(root, 100.0, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback)
        else:
            root.after(10, update)

    update()
