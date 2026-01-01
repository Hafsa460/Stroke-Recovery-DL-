# Stroke Recovery Game - Project Architecture & File Guide

## Overview
This is a **stroke rehabilitation game** using hand gesture recognition (MediaPipe) and computer vision (OpenCV). It features 10 progressive levels designed to improve hand mobility, grip strength, and fine motor control in stroke patients.

---

## 🗂️ Core Project Files

### **main.py** - Entry Point & Menu System
**Purpose:** Game launcher and level navigation hub.  
**What it does:**
- Initializes a tkinter GUI window (640x480)
- Displays the main menu with Play, How to Play, and About options
- Manages level unlocking system (only Level 1 starts unlocked)
- Handles level progression and callbacks when levels complete
- Tracks accuracy scores for each level
- Creates wrappers that launch each level with intro screens

**Key variables:**
- `level_unlocked`: Dict tracking which levels are accessible
- `level_accuracy`: Dict storing scores for each level
- Wrapper functions for each level (e.g., `run_level1_wrapper()`)

---

### **levels.py** - Level Persistence
**Purpose:** Save/load level unlock state to a JSON file.  
**What it does:**
- Loads unlocked levels from `levels.json` at startup
- Initially only Level 1 is unlocked; others unlock on completion
- Provides helper functions: `load_levels()`, `save_levels()`, `is_level_unlocked()`
- Enables persistent progress across sessions

---

## 🎮 Level Files (level1.py → level10.py)

Each level implements a specific rehabilitation exercise:

| Level | File | Exercise | Goal |
|-------|------|----------|------|
| 1 | `level1.py` | **Balance & Hold** | Pinch thumb+index and hold in target circle for 5 seconds |
| 2 | `level2.py` | **Shape Dragging** | Drag shapes to match outlines on screen |
| 3 | `level3.py` | **Color Matching** | Drag colored balls into matching basket zones |
| 4 | `level4.py` | **Sequence Tapping** | Tap colored squares in the sequence shown |
| 5 | `level5.py` | **Grip Strength** | Perform 5 repetitions of grip/release cycles |
| 6 | `level6.py` | **Hand Open/Close** | Follow prompts: open → close → open (5 reps) |
| 7 | `level7.py` | **Grab & Place** | Grab a green ball with pinch and place on red circle |
| 8 | `level8.py` | **Touch Targets** | Touch 8 randomly appearing targets |
| 9 | `level9.py` | **Zone Placement** | Place hand in correct zone (left/right) when prompted |
| 10 | `level10.py` | **Zone Sequence** | Follow a sequence of 4 zones in order |

### Typical Level Structure:
```python
# Hand tracking via MediaPipe
hands = mp_hands.Hands(min_detection_confidence=0.7)

# Game logic class (e.g., BalanceAndHold)
game = BalanceAndHold()

# Update loop captures video frames → detects hand landmarks → updates game state
def update():
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)  # Mirror for user convenience
    frame = game.update(frame, hands)  # Process and draw
    display_on_canvas(frame)
    if game.is_level_complete():
        show_result_screen()
    else:
        root.after(10, update)  # Next frame
```

---

## 📊 Utilities & Support Files

### **smoothing_utils.py** - NEW! Movement Smoothing
**Purpose:** Smooth hand gestures and reduce jitter from sensor noise.  
**Classes:**
- `ExponentialSmoother(alpha=0.6)`: Exponential smoothing for (x, y) positions
  - `smooth(x, y)` → returns smoothed coordinates
  - Higher alpha = more responsive, lower = smoother
- `MovingAverageSmoother(window_size=5)`: Moving average filter
  - Averages the last N frames of position
- `DistanceSmoother(alpha=0.5)`: Smooths scalar distance values (e.g., pinch gap)
  - Used in Level 6 to detect hand open/close state smoothly

**Used in:** All levels to reduce gesture jitter

---

### **movement_metrics.py** - Performance Tracking
**Purpose:** Quantify rehabilitation progress and movement quality.  
**Key metrics:**
- `smoothness()`: Calculates jerk (3rd derivative of position) to measure smoothness (0-100)
- `grasp_quality()`: Success rate of grip events
- `reaction_time()`: Time to first success after prompt
- `add_position(x, y)`: Buffers hand positions for later analysis
- `add_grasp_event(success, ts)`: Logs grip attempts

**Usage:** Called in each level to measure quality of movements for the session log.

---

### **data_logging.py** - Session Recording
**Purpose:** Log rehabilitation sessions to CSV for progress tracking.  
**Key method:**
- `log_session(level, duration_s, score, smoothness, grasp_quality, notes='')`: Writes one row to `session_data/sessions.csv`
- Creates headers: timestamp, level, duration, score, smoothness, grasp_quality, notes

**Output:** `session_data/sessions.csv` - therapists can analyze progress over time.

---

### **dl_utils.py** - Deep Learning & Object Detection
**Purpose:** Wraps hand tracking + object detection models.  
**Classes:**
1. **ObjectDetector**: Uses YOLO (`best.pt`) to detect balls, boxes, zones on screen
   - `detect(frame)` → returns bounding boxes, confidence, class names
