from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import torch
import torch.nn as nn
from torchvision import models
import os
import tempfile
import uuid
import threading
import subprocess
from PIL import Image
import numpy as np
import sys

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============ LOAD MODELS ============
stage1_model = models.resnet50(pretrained=False)
stage1_model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
stage1_model.fc = nn.Linear(stage1_model.fc.in_features, 2)
stage1_model.load_state_dict(torch.load("best_stage1_model.pth", map_location=device))
stage1_model.to(device).eval()

stage2_model = models.resnet50(pretrained=False)
stage2_model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
stage2_model.fc = nn.Linear(stage2_model.fc.in_features, 2)
stage2_model.load_state_dict(torch.load("best_stage2_model.pth", map_location=device))
stage2_model.to(device).eval()

CLASS_MAP = {0: "Hemorrhagic", 1: "Ischemic", 2: "Normal"}

# ============ UTILS ============
def load_tensor(path):
    img = Image.open(path).convert("L").resize((224, 224))
    img = np.array(img) / 255.0
    tensor = torch.tensor(img).unsqueeze(0).unsqueeze(0).float().to(device)
    return tensor

def predict_stroke(image_path):
    """Two-stage stroke prediction using stage1 and stage2 models"""
    x = load_tensor(image_path)
    
    # Stage 1
    out1 = stage1_model(x)
    p1 = torch.argmax(out1, dim=1).item()
    
    if p1 == 1:  # Ischemic
        final = 1
        confidence = torch.softmax(out1, dim=1)[0, 1].item()
    else:
        # Stage 2
        out2 = stage2_model(x)
        p2 = torch.argmax(out2, dim=1).item()
        final = 0 if p2 == 0 else 2
        confidence = torch.softmax(out2, dim=1)[0, p2].item()
    
    return CLASS_MAP[final], float(confidence)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/options")
def options():
    return render_template("options.html")


@app.route("/verify")
def verify():
    return render_template("verify.html")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image file provided"}), 400
    f = request.files["image"]
    if f.filename == "":
        return jsonify({"success": False, "message": "Empty filename"}), 400

    tmpdir = tempfile.gettempdir()
    filename = f"predict_{uuid.uuid4().hex}.png"
    path = os.path.join(tmpdir, filename)
    f.save(path)

    try:
        label, confidence = predict_stroke(path)
        return jsonify({"success": True, "prediction": label, "confidence": confidence})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def _launch_game():
    try:
        # use the same python executable running this server
        python_exec = sys.executable or "python"
        cwd = os.path.abspath(os.path.dirname(__file__))
        subprocess.Popen([python_exec, "main.py"], cwd=cwd)
    except Exception:
        pass


@app.route("/play")
def play():
    # start the game in background and return a small page telling user it's launched
    thread = threading.Thread(target=_launch_game, daemon=True)
    thread.start()
    return render_template("play_started.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
