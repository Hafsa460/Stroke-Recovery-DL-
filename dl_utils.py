import cv2
import numpy as np
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None
import mediapipe as mp


class ObjectDetector:
    def __init__(self, model_path='best.pt', conf=0.4, device=None):
        self.model_path = model_path
        self.conf = conf
        self.model = None
        if YOLO is None:
            return
        try:
            self.model = YOLO(model_path)
            # device selection handled by ultralytics if provided as arg in train/predict
        except Exception:
            self.model = None

    def detect(self, frame):
        """Run inference on a single BGR frame. Returns simple dict or None."""
        if self.model is None:
            return None
        try:
            results = self.model(frame, conf=self.conf, verbose=False)
            detections = {'boxes': [], 'confs': [], 'cls': [], 'names': []}
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    name = r.names.get(cls, str(cls))
                    detections['boxes'].append([x1, y1, x2, y2])
                    detections['confs'].append(conf)
                    detections['cls'].append(cls)
                    detections['names'].append(name)
            return detections
        except Exception:
            return None


class HandTracker:
    def __init__(self, min_detection_confidence=0.7, min_tracking_confidence=0.5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False,
                                         max_num_hands=2,
                                         min_detection_confidence=min_detection_confidence,
                                         min_tracking_confidence=min_tracking_confidence)

    def detect(self, frame):
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = self.hands.process(rgb)
            return res
        except Exception:
            return None


class DLModelManager:
    def __init__(self, model_path='best.pt'):
        self.detector = None
        self.hand_tracker = None
        try:
            if YOLO is not None:
                self.detector = ObjectDetector(model_path=model_path)
        except Exception:
            self.detector = None
        try:
            self.hand_tracker = HandTracker()
        except Exception:
            self.hand_tracker = None

    def process_frame(self, frame):
        """Return dict: {'objects': detections or None, 'hands': mediapipe result or None} """
        objs = None
        hands = None
        if self.detector is not None:
            objs = self.detector.detect(frame)
        if self.hand_tracker is not None:
            hands = self.hand_tracker.detect(frame)
        return {'objects': objs, 'hands': hands}

    def draw_results(self, frame, results):
        if results is None:
            return frame
        objs = results.get('objects')
        if objs:
            for box, conf, name in zip(objs['boxes'], objs['confs'], objs['names']):
                x1, y1, x2, y2 = box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        # Note: hand drawing left to application (MediaPipe provides drawing utils)
        return frame
