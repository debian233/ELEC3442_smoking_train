"""
Smoking Detection - Live Camera Feed using local YOLO model
Raspberry Pi 5 + Pi Camera / USB Webcam
Streams annotated video via built-in MJPEG HTTP server.

Usage:
    python3 detect_local.py --model best.pt
    python3 detect_local.py --model best_ncnn_model --imgsz 320
    python3 detect_local.py --model best.pt --conf 0.5 --save

    Then open browser: http://<PI_IP>:8888
"""

import argparse
import threading
import time
import cv2
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from ultralytics import YOLO
# 1. At the top, import the module
from db import init_db, insert_detection

# Create a folder for images if it doesn't exist
if not os.path.exists('detections'):
    os.makedirs('detections')

# Shared frame for streaming
latest_frame = None
frame_lock = threading.Lock()

# Threaded camera capture
current_frame = None
camera_lock = threading.Lock()
camera_running = True


class CameraThread(threading.Thread):
    """Capture frames in a separate thread to avoid blocking inference."""
    def __init__(self, cap):
        super().__init__(daemon=True)
        self.cap = cap

    def run(self):
        global current_frame, camera_running
        while camera_running:
            ret, frame = self.cap.read()
            if not ret:
                break
            with camera_lock:
                current_frame = frame


class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <html><head><title>Smoking Detection</title></head>
            <body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh">
                <img src="/stream" style="max-width:100%;max-height:100vh">
            </body></html>
            """)
        elif self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary=--frame")
            self.end_headers()
            try:
                while True:
                    with frame_lock:
                        frame = latest_frame
                    if frame is not None:
                        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode())
                        self.wfile.write(jpeg.tobytes())
                        self.wfile.write(b"\r\n")
                    time.sleep(0.03)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def start_server(port):
    server = HTTPServer(("0.0.0.0", port), MJPEGHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def parse_args():
    parser = argparse.ArgumentParser(description="Smoking Detection with Local YOLO Model")
    parser.add_argument("--model", type=str, required=True, help="Path to YOLO weights (.pt or NCNN folder)")
    parser.add_argument("--source", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--conf", type=float, default=0.4, help="Confidence threshold (default: 0.4)")
    parser.add_argument("--save", action="store_true", help="Save frames with detections")
    parser.add_argument("--imgsz", type=int, default=320, help="Inference image size (default: 320)")
    parser.add_argument("--width", type=int, default=640, help="Camera frame width")
    parser.add_argument("--height", type=int, default=480, help="Camera frame height")
    parser.add_argument("--port", type=int, default=8888, help="HTTP stream port (default: 8888)")
    parser.add_argument("--no-stream", action="store_true", help="Disable HTTP stream, terminal only")
    return parser.parse_args()


def main():
    global latest_frame, camera_running
    args = parse_args()

    # Load model
    print(f"[INFO] Loading model: {args.model}")
    model = YOLO(args.model)
    print(f"[INFO] Model loaded. Classes: {model.names}")
    init_db()
    # Open camera
    print(f"[INFO] Opening camera {args.source}...")
    cap = cv2.VideoCapture(args.source)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize camera buffer lag

    if not cap.isOpened():
        print("[ERROR] Cannot open camera. Try a different --source index.")
        return

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Camera opened: {actual_w}x{actual_h}")

    # Start threaded camera capture
    cam_thread = CameraThread(cap)
    cam_thread.start()
    time.sleep(0.5)  # Let camera warm up

    # Start HTTP stream
    if not args.no_stream:
        start_server(args.port)
        print(f"[INFO] Stream ready at:")
        print(f"       http://localhost:{args.port}")
        print(f"       http://10.0.20.67:{args.port}")

    print(f"[INFO] Confidence threshold: {args.conf}")
    print(f"[INFO] Inference size: {args.imgsz}")
    print(f"[INFO] Press Ctrl+C to stop\n")

    frame_count = 0
    detection_count = 0
    fps_list = []

    try:
        while True:
            # Get latest frame from camera thread
            with camera_lock:
                frame = current_frame
            if frame is None:
                time.sleep(0.01)
                continue

            start = time.time()

            # Run inference
            results = model(frame, imgsz=args.imgsz, conf=args.conf, verbose=False)
            elapsed = time.time() - start
            fps = 1.0 / elapsed if elapsed > 0 else 0
            fps_list.append(fps)

            # Get annotated frame
            annotated = results[0].plot()

            # Add FPS overlay
            avg_fps = sum(fps_list[-30:]) / len(fps_list[-30:])
            cv2.putText(annotated, f"FPS: {avg_fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Update shared frame for stream
            with frame_lock:
                latest_frame = annotated

            # Log detections
            frame_count += 1
            boxes = results[0].boxes
            if len(boxes) > 0:
                # BACKEND LOGIC implemented here. 
                detection_count += 1
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = model.names[cls_id]

                    # Store the data into SQLite database
                    # Store to SQLite  ← replaces the old comment
                    # Save image first so we have the path ready
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"detections/smoker_{ts}_{frame_count}.jpg"
                    cv2.imwrite(filename, annotated)
                    insert_detection(
                        confidence=conf,
                        image_path=filename,
                        class_name=cls_name,
                    )
                    # You can use the 'sqlite3' library to connect and insert data into your database

                    print(f"[Frame {frame_count}] {cls_name} ({conf:.0%}) | {fps:.1f} FPS")

                if args.save:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Save inside the 'detections' folder
                    filename = f"detections/smoker_{ts}_{frame_count}.jpg"
                    cv2.imwrite(filename, annotated)
                    print(f"  -> Saved: {filename}")
            else:
                print(f"[Frame {frame_count}] No detection | {fps:.1f} FPS", end="\r")

    except KeyboardInterrupt:
        avg = sum(fps_list) / len(fps_list) if fps_list else 0
        print(f"\n\n[INFO] Stopped.")
        print(f"[INFO] Frames: {frame_count} | Detections: {detection_count} | Avg FPS: {avg:.1f}")
    finally:
        camera_running = False
        cap.release()


if __name__ == "__main__":
    main()