2. **HandTracker**: MediaPipe hand tracking wrapper
   - `detect(frame)` → returns 21-point hand skeleton per hand
3. **DLModelManager**: Combines both for integrated inference
   - `process_frame(frame)` → returns both object detections and hand landmarks

**Used by:** All levels for robust hand detection and optional object tracking.

---

### **app.py** - Flask Web API (for Frontend Integration)
**Purpose:** Exposes stroke detection model via HTTP endpoints.  
**Routes:**
- `/` → Landing page (Stroke Detection & Recovery Game)
- `/options` → Menu (Test Reports or Play Game)
- `/verify` → Image upload for stroke prediction
- `/api/predict` → POST endpoint for ML inference
  - Input: image file
  - Output: JSON with prediction (Hemorrhagic/Ischemic/Normal) + confidence
- `/play` → Launches main.py in background

**Models used:**
- `best_stage1_model.pth`: Detects Ischemic vs non-Ischemic
- `best_stage2_model.pth`: Distinguishes Hemorrhagic vs Normal

---

### **requirements.txt** - Dependencies
```
ultralytics>=8.0.0       # YOLO for object detection
mediapipe>=0.10.0        # Hand/pose tracking
opencv-python>=4.5.5.64  # Computer vision
numpy>=1.22.0            # Numerical computing
Pillow>=9.0.0            # Image processing
Flask>=2.0.0             # Web framework
Flask-Cors>=3.0.10       # CORS support
torch>=1.9.0             # PyTorch for models
torchvision>=0.10.0      # Vision models
```

---

## 📂 Directory Structure

```
Stroke-Recovery-DL-/
├── main.py                      # Entry point
├── level1.py - level10.py       # 10 rehabilitation levels
├── levels.py                    # Level persistence
├── movement_metrics.py          # Performance metrics
├── data_logging.py              # CSV session logging
├── smoothing_utils.py           # Movement smoothing filters
├── dl_utils.py                  # Model wrappers
├── app.py                       # Flask web API
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (FLASK_DEBUG, MONGO_URI, etc.)
├── session_data/
│   └── sessions.csv             # Logged rehabilitation sessions
├── templates/                   # HTML templates for Flask
│   ├── index.html               # Landing page
│   ├── options.html             # Menu (Test Reports / Play Game)
│   ├── verify.html              # Stroke detection page
│   └── play_started.html        # Game launched confirmation
├── static/                      # Frontend assets
│   ├── style.css                # Styling
│   └── verify.js                # Image upload handler
├── best.pt                      # YOLO object detection model
├── best_stage1_model.pth        # PyTorch Stage 1 model (Ischemic detection)
├── best_stage2_model.pth        # PyTorch Stage 2 model (Hemorrhagic vs Normal)
├── ball.png, box.png            # Game assets
├── tests/                       # Unit tests
└── __pycache__/                 # Python cache
```

---

## 🔄 Typical User Flow

### **Desktop Game Mode:**
1. User runs `python main.py`
2. Main menu appears → selects "Play"
3. Level menu shows available levels
4. User clicks Level 1 → intro screen
5. Level game starts (tkinter + OpenCV)
6. Webcam captures hand landmarks via MediaPipe
7. Game logic updates state and renders feedback
8. On completion → result screen with score
9. Session logged to CSV

### **Web Mode (Stroke Detection):**
1. User runs `python app.py`
2. Opens browser → http://127.0.0.1:5000
3. Landing page → clicks "Enter"
4. Menu → selects "Test Reports"
5. Verify page → uploads an MRI image
6. Flask calls `/api/predict` with image
7. Two-stage model runs (Stage1 → Stage2)
8. Result displayed: Hemorrhagic / Ischemic / Normal + confidence

---

## 🎯 Key Features Implemented

### **Smoothing (NEW)**
- **ExponentialSmoother**: Reduces gesture jitter in pinch/grip detection
  - Applied in: Level 1 (pinch position), Level 6 (open/close detection)
- **DistanceSmoother**: Smooths distance measurements between finger landmarks
  - Makes gesture recognition more reliable and less prone to false triggers

### **Metrics & Logging**
- Movement smoothness (jerk-based scoring)
- Grasp quality (success rate)
- Reaction time tracking
- Session CSV export for therapist review

### **Model Integration**
- Hand tracking: MediaPipe (21-point skeleton)
- Object detection: YOLO (`best.pt`)
- Stroke classification: Two-stage PyTorch models

---

## 🚀 How to Run

### **Game Mode:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

### **Web API Mode:**
```bash
# Start Flask server
python app.py

# Open browser
http://127.0.0.1:5000
```

---

## 📝 Notes for Future Development

1. **Database Integration:** Currently uses CSV. Could add MongoDB (`.env` placeholder exists).
2. **Video Playback:** Consider recording sessions for patient feedback.
3. **Mobile Support:** Game could run on mobile with camera access.
4. **Real-time Feedback:** Add audio cues ("Great job!" on success).
5. **Therapist Dashboard:** Web UI to view patient progress across sessions.

---

**Version:** 1.0 (with movement smoothing)  
**Last Updated:** Jan 2, 2026  
**Status:** Full game + web API integrated
