from flask import Flask, request, Response, jsonify
import cv2
import numpy as np
from threading import Lock
from ultralytics import YOLO

app = Flask(__name__)
model = YOLO(r"C:\Users\Shriyansh\Downloads\WORk\mv_prj\runs\segment\train\weights\last.pt")


prev_gray   = {}     # roadID -> previous gray frame
counts      = {}     # roadID -> stopped cars no.
counts_lock = Lock()

ROAD_ORDER   = ['A','B','C','D']
last_served  = None

FLOW_THRESH = 0.5  # threshold: avg optical‑flow magnitude below this = “stopped”
PILEUP_Y_THRESH = 100  # threshold for bbox height to consider it as pileup
PILEUP_CAR_ESTIMATE = 3  # estimate how many cars are piled per large bbox
@app.route('/detect', methods=['POST'])
def detect():
    road = request.form.get('roadID', 'Unknown')
    img  = cv2.imdecode(np.frombuffer(request.files['image'].read(), np.uint8), cv2.IMREAD_COLOR)
    raw  = img.copy()
        #Build optical flow mask

    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    if road not in prev_gray:
        prev_gray[road] = gray
        flow = np.zeros((gray.shape[0], gray.shape[1], 2), dtype=np.float32)
    else:
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray[road], gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        prev_gray[road] = gray

    results = model(raw, classes=[2])[0]
    try:
        boxes = results.boxes.xyxy.cpu().numpy().astype(int)
    except:
        boxes = results.boxes.xyxy.numpy().astype(int)

    stopped_boxes = []
    moving_boxes = []

    for (x1, y1, x2, y2) in boxes:
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(raw.shape[1], x2), min(raw.shape[0], y2)
        crop = flow[y1:y2, x1:x2]
        if crop.size == 0:
            moving_boxes.append((x1, y1, x2, y2))
            continue

        mag, _ = cv2.cartToPolar(crop[...,0], crop[...,1])
        avg_mag = float(np.mean(mag))

        if avg_mag < FLOW_THRESH:
            stopped_boxes.append((x1, y1, x2, y2))
        else:
            moving_boxes.append((x1, y1, x2, y2))
    #Estimate actual stopped car count using bbox height

    estimated_stopped = 0
    for (x1, y1, x2, y2) in stopped_boxes:
        height = y2 - y1
        if height > PILEUP_Y_THRESH:
            estimated_stopped += PILEUP_CAR_ESTIMATE
        else:
            estimated_stopped += 1
    # Draw overlay
    annotated = raw.copy()
    for (x1, y1, x2, y2) in moving_boxes:
        cv2.rectangle(annotated, (x1,y1), (x2,y2), (0,255,0), 2)
    for (x1, y1, x2, y2) in stopped_boxes:
        cv2.rectangle(annotated, (x1,y1), (x2,y2), (0,0,255), 2)
# road stopped moving

    text = f"R {road} S:{estimated_stopped} M:{len(moving_boxes)}"
    cv2.putText(annotated, text, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)

    with counts_lock:
        counts[road] = estimated_stopped

    ok, buf = cv2.imencode('.jpg', annotated)
    if not ok:
        return Response("Encoding failed", status=500)
    return Response(buf.tobytes(), mimetype='image/jpeg')

@app.route('/decide', methods=['GET'])
def decide():
    global last_served

    with counts_lock:
        if not counts:
            chosen_road, q = 'A', 0
        else:
            max_q = max(counts.values())
            candidates = [r for r,v in counts.items() if v == max_q]
            start = (ROAD_ORDER.index(last_served) + 1) % len(ROAD_ORDER) if last_served in ROAD_ORDER else 0
            for i in range(len(ROAD_ORDER)):
                r = ROAD_ORDER[(start + i) % len(ROAD_ORDER)]
                if r in candidates:
                    chosen_road = r
                    break
            q = counts[chosen_road]
        last_served = chosen_road

    road_map = {'A':0,'B':1,'C':2,'D':3}
    idx = road_map.get(chosen_road, 0)
    wait = 5.0 + 0.5 * q
    return jsonify({'next': idx, 'wait': wait})

if __name__ == '__main__':
    app.run(port=5000, threaded=True)
