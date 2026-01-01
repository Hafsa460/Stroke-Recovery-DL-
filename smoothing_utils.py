"""
Smoothing utilities for gesture and movement tracking.
Provides exponential smoothing and moving average filters.
"""
import numpy as np
from collections import deque


class ExponentialSmoother:
    """Exponential smoothing filter for position data (x, y)"""
    def __init__(self, alpha=0.6):
        """
        alpha: smoothing factor (0-1). Higher = more responsive, lower = smoother.
        """
        self.alpha = alpha
        self.prev_x = None
        self.prev_y = None

    def smooth(self, x, y):
        """Apply exponential smoothing to (x, y) position"""
        if self.prev_x is None:
            self.prev_x = x
            self.prev_y = y
            return x, y
        
        smooth_x = self.alpha * x + (1 - self.alpha) * self.prev_x
        smooth_y = self.alpha * y + (1 - self.alpha) * self.prev_y
        
        self.prev_x = smooth_x
        self.prev_y = smooth_y
        return smooth_x, smooth_y

    def reset(self):
        self.prev_x = None
        self.prev_y = None


class MovingAverageSmoother:
    """Moving average filter for position data (x, y)"""
    def __init__(self, window_size=5):
        """
        window_size: number of frames to average over
        """
        self.window_size = window_size
        self.x_buffer = deque(maxlen=window_size)
        self.y_buffer = deque(maxlen=window_size)

    def smooth(self, x, y):
        """Apply moving average to (x, y) position"""
        self.x_buffer.append(x)
        self.y_buffer.append(y)
        
        avg_x = np.mean(list(self.x_buffer))
        avg_y = np.mean(list(self.y_buffer))
        
        return avg_x, avg_y

    def reset(self):
        self.x_buffer.clear()
        self.y_buffer.clear()


class DistanceSmoother:
    """Smoothing filter for distance measurements (e.g., pinch detection)"""
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.prev_dist = None

    def smooth(self, distance):
        """Apply exponential smoothing to a scalar distance value"""
        if self.prev_dist is None:
            self.prev_dist = distance
            return distance
        
        smooth_dist = self.alpha * distance + (1 - self.alpha) * self.prev_dist
        self.prev_dist = smooth_dist
        return smooth_dist

    def reset(self):
        self.prev_dist = None
