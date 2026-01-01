import cv2
import random
import tkinter as tk
from PIL import Image, ImageTk
import mediapipe as mp
from smoothing_utils import ExponentialSmoother

from level3 import show_result
import time

try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False

class Level4_SequenceTapping:
    def __init__(self, hands_detector):
        self.hands_detector = hands_detector
        self.colors = ['red', 'green', 'blue', 'yellow']
        self.square_size = 100
        self.squares_pos = [(50, 100), (200, 100), (350, 100), (500, 100)]
        self.sequence = []
        self.user_taps = []
        self.current_show_index = 0
        self.show_sequence = True
        self.timer = 0
        self.score = 0
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.generate_sequence(5)
        self.level_complete = False
        self.last_tap_time = 0
        self.flash_index = -1
        self.blink_timer = 0  # For blinking effect
        self.show_repeat_button = False  # Show "Repeat" after sequence
        self.repeat_button_rect = (200, 400, 440, 450)  # (x1, y1, x2, y2)

    def generate_sequence(self, length):
        self.sequence = [random.choice(self.colors) for _ in range(length)]

    def get_bgr(self, color):
        return {'red': (0, 0, 255), 'green': (0, 255, 0), 'blue': (255, 0, 0), 'yellow': (0, 255, 255)}.get(color, (255, 255, 255))

    def draw(self, img):
        for i, color in enumerate(self.colors):
            x, y = self.squares_pos[i]
            thickness = 3
            bgr = self.get_bgr(color)

            if self.show_sequence and self.current_show_index < len(self.sequence) and self.sequence[self.current_show_index] == color:
                # Blink effect: toggle on/off every 15 frames
                if (self.blink_timer // 15) % 2 == 0:
                    thickness = -1
            elif self.flash_index == i:
                thickness = -1 

            cv2.rectangle(img, (x, y), (x + self.square_size, y + self.square_size), bgr, thickness)
            cv2.putText(img, color.capitalize(), (x, y - 10), self.font, 0.7, bgr, 2)

        cv2.putText(img, 'Repeat the sequence by tapping squares', (10, 40), self.font, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f'Score: {self.score}/{len(self.sequence)}', (10, 70), self.font, 0.7, (255, 255, 255), 2)
        
        # Draw "Repeat" button if sequence finished
        if self.show_repeat_button:
            x1, y1, x2, y2 = self.repeat_button_rect
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 200, 255), -1)
            cv2.putText(img, 'Repeat Sequence', (x1 + 20, y1 + 30), self.font, 0.8, (255, 255, 255), 2)

    def update(self, img):
        self.flash_index = -1
        self.blink_timer += 1

        if self.show_sequence:
            self.timer += 1
            if self.timer % 30 == 0:
                self.current_show_index += 1
                if self.current_show_index >= len(self.sequence):
                    self.show_sequence = False
                    self.show_repeat_button = True  # Show repeat button
                    self.current_show_index = -1
        else:
            results = self.hands_detector.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            index_pos = None
            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0]
                h, w, _ = img.shape
                index_pos = (int(lm.landmark[8].x * w), int(lm.landmark[8].y * h))
                cv2.circle(img, index_pos, 10, (255, 255, 255), -1)

            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0]
                h, w, _ = img.shape
                index_pos = (int(lm.landmark[8].x * w), int(lm.landmark[8].y * h))
                thumb_pos = (int(lm.landmark[4].x * w), int(lm.landmark[4].y * h))

                cv2.circle(img, index_pos, 10, (255, 255, 255), -1)

                dist = ((index_pos[0] - thumb_pos[0]) ** 2 + (index_pos[1] - thumb_pos[1]) ** 2) ** 0.5

                # Check if clicked "Repeat" button
                if self.show_repeat_button and dist < 40:
                    x1, y1, x2, y2 = self.repeat_button_rect
                    if x1 < index_pos[0] < x2 and y1 < index_pos[1] < y2:
                        # Repeat sequence
                        self.show_sequence = True
                        self.show_repeat_button = False
                        self.current_show_index = 0
                        self.timer = 0
                        self.user_taps = []
                        self.score = 0

                if dist < 40 and (time.time() - self.last_tap_time > 0.5):  
                    for i, (x, y) in enumerate(self.squares_pos):
                        if x < index_pos[0] < x + self.square_size and y < index_pos[1] < y + self.square_size:
                            self.user_taps.append(i)
                            self.flash_index = i
                            self.last_tap_time = time.time()

                            correct_color = self.colors.index(self.sequence[len(self.user_taps) - 1])
                            if i == correct_color:
                                self.score += 1
                            else:
                                self.user_taps = []
                                self.score = 0
                            break


            if len(self.user_taps) == len(self.sequence):
                self.level_complete = True

        return img

    def is_level_complete(self):
        return self.level_complete

    def get_accuracy(self):
        return (self.score / len(self.sequence)) * 100 if self.sequence else 0


def run_level4(root, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    game = Level4_SequenceTapping(hands)

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

        # Collect simple position metric from hand index if available
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
        game.draw(frame)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        if game.is_level_complete():
            level_unlocked[5] = True
            accuracy = game.get_accuracy()
            cap.release()
            # Log session if logger available
            try:
                smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                globals()['logger'].log_session(level=4, duration_s=0.0, score=accuracy, smoothness=smooth, grasp_quality=0.0, notes='Level4 complete')
            except Exception:
                pass
            show_result(root, accuracy, level_unlocked, back_to_menu_callback, new_level_callback,retry_level_callback)
        else:
            root.after(10, update)

    update()
