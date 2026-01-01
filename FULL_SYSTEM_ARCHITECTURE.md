# STROKE RECOVERY GAME - COMPLETE SYSTEM ARCHITECTURE & DETAILED REPORT

**Date:** January 2, 2026  
**Version:** 2.0 (Full Stack - Desktop Game + Web API)  
**Status:** Production Ready

---

## 📋 TABLE OF CONTENTS
1. [System Architecture Overview](#system-architecture-overview)
2. [Flask API - Stroke Detection System](#flask-api-stroke-detection-system)
3. [Desktop Game - Main Flow](#desktop-game-main-flow)
4. [Detailed Level Breakdown](#detailed-level-breakdown)
5. [Data Flow & Integration](#data-flow-integration)
6. [Installation & Deployment](#installation--deployment)
7. [Technical Stack](#technical-stack)

---

## 🏗️ SYSTEM ARCHITECTURE OVERVIEW

### Two-Mode Application

```
┌─────────────────────────────────────────────────────────────┐
│           Stroke Recovery System (Python)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐         ┌──────────────────────┐ │
│  │   FLASK WEB API      │         │   DESKTOP GAME       │ │
│  │   (app.py)           │         │   (main.py)          │ │
│  ├──────────────────────┤         ├──────────────────────┤ │
│  │  • Stroke Detection  │         │  • 10 Levels         │ │
│  │  • Image Upload      │         │  • Hand Tracking     │ │
│  │  • Two-Stage Models  │         │  • Progress Logging  │ │
│  │  • REST Endpoints    │         │  • Level Unlocking   │ │
│  │  • Web Pages         │         │  • Session Metrics   │ │
│  └──────────────────────┘         └──────────────────────┘ │
│        Port 5000                      Tkinter GUI            │
│    http://localhost:5000          Local Rehabilitation      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 FLASK API - STROKE DETECTION SYSTEM

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    FLASK WEB SERVER (app.py)                     │
│                    Listening on port 5000                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Startup Phase:                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Load Stage 1 Model (best_stage1_model.pth)          │   │
│  │    - ResNet50 with 1 input channel (grayscale)        │   │
│  │    - Detects: Ischemic (class 1) vs Non-Ischemic      │   │
│  │                                                          │   │
│  │ 2. Load Stage 2 Model (best_stage2_model.pth)          │   │
│  │    - ResNet50 with 1 input channel                     │   │
│  │    - Detects: Hemorrhagic (class 0) vs Normal (class 2)│   │
│  │                                                          │   │
│  │ 3. Setup GPU/CPU Device                                │   │
│  │    - Uses CUDA if available, else CPU                 │   │
│  │                                                          │   │
│  │ 4. Initialize Flask App                                │   │
│  │    - CORS enabled (cross-origin requests allowed)     │   │
│  │    - Static folder: ./static                          │   │
│  │    - Template folder: ./templates                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  HTTP Routes:                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Route 1: GET /                                          │   │
│  │ Returns: index.html (Landing Page)                     │   │
│  │ Purpose: Welcome screen → "Enter" button               │   │
│  │                                                          │   │
│  │ Route 2: GET /options                                  │   │
│  │ Returns: options.html (Menu Page)                      │   │
│  │ Buttons: "Test Reports" | "Play Game"                  │   │
│  │                                                          │   │
│  │ Route 3: GET /verify                                   │   │
│  │ Returns: verify.html (Upload Page)                     │   │
│  │ UI: File input → Preview → Upload button               │   │
│  │                                                          │   │
│  │ Route 4: POST /api/predict ⭐ MAIN API                 │   │
│  │ Input: FormData with image file                        │   │
│  │ Output: JSON {prediction, confidence}                  │   │
│  │ Processing:                                             │   │
│  │   a. Save file to temp directory                       │   │
│  │   b. Load and preprocess image:                        │   │
│  │      - Open as grayscale                              │   │
│  │      - Resize to 224×224                              │   │
│  │      - Normalize to [0-1]                             │   │
│  │      - Convert to PyTorch tensor                      │   │
│  │   c. Stage 1 Inference:                                │   │
│  │      - Pass through stage1_model                       │   │
│  │      - Get argmax prediction (0 or 1)                 │   │
│  │      - Confidence = softmax[pred class]                │   │
│  │   d. If Stage 1 = Ischemic (1):                        │   │
│  │      - Return "Ischemic" + confidence                  │   │
│  │   e. If Stage 1 = Non-Ischemic (0):                    │   │
│  │      - Pass to stage2_model                           │   │
│  │      - Get argmax (0 or 1)                            │   │
│  │      - Map 0→Hemorrhagic, 1→Normal                   │   │
│  │      - Return prediction + confidence                  │   │
│  │   f. Delete temp file                                 │   │
│  │   g. Return JSON to client                            │   │
│  │                                                          │   │
│  │ Route 5: GET /play                                     │   │
│  │ Action: Launch main.py in background subprocess       │   │
│  │ Returns: play_started.html (Confirmation page)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### API Endpoint Details: `/api/predict`

```python
HTTP POST /api/predict
├── Request:
│   ├── Content-Type: multipart/form-data
│   ├── Body: { "image": <file binary> }
│   └── Example: curl -F "image=@scan.png" http://localhost:5000/api/predict
│
├── Processing Pipeline:
│   ├── Step 1: Validate Request
│   │   ├── Check if "image" field exists
│   │   ├── Check if filename is not empty
│   │   └── Return 400 if validation fails
│   │
│   ├── Step 2: Save Uploaded File
│   │   ├── Generate unique filename: predict_{uuid}.png
│   │   ├── Save to temp directory (e.g., /tmp on Linux, %TEMP% on Windows)
│   │   └── Path example: C:\Users\...\AppData\Local\Temp\predict_a1b2c3d4.png
│   │
│   ├── Step 3: Image Preprocessing
│   │   ├── Open image with PIL
│   │   ├── Convert to grayscale (L mode)
│   │   ├── Resize to 224×224
│   │   ├── Normalize: pixel_value / 255.0
│   │   ├── Create tensor: [1, 1, 224, 224] (batch=1, channels=1)
│   │   └── Move to device (GPU/CPU)
│   │
│   ├── Step 4: Two-Stage Inference
│   │   │
│   │   ├── Stage 1: Ischemic Detection
│   │   │   ├── Input: tensor [1, 1, 224, 224]
│   │   │   ├── Model: stage1_model (ResNet50)
│   │   │   ├── Output: logits [1, 2]
│   │   │   ├── Argmax: pred ∈ {0=Non-Ischemic, 1=Ischemic}
│   │   │   ├── Confidence: softmax(logits)[0, pred]
│   │   │   │
│   │   │   └── Decision Branch:
│   │   │       ├── If pred == 1 (Ischemic):
│   │   │       │   └── Return "Ischemic" + confidence → END
│   │   │       └── Else (pred == 0, Non-Ischemic):
│   │   │           └── Continue to Stage 2
│   │   │
│   │   └── Stage 2: Hemorrhagic vs Normal Classification
│   │       ├── Input: Same tensor from Stage 1
│   │       ├── Model: stage2_model (ResNet50)
│   │       ├── Output: logits [1, 2]
│   │       ├── Argmax: pred ∈ {0, 1}
│   │       ├── Confidence: softmax(logits)[0, pred]
│   │       │
│   │       └── Mapping:
│   │           ├── If pred == 0 → "Hemorrhagic"
│   │           └── If pred == 1 → "Normal"
│   │
│   └── Step 5: Cleanup & Response
│       ├── Delete temp image file
│       ├── Return JSON response
│       └── (If error: return 500 with error message)
│
└── Response:
    ├── Success (200):
    │   {
    │     "success": true,
    │     "prediction": "Ischemic|Hemorrhagic|Normal",
    │     "confidence": 0.87  (0.0-1.0)
    │   }
    │
    └── Error (4xx/5xx):
        {
          "success": false,
          "message" | "error": "error description"
        }
```

### Frontend-Backend Communication (Web Mode)

```javascript
// verify.js: Frontend sends image to /api/predict
const fd = new FormData();
fd.append('image', selectedFile);  // User uploads MRI/brain scan

const res = await fetch('/api/predict', {
  method: 'POST',
  body: fd  // FormData automatically sets Content-Type: multipart/form-data
});

const data = await res.json();
// Response: { success: true, prediction: "Ischemic", confidence: 0.92 }

// Display result on page
resultArea.innerHTML = `
  <h4>Prediction Result:</h4>
  <p><strong>Prediction:</strong> ${data.prediction}</p>
  <p><strong>Confidence:</strong> ${Math.round(data.confidence*100)}%</p>
`;
```

---

## 🎮 DESKTOP GAME - MAIN FLOW

### Initialization Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User runs: python main.py                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ main.py imports all levels                                   │
│ - Imports: level1.py, level2.py, ..., level10.py           │
│ - Each level has: run_levelN(root, ...) function           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Initialize Tkinter Window                                   │
│ - Window size: 640×480                                     │
│ - Title: "Stroke Recovery Game"                            │
│ - Level unlock state: {1: True, 2-10: False}              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ show_main_menu() displays:                                  │
│ ┌─────────────────────────────────┐                        │
│ │ Stroke Recovery Game            │                        │
│ │                                 │                        │
│ │  [Play]                         │                        │
│ │  [How to Play]                  │                        │
│ │  [About]                        │                        │
│ └─────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                           │
                 ┌─────────┼─────────┐
                 │         │         │
        [Play]   │  [How]  │  [About]│
                 │         │         │
                 ▼         ▼         ▼
          show_level_menu  show_how_to_play  show_about
                 │
                 ▼
    Level Selection Menu (1-10)
    Unlocked levels clickable
    Locked levels disabled
```

### Level Execution Flow (All Levels Follow Similar Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│ User clicks Level N → run_levelN_wrapper()                  │
│                                                               │
│ Step 1: Show intro screen with level description            │
│         (1.4 second delay before starting)                  │
│                                                               │
│ Step 2: run_levelN(root, level_unlocked, callbacks...)      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Level Initialization (inside run_levelN):                   │
│                                                               │
│ ├─ Clear all widgets from root                             │
│ ├─ Create Canvas (640×480) for video display               │
│ ├─ Initialize MediaPipe hands detector                      │
│ ├─ Open webcam (cv2.VideoCapture(0))                       │
│ ├─ Create game logic object (e.g., BalanceAndHold())       │
│ ├─ Optionally init DL components:                           │
│ │  ├─ DLModelManager('best.pt')  [YOLO for objects]        │
│ │  ├─ MovementMetrics()           [Track performance]       │
│ │  └─ SessionLogger()             [Log session]             │
│ └─ Start update loop (frame-by-frame processing)           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Frame Update Loop (runs ~30 fps):                           │
│                                                               │
│ def update():                                               │
│   1. Capture frame from webcam                             │
│   2. Flip frame horizontally (mirror effect)               │
│   3. Detect hands with MediaPipe                           │
│   4. Call game.update(frame)                               │
│      └─ Processes hand landmarks                           │
│      └─ Updates game state                                 │
│      └─ Draws UI (target, score, prompts)                  │
│   5. (Optional) Collect metrics with MovementMetrics       │
│   6. Convert frame BGR→RGB, show on canvas                 │
│   7. Check if level is complete                            │
│      ├─ If YES:  show_result() → log session → next level  │
│      └─ If NO:   root.after(10, update)  # 10ms delay      │
└─────────────────────────────────────────────────────────────┘
```

### Level Completion & Progression

```
Level Complete
      │
      ▼
┌─────────────────────────────────┐
│ Call show_result(root, score,   │
│   level_unlocked, callbacks...)  │
│                                  │
│ Display:                         │
│ ✓ Completion message            │
│ ✓ Score: 100.0                  │
│ ✓ Buttons: Next Level / Retry   │
└─────────────────────────────────┘
      │
      ├─→ [Next Level] Button
      │   ├─ Unlock next level: level_unlocked[n+1] = True
      │   ├─ Save to levels.json
      │   └─ Run next level wrapper
      │
      └─→ [Retry] Button
          └─ Restart current level
```

---

## 📊 DETAILED LEVEL BREAKDOWN

### LEVEL 1 - Balance & Hold (Pinch Control)

**File:** `level1.py`

**Exercise:** Pinch thumb and index finger, hold position in target circle for 5 seconds.

**Rehabilitation Focus:** Fine motor control, hand stabilization, precision grip.

```python
# Game Logic Class
class BalanceAndHold:
    def __init__(self, hold_time=5):
        self.hold_time = 5  # seconds to hold
        self.target_pos = (320, 240)  # center of screen
        self.radius = 30  # target circle size in pixels
        self.count = 0  # completions counter
        self.smoother = ExponentialSmoother(alpha=0.7)  # smooth jitter

    def update(self, img, hands_detector):
        # Draw target circle
        cv2.circle(img, self.target_pos, self.radius, (0, 255, 0), 2)
        
        # Detect hand landmarks
        results = hands_detector.process(...)
        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]
            # Get index finger tip (landmark 8)
            index_tip = lm.landmark[8]
            x = int(index_tip.x * w)
            y = int(index_tip.y * h)
            
            # Smooth position
            x, y = self.smoother.smooth(x, y)
            
            # Draw current position
            cv2.circle(img, (x, y), 8, (255, 255, 255), -1)
            
            # Check if inside target
            dist = distance((x, y), self.target_pos)
            if dist < self.radius:
                if self.hold_start is None:
                    self.hold_start = time.time()
                elapsed = time.time() - self.hold_start
                
                if elapsed >= self.hold_time:
                    self.count += 1
                    self.hold_start = None
                    if self.count >= 1:
                        self.completed = True
```

**Metrics Tracked:**
- Time to complete
- Position smoothness (via jerk calculation)
- Hold stability

---

### LEVEL 2 - Shape Dragging (Visual Coordination)

**File:** `level2.py`

**Exercise:** Drag shapes from left side to match outlines on right side.

**Rehabilitation Focus:** Eye-hand coordination, visual tracking, drag movement control.

```python
# Game Elements
- Source shapes (left): ball.png, box.png
- Target outlines (right): matching positions
- Hand tracking: index finger used as drag cursor
- Smoothing: Applied to drag position

# Gameplay Loop
1. Detect hand index finger position
2. Apply smoothing
3. Check if hand overlaps with shape (grab)
4. If grabbed: drag shape with hand
5. Check if shape reaches target outline
6. On match: lock shape in place
7. Score: (matched_shapes / total_shapes) * 100
```

**Mechanics:**
- Overlay detection for transparency blending
- Collision detection (point-to-box)
- Smooth dragging with interpolation (lerp)

---

### LEVEL 3 - Color Matching (Cognitive & Motor)

**File:** `level3.py`

**Exercise:** Drag colored balls into matching color baskets.

**Rehabilitation Focus:** Color recognition, fine dragging, multiple object tracking.

```python
# Game Elements
Colors: Red, Green, Blue
Balls: 6 total (2 of each color)
Baskets: 3 targets (1 per color)
Hand Input: Index finger for dragging

# State Tracking
for each ball:
    - position: [x, y]
    - color: 'red'|'green'|'blue'
    - placed: True/False
    - orig_pos: original position

# Dragging Logic
if hand_position overlaps ball:
    dragging = ball_id
    ball.pos = hand_position (smoothed)
else if hand releases (depth threshold):
    if ball in basket:
        ball.placed = True
        score++
    else:
        ball.pos = orig_pos  # reset
```

---

### LEVEL 4 - Sequence Tapping (Memory & Rhythm)

**File:** `level4.py`

**Exercise:** Watch sequence of colored squares flash, then tap in same order.

**Rehabilitation Focus:** Memory, reaction time, sequential motor control.

```python
# Gameplay Flow
1. Show sequence: RED → GREEN → BLUE → YELLOW (animated)
2. Wait for user input
3. User taps colored squares in correct order
4. Each correct tap: green flash, score++
5. Wrong tap: red flash, restart sequence
6. Complete all 5 items: level complete

# Hand Detection
- Index finger position tracked
- Check distance from each square
- If distance < radius: tap detected
- Cooldown timer to prevent double-taps
```

---

### LEVEL 5 - Grip Strength (Strength Measurement)

**File:** `level5.py`

**Class:** `GripStrengthGame`

**Exercise:** Perform 5 open-close grip cycles.

**Rehabilitation Focus:** Grip strength building, repetitive motion, endurance.

```python
# Detection Logic
def is_hand_closed(landmarks):
    # Check if all fingertips are close to wrist
    fingertips = [8, 12, 16, 20]  # indices, middle, ring, pinky
    closed_count = 0
    
    for tip_id in fingertips:
        distance = dist(tip[tip_id], wrist)
        if distance < 0.12:  # threshold
            closed_count += 1
    
    return closed_count >= 3  # at least 3 fingers closed

# Grip Cycle
1. Open hand (baseline)
2. Close hand (grip detected)
3. Count += 1
4. Repeat until count == 5

# Metrics
- Grips: total successful grips
- Consistency: success_rate = (grips / attempts) * 100
```

---

### LEVEL 6 - Hand Open/Close (Dexterity)

**File:** `level6.py`

**Class:** `Level6_HandOpenClose`

**Exercise:** Follow prompts: Open → Close → Open (repeat 5 times).

**Rehabilitation Focus:** Hand dexterity, gesture recognition, state transitions.

```python
# State Machine
State 0: Open hand
State 1: Close hand (make fist)
State 2: Open hand again

# Detection
distance = ||index_tip - thumb_tip||
if distance > 60: "open"
else: "closed"

# Smoothing
dist = dist_smoother.smooth(dist)

# Transition Logic
State 0 + open → State 1 (close prompt)
State 1 + closed → State 2 (open prompt)
State 2 + open → increment counter
  if counter >= 5: completed

# Metrics
- Sequence count: how many full cycles completed
- Smoothness: consistency of transitions
```

---

### LEVEL 7 - Grab & Place (Fine Motor)

**File:** `level7.py`

**Exercise:** Grab green ball with index+thumb pinch, place on red circle.

**Rehabilitation Focus:** Precision pinch, target placement, object tracking.

```python
# Mechanics
1. Ball displayed at center (300, 300)
2. Target circle at random position
3. Detect pinch: distance(index_tip, thumb_tip) < threshold
4. If pinch on ball: ball_grabbed = True
5. If grabbed: ball.pos = hand_position (smoothed)
6. On release: check if ball in target
7. If yes: increment score, new random target
8. Complete 10 placements: level done

# Difficulty Scaling
def get_target_radius(level):
    return max(30 - level * 2, 10)
    # Gets smaller as level increases
```

---

### LEVEL 8 - Touch Targets (Reaction & Accuracy)

**File:** `level8.py`

**Exercise:** Touch 8 randomly appearing targets as quickly as possible.

**Rehabilitation Focus:** Reaction time, hand speed, spatial awareness.

```python
# Gameplay
1. Target appears at random location
2. User touches target with index finger
3. Target disappears, new one appears
4. Repeat 8 times
5. Timer tracks total time

# Detection
distance = ||index_tip - target_center||
if distance < target_radius:
    target_hit = True
    targets_hit++
    new_target_location = random()

# Metrics
- Total time to complete
- Average reaction time per target
```

---

### LEVEL 9 - Zone Placement (Directional Control)

**File:** `level9.py`

**Exercise:** Place hand in correct zone (Left or Right) when prompted.

**Rehabilitation Focus:** Directional control, following instructions, hand placement.

```python
# Zones
Left Zone: (120, 240)  # left side of screen
Right Zone: (520, 240)  # right side

# Prompt Sequence
1. Show prompt: "Place hand in LEFT zone"
2. Wait for hand to enter zone
3. Confirm success
4. Prompt: "Place hand in RIGHT zone"
5. Repeat for 6 attempts total

# Detection
wrist_x = hand_landmarks[0].x * width
if (zone == 'left' and wrist_x < 320) or (zone == 'right' and wrist_x > 320):
    correct++

# Metrics
- Accuracy: (correct / total) * 100
```

---

### LEVEL 10 - Zone Sequence (Complex Coordination)

**File:** `level10.py`

**Exercise:** Follow sequence of 4 zones in correct order.

**Rehabilitation Focus:** Multi-step planning, sequential motor control, memory.

```python
# Sequence
sequence = [(120,120), (320,120), (520,120), (320,360)]
           # Top-left → Top-center → Top-right → Bottom-center

# Gameplay
1. Highlight zone 0 (top-left)
2. User moves hand to zone 0
3. On enter: unlock zone 1
4. Repeat for all zones
5. If user goes to wrong zone: reset

# State
- index: current zone in sequence (0-3)
- hits: zones completed successfully

# Metrics
- Sequence completion time
- Accuracy: how many wrong zones touched
```

---

## 🔄 DATA FLOW & INTEGRATION

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     WEB MODE (app.py)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  User Browser              Flask Server            Models   │
│      │                          │                    │       │
│      │──[1] GET / ────────────→ │                   │       │
│      │← [2] index.html ────────│                   │       │
│      │                          │                   │       │
│      │──[3] Click Enter ───────→ /options          │       │
│      │← [4] options.html ──────│                   │       │
│      │                          │                   │       │
│      │──[5] Test Reports ──────→ /verify           │       │
│      │← [6] verify.html ───────│                   │       │
│      │                          │                   │       │
│      │──[7] Select Image ──────→ (local upload)    │       │
│      │                          │                   │       │
│      │──[8] POST /api/predict ─→ │──[9] Load model │       │
│      │                          │  │                 │       │
│      │                          │  │──[10] Process  │       │
│      │                          │  │  Image         │       │
│      │                          │  │                 │       │
│      │                          │  ├─→ Stage1:      │       │
│      │                          │  │   Ischemic?    │       │
│      │                          │  │                 │       │
│      │                          │  ├─→ Stage2:      │       │
│      │                          │  │   Hemorrhagic? │       │
│      │                          │  │                 │       │
│      │← [11] JSON Response ────│──[12] Return     │       │
│      │  {prediction, conf}     │                    │       │
│      │                          │                   │       │
│      │──[13] Play Game ───────→ /play             │       │
│      │← [14] Subprocess ──────│ (starts main.py)  │       │
│                                                              │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                  GAME MODE (main.py + levels)                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Camera Input          Game Logic           Output           │
│      │                     │                  │              │
│      │──[1] Capture ──────→ │                 │              │
│      │  Frame              │                 │              │
│      │                      │                 │              │
│      │                  [2] MediaPipe         │              │
│      │                  Hand Detection       │              │
│      │                  (21 landmarks)       │              │
│      │                      │                 │              │
│      │                  [3] Level.update()    │              │
│      │                  - Check state        │              │
│      │                  - Update score       │              │
│      │                  - Detect gestures   │              │
│      │                      │                 │              │
│      │                  [4] MovementMetrics  │              │
│      │                  - Smoothness         │              │
│      │                  - Grasp quality      │              │
│      │                      │                 │              │
│      │                  [5] Draw UI          │              │
│      │                  - Targets            │──→ Display  │
│      │                  - Score              │   on Canvas │
│      │                  - Prompts            │              │
│      │                      │                 │              │
│      │                  [6] Check complete?  │              │
│      │                      │                 │              │
│      │                  YES: Show result     │              │
│      │                      │                 │              │
│      │                  [7] SessionLogger    │              │
│      │                  Log to sessions.csv  │              │
│      │                      │                 │              │
│      │                  [8] Unlock next     │              │
│      │                  level_unlocked[n]   │              │
│                                                              │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                    CSV LOGGING SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SessionLogger (data_logging.py)                            │
│                                                               │
│  log_session(level, duration, score, smoothness, ...)       │
│       │                                                       │
│       └─→ sessions.csv                                       │
│           ┌───────────────────────────────────────────┐      │
│           │ timestamp │ level │ score │ smoothness  │      │
│           ├───────────────────────────────────────────┤      │
│           │ 2026-01-02 10:30:45 │ 1 │ 100.0 │ 85.2  │      │
│           │ 2026-01-02 10:31:20 │ 2 │ 95.5  │ 82.1  │      │
│           │ 2026-01-02 10:32:10 │ 3 │ 98.7  │ 87.3  │      │
│           └───────────────────────────────────────────┘      │
│                                                               │
│  Used by:                                                    │
│  - Therapist for progress tracking                          │
│  - Performance analytics                                     │
│  - Rehabilitation effectiveness measurement                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Model Processing Pipeline

```
Input Image (MRI/Brain Scan)
         │
         ▼
    ┌─────────────────────────────────────┐
    │ Image Preprocessing                 │
    ├─────────────────────────────────────┤
    │ 1. PIL.Image.open() → Load image   │
    │ 2. .convert('L') → Grayscale        │
    │ 3. .resize((224,224)) → Resize     │
    │ 4. np.array() / 255 → Normalize     │
    │ 5. torch.tensor() → Convert to PT   │
    │ 6. .to(device) → GPU/CPU transfer  │
    └─────────────────────────────────────┘
         │
         ▼ [1, 1, 224, 224]
    ┌─────────────────────────────────────┐
    │ STAGE 1: ResNet50 Model             │
    ├─────────────────────────────────────┤
    │ Input channels: 1 (grayscale)       │
    │ Output: 2 classes                   │
    │ - Class 0: Non-Ischemic             │
    │ - Class 1: Ischemic                 │
    │                                      │
    │ forward(x) → logits [1, 2]          │
    │ softmax → probabilities              │
    │ argmax → class prediction            │
    └─────────────────────────────────────┘
         │
         ├─→ YES: Ischemic (pred=1)
         │       └─→ Return "Ischemic" + conf
         │
         └─→ NO: Non-Ischemic (pred=0)
                 ▼
         ┌─────────────────────────────────────┐
         │ STAGE 2: ResNet50 Model             │
         ├─────────────────────────────────────┤
         │ Input channels: 1 (grayscale)       │
         │ Output: 2 classes                   │
         │ - Class 0: Hemorrhagic              │
         │ - Class 1: Normal                   │
         │                                      │
         │ forward(x) → logits [1, 2]          │
         │ softmax → probabilities              │
         │ argmax → class prediction            │
         └─────────────────────────────────────┘
                 │
                 ├─→ Class 0 → "Hemorrhagic"
                 └─→ Class 1 → "Normal"
                 │
                 ▼
        Final Output: {
          "prediction": "Ischemic|Hemorrhagic|Normal",
          "confidence": 0.0-1.0
        }
```

---

## 📦 INSTALLATION & DEPLOYMENT

### Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd c:\Users\syeda\Documents\DL-Project\Stroke-Recovery-DL-

# Install all requirements
pip install -r requirements.txt
```

### Step 2: Verify Model Files

Ensure these files exist in project root:
```
✓ best_stage1_model.pth
✓ best_stage2_model.pth
✓ best.pt (for YOLO object detection)
```

### Step 3: (Optional) Setup .env

Edit `.env` file:
```
FLASK_DEBUG=1
PORT=5000
# Add later:
EMAIL=your_email@gmail.com
EMAIL_PASS=your_app_password
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/db
```

### Step 4: Run Desktop Game

```bash
python main.py
```

### Step 5: Run Web API

```bash
python app.py
# Opens: http://127.0.0.1:5000/
```

### Step 6: Run Flask in Production

```bash
# Using Gunicorn (better for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or using Waitress (Windows-friendly)
pip install waitress
waitress-serve --port=5000 app:app
```

---

## 🛠️ TECHNICAL STACK

### Backend Technologies

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| Web Framework | Flask | ≥2.0.0 | HTTP server, routing |
| CORS | Flask-Cors | ≥3.0.10 | Cross-origin requests |
| Deep Learning | PyTorch | ≥1.9.0 | Two-stage models |
| Vision | torchvision | ≥0.10.0 | ResNet50 architecture |
| Image Proc | Pillow | ≥9.0.0 | Image loading, resizing |
| CV | OpenCV | ≥4.5.5 | Video capture, drawing |
| Hand Track | MediaPipe | ≥0.10.0 | 21-point hand skeleton |
| Numerics | NumPy | ≥1.22.0 | Array operations |
| Detection | Ultralytics | ≥8.0.0 | YOLO object detection |
| GUI | tkinter | Built-in | Desktop UI |

### Frontend Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Markup | HTML5 | Page structure |
| Styling | CSS3 | UI design |
| Logic | JavaScript (Vanilla) | Form handling, API calls |
| HTTP | Fetch API | XMLHttpRequest replacement |
| Preview | Canvas API | Image preview |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|------------|
| Processor | i5 | i7/i9 or GPU |
| RAM | 8 GB | 16 GB |
| GPU | Optional | NVIDIA RTX 30/40 series |
| Webcam | 720p | 1080p+ |
| Disk | 2 GB | 5+ GB (for models) |
| OS | Windows 10+ | Windows 11 |

---

## 📋 COMPLETE REQUIREMENTS.txt

All required packages for both modes:

```txt
# ============ CORE DEPENDENCIES ============
# Web Framework
Flask>=2.0.0
Flask-Cors>=3.0.10

# Deep Learning & Models
torch>=1.9.0
torchvision>=0.10.0
ultralytics>=8.0.0

# Computer Vision & Hand Tracking
opencv-python>=4.5.5.64
mediapipe>=0.10.0

# Image & Data Processing
Pillow>=9.0.0
numpy>=1.22.0

# ============ OPTIONAL: PRODUCTION DEPLOYMENT ============
# For production Flask server
gunicorn>=20.1.0
# OR for Windows
waitress>=2.1.0

# ============ OPTIONAL: MONGODB (when adding database) ============
# pymongo>=4.0.0
# motor>=2.3.0  # async MongoDB driver

# ============ OPTIONAL: EMAIL (when adding notifications) ============
# python-dotenv>=0.19.0
# python-decouple>=3.5

# ============ OPTIONAL: TESTING ============
# pytest>=6.2.0
# pytest-flask>=1.2.0
```

---

## 🚀 QUICK START GUIDE

### Web Mode (Stroke Detection API)
```bash
# 1. Install
pip install -r requirements.txt

# 2. Start server
python app.py

# 3. Open browser
http://127.0.0.1:5000/

# 4. Upload MRI image
# → Get Hemorrhagic/Ischemic/Normal prediction
```

### Game Mode (Rehabilitation Game)
```bash
# 1. Install
pip install -r requirements.txt

# 2. Run game
python main.py

# 3. Play 10 rehabilitation levels
# → Progress tracked in sessions.csv
```

---

**Last Updated:** January 2, 2026  
**Documentation Version:** 2.0  
**Status:** ✅ Complete & Production-Ready
