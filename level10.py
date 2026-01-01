import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import time
import random
from smoothing_utils import ExponentialSmoother
try:
    from dl_utils import DLModelManager
    from movement_metrics import MovementMetrics
    from data_logging import SessionLogger
    DL_AVAILABLE = True
except Exception:
    DL_AVAILABLE = False
from level3 import show_result


def run_level10(root, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback):
    for widget in root.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(root, width=640, height=480)
    canvas.pack()
    label = tk.Label(root, text="Follow the sequence of zones in order (Mixed Sequence)", font=("Arial", 14))
    label.pack()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)

    # Create zone positions
    zone_positions = [(120, 120), (320, 120), (520, 120), (320, 360)]  # TL, TC, TR, BC
    # Shuffle the sequence randomly
    sequence = list(range(4))  # [0, 1, 2, 3]
    random.shuffle(sequence)  # e.g. [2, 0, 3, 1]
    
    index = 0
    hits_required = 4
    hits = 0
    radius = 50

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
        nonlocal index, hits
        ret, frame = cap.read()
        if not ret:
            root.after(10, update)
            return
        frame = cv2.flip(frame, 1)
        init_dl()
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        # draw all zones with colors indicating order
        colors_map = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 0)]
        for i, pos in enumerate(zone_positions):
            # Highlight current target zone
            if sequence[index] == i:
                color = (0, 255, 0)  # Green = next target
                thickness = 3
                cv2.circle(frame, pos, radius + 5, color, thickness)
            else:
                color = colors_map[i]
                thickness = 2
                cv2.circle(frame, pos, radius, color, thickness)
            
            # Draw zone number (based on sequence order)
            zone_order = sequence.index(i) + 1
            cv2.putText(frame, str(zone_order), (pos[0] - 10, pos[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        cv2.putText(frame, f'Progress: {hits}/{hits_required}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f'Current Target: Zone {sequence[index] + 1}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Display sequence order at bottom
        seq_display = ' → '.join([str(sequence.index(i) + 1) for i in range(4)])
        cv2.putText(frame, f'Sequence Order: {seq_display}', (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0]
            ix = int(lm.landmark[8].x * w)
            iy = int(lm.landmark[8].y * h)
            if globals().get('metrics') is not None:
                try:
                    globals()['metrics'].add_position(ix, iy)
                except Exception:
                    pass
            
            # Check if hand is in current target zone
            tx, ty = zone_positions[sequence[index]]
            dist = ((ix - tx) ** 2 + (iy - ty) ** 2) ** 0.5
            if dist < radius:
                hits += 1
                index = min(len(sequence) - 1, index + 1)
                cv2.putText(frame, '✓ ZONE HIT!', (250, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.imgtk = imgtk

        if hits >= hits_required:
            cap.release()
            hands.close()
            try:
                smooth = globals()['metrics'].smoothness() if globals().get('metrics') is not None else 0.0
                score = min(100.0, (hits / hits_required) * 100.0)
                globals()['logger'].log_session(level=10, duration_s=0.0, score=score, smoothness=smooth, grasp_quality=0.0, notes=f'Level10 sequence_hits:{hits}/{hits_required}')
            except Exception:
                pass
            level_unlocked[10] = True
            show_result(root, score, level_unlocked, back_to_menu_callback, new_level_callback, retry_level_callback)
        else:
            root.after(10, update)

    update()
