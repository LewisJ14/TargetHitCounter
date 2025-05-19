from flask import Flask, render_template, Response, request, redirect, url_for, jsonify, send_from_directory
import cv2
import os
import json
from datetime import datetime
import numpy as np
import threading
import time
import sys
import subprocess
import tempfile

app = Flask(__name__)

LIBCAMERA_VID_PORT = 8081

def start_libcamera_vid():
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = proc.info.get('cmdline')
        if cmdline and 'libcamera-vid' in ' '.join(cmdline):
            return  # Already running
    # Start libcamera-vid as MJPEG server
    cmd = [
        "libcamera-vid",
        "--inline",
        "-t", "0",
        "--width", "640",
        "--height", "480",
        "-o", f"tcp://0.0.0.0:{LIBCAMERA_VID_PORT}"
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

SCORES_FILE = 'scores.json'
SCREENSHOTS_DIR = 'screenshots'
BACKGROUND_FILE = 'background.jpg'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def capture_frame_libcamera():
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmpfile:
        tmp_path = tmpfile.name
    # Capture image using libcamera-still
    cmd = [
        "libcamera-still",
        "-o", tmp_path,
        "--width", "640",
        "--height", "480",
        "--nopreview",
        "-t", "1"
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        frame = cv2.imread(tmp_path)
        os.remove(tmp_path)
        return frame
    except Exception as e:
        print(f"libcamera-still failed: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return None

# Load or initialize scores
def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f)

scores = load_scores()

# Shooter management
@app.route('/add_shooter', methods=['POST'])
def add_shooter():
    name = request.form['name'].strip()
    if name and name not in scores:
        scores[name] = {'score': 0, 'shots': []}
        save_scores(scores)
    return redirect(url_for('index'))

@app.route('/remove_shooter', methods=['POST'])
def remove_shooter():
    name = request.form['name']
    if name in scores:
        del scores[name]
        save_scores(scores)
    return redirect(url_for('index'))

@app.route('/reset_scores', methods=['POST'])
def reset_scores():
    for shooter in scores:
        scores[shooter]['score'] = 0
        scores[shooter]['shots'] = []
    save_scores(scores)
    # Optionally clear screenshots
    for f in os.listdir(SCREENSHOTS_DIR):
        os.remove(os.path.join(SCREENSHOTS_DIR, f))
    return redirect(url_for('index'))

# Serve screenshots
@app.route('/screenshots/<filename>')
def screenshot(filename):
    return send_from_directory(SCREENSHOTS_DIR, filename)

# Main page
@app.route('/')
def index():
    return render_template('index.html', scores=scores)

# Capture background image
@app.route('/capture_background', methods=['POST'])
def capture_background():
    frame = capture_frame_libcamera()
    if frame is not None:
        cv2.imwrite(BACKGROUND_FILE, frame)
        return jsonify({'success': True})
    return jsonify({'success': False})

def load_background():
    if os.path.exists(BACKGROUND_FILE):
        return cv2.imread(BACKGROUND_FILE)
    return None

def detect_hits(background, frame, threshold=50, min_area=50):
    # Simple frame differencing for hit detection
    diff = cv2.absdiff(background, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hit_points = []
    for cnt in contours:
        if cv2.contourArea(cnt) > min_area:
            x, y, w, h = cv2.boundingRect(cnt)
            hit_points.append((x + w//2, y + h//2))
    return hit_points

def mark_hits(frame, hit_points):
    for idx, (x, y) in enumerate(hit_points):
        cv2.circle(frame, (x, y), 12, (0, 0, 255), 2)
        cv2.putText(frame, f"{idx+1}", (x+14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

# Register a hit for a shooter
@app.route('/register_hit', methods=['POST'])
def register_hit():
    shooter = request.form['shooter']
    if shooter in scores:
        background = load_background()
        if background is None:
            return jsonify({'success': False, 'error': 'No background set'})
        frame = capture_frame_libcamera()
        if frame is not None:
            hit_points = detect_hits(background, frame)
            if hit_points:
                mark_hits(frame, hit_points)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{shooter}_{timestamp}.jpg"
                filepath = os.path.join(SCREENSHOTS_DIR, filename)
                cv2.imwrite(filepath, frame)
                scores[shooter]['score'] += len(hit_points)
                scores[shooter]['shots'].append(filename)
                save_scores(scores)
                return jsonify({'success': True, 'filename': filename, 'score': scores[shooter]['score'], 'hits': len(hit_points)})
            else:
                return jsonify({'success': False, 'error': 'No hits detected'})
        else:
            return jsonify({'success': False, 'error': 'Failed to capture picture'})
    return jsonify({'success': False})

if __name__ == '__main__':
    start_libcamera_vid()
    app.run(host='0.0.0.0', port=5002, debug=True)
