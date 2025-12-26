import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import mediapipe as mp
try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False


class Level3_ColorMatching:
    def __init__(self, hands_detector):
        self.hands_detector = hands_detector
        self.colors = ['red', 'green', 'blue']
        self.baskets = {}
        self.balls = []
        self.score = 0
        self.total = 6
        self.dragging = None
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.init_baskets_and_balls()

    def init_baskets_and_balls(self):
        start_y = 60
        spacing = 120
        for i, color in enumerate(self.colors):
            x1, y1 = 500, start_y + i * spacing
            self.baskets[color] = (x1, y1, x1 + 100, y1 + 100)

        positions = [(50, 80), (150, 80), (50, 200), (150, 200), (50, 320), (150, 320)]
        self.balls = []
        for i, color in enumerate(self.colors * 2):
            self.balls.append({'color': color, 'pos': list(positions[i]), 'placed': False, 'orig_pos': positions[i]})

    def get_bgr(self, color):
        return {'red': (0, 0, 255), 'green': (0, 255, 0), 'blue': (255, 0, 0)}.get(color, (255, 255, 255))

    def draw(self, img):
        for color, (x1, y1, x2, y2) in self.baskets.items():
            cv2.rectangle(img, (x1, y1), (x2, y2), self.get_bgr(color), 3)
        for ball in self.balls:
            if not ball['placed']:
                cv2.circle(img, tuple(ball['pos']), 30, self.get_bgr(ball['color']), -1)
        cv2.putText(img, f'Score: {self.score}/{self.total}', (10, 30), self.font, 1, (255, 255, 255), 2)

    def update(self, img):
        results = self.hands_detector.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        index_pos, thumb_pos = None, None
        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            h, w, _ = img.shape
            index_pos = (int(lm.landmark[8].x * w), int(lm.landmark[8].y * h))
            thumb_pos = (int(lm.landmark[4].x * w), int(lm.landmark[4].y * h))
            cv2.circle(img, index_pos, 10, (255, 255, 255), -1)

        if index_pos:
            if self.dragging is None:
                for ball in self.balls:
                    if ball['placed']:
                        continue
                    bx, by = ball['pos']
                    dist = np.hypot(index_pos[0] - bx, index_pos[1] - by)
                    if dist < 40:
                        self.dragging = ball
                        break
            else:
                self.dragging['pos'] = list(index_pos)

                if thumb_pos:
                    pinch_distance = np.hypot(index_pos[0] - thumb_pos[0], index_pos[1] - thumb_pos[1])
                    if pinch_distance < 40:
                        x, y = self.dragging['pos']
                        correct_basket = self.baskets[self.dragging['color']]
                        bx1, by1, bx2, by2 = correct_basket
                        if bx1 < x < bx2 and by1 < y < by2:
                            self.dragging['placed'] = True
                            self.score += 1
                        else:
                            self.dragging['pos'] = list(self.dragging['orig_pos'])
                        self.dragging = None
        return img

    def is_level_complete(self):
        return self.score == self.total



def run_level3(root, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    game = Level3_ColorMatching(hands)
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

    def update():
        success, frame = cap.read()
        if not success:
            root.after(10, update)
            return

        frame = cv2.flip(frame, 1)
        frame = game.update(frame)
        game.draw(frame)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        if game.is_level_complete():
            level_unlocked[4] = True
            cap.release()
            show_result(root, 100.0, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback)
        else:
            root.after(10, update)  

    update()


def show_result(root, acc, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    passed = acc >= 70
    msg = f"Great job! Accuracy {acc:.1f}%" if passed else f"Accuracy {acc:.1f}% — need ≥ 70%"

    tk.Label(root, text=msg, font=("Arial", 18)).pack(pady=30)

    if passed and new_level_callback:
        level_unlocked[4] = True
        tk.Button(root, text="Next Level", font=("Arial", 16), command=new_level_callback).pack(pady=10)
    else:
        tk.Button(root, text="Retry", font=("Arial", 16),
                command=retry_level_callback).pack(pady=10)


    tk.Button(root, text="Back to Menu", font=("Arial", 14),
              command=back_to_menu_callback).pack(pady=10)
