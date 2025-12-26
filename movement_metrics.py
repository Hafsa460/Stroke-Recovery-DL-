import numpy as np
from collections import deque


class MovementMetrics:
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.positions = deque(maxlen=window_size)
        self.grasp_events = []
        self.session_start = None
        self.first_success_time = None

    def add_position(self, x, y):
        self.positions.append((x, y))

    def smoothness(self):
        if len(self.positions) < 4:
            return 0.0
        pts = np.array(self.positions)
        v = np.diff(pts, axis=0)
        a = np.diff(v, axis=0)
        jerk = np.diff(a, axis=0)
        mag = np.linalg.norm(jerk, axis=1)
        avg_jerk = float(np.mean(mag))
        score = max(0.0, 100.0 - avg_jerk * 10.0)
        return min(100.0, score)

    def reset(self):
        self.positions.clear()
        self.grasp_events.clear()
        self.session_start = None
        self.first_success_time = None

    def start_session(self, ts):
        self.session_start = ts

    def record_first_success(self, ts):
        if self.first_success_time is None:
            self.first_success_time = ts

    def add_grasp_event(self, success: bool, ts=None):
        self.grasp_events.append({'success': bool(success), 'ts': ts})

    def grasp_quality(self):
        if not self.grasp_events:
            return 0.0
        succ = sum(1 for e in self.grasp_events if e.get('success'))
        return float(succ) / len(self.grasp_events) * 100.0

    def reaction_time(self):
        if self.session_start is None or self.first_success_time is None:
            return None
        return float(self.first_success_time - self.session_start)
