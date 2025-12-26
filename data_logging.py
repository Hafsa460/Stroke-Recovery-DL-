import os
import csv
from datetime import datetime


class SessionLogger:
    def __init__(self, log_dir='session_data'):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.csv_file = os.path.join(self.log_dir, 'sessions.csv')
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp','level','duration_s','score','smoothness','grasp_quality','notes'])

    def log_session(self, level, duration_s, score, smoothness, grasp_quality, notes=''):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([ts, level, f'{duration_s:.1f}', f'{score:.1f}', f'{smoothness:.1f}', f'{grasp_quality:.1f}', notes])
        print(f"✅ Session logged: level={level}, score={score:.1f}")
