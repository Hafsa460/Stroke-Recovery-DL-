# Stroke-Recovery-DL-

## DL Integration

Place your trained model `best.pt` in the project root to enable optional YOLOv8-based object detection. The game will run without the model or `ultralytics` installed — DL features are lazy-initialized and optional.

Quick checks:

- Install dependencies: `pip install -r requirements.txt`
- Verify model load: `python test_model_load.py`
