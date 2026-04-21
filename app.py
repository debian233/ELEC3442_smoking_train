import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory, abort

DB_PATH = os.environ.get("DB_PATH", "detections.db")
DETECTIONS_DIR = os.environ.get("DETECTIONS_DIR", "detections")

app = Flask(__name__, static_folder="static", static_url_path="/static")


def db_connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def index():
    # Serve static/index.html when user hits /
    return send_from_directory(app.static_folder, "index.html")


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "db_path": DB_PATH,
        "db_exists": os.path.exists(DB_PATH),
        "detections_dir": DETECTIONS_DIR,
        "detections_dir_exists": os.path.exists(DETECTIONS_DIR),
    })


@app.get("/api/detections")
def get_detections():
    """
    Returns rows with only:
      - id
      - time (detected_at)
      - confidence
      - temperature
      - location (xc, yc)
      - image_url

    Query params:
      - limit (default 50, max 500)
      - offset (default 0)
      - class_name (optional)
      - min_conf (optional float)
    """
    limit = int(request.args.get("limit", 50))
    limit = max(1, min(limit, 500))
    offset = int(request.args.get("offset", 0))
    offset = max(0, offset)

    class_name = request.args.get("class_name")
    min_conf = request.args.get("min_conf")

    where = []
    params = []

    if class_name:
        where.append("class_name = ?")
        params.append(class_name)

    if min_conf is not None:
        try:
            min_conf_val = float(min_conf)
        except ValueError:
            return jsonify({"error": "min_conf must be a number"}), 400
        where.append("confidence >= ?")
        params.append(min_conf_val)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT
            id,
            detected_at,
            confidence,
            temperature,
            image_path,
            class_name,
            xc,
            yc
        FROM detections
        {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    conn = db_connect()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    out = []
    for r in rows:
        image_path = r["image_path"]
        filename = os.path.basename(image_path) if image_path else None

        out.append({
            "id": r["id"],
            "time": r["detected_at"],
            "confidence": r["confidence"],
            "temperature": r["temperature"],
            "location": {
                "xc": r["xc"],
                "yc": r["yc"],
            },
            "image_url": f"/detections/{filename}" if filename else None,
            # Keeping class_name in response is optional; dashboard ignores it.
            "class_name": r["class_name"],
        })

    return jsonify(out)


@app.get("/api/stats")
def get_stats():
    """
    Lightweight stats used by the header:
      - total rows
      - latest (id, time)
    """
    conn = db_connect()
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM detections").fetchone()["c"]
        latest = conn.execute("""
            SELECT id, detected_at
            FROM detections
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()
    finally:
        conn.close()

    return jsonify({
        "total_detections": total,
        "latest": ({
            "id": latest["id"],
            "time": latest["detected_at"],
        } if latest else None)
    })


@app.get("/detections/<path:filename>")
def serve_detection_image(filename):
    if not os.path.exists(DETECTIONS_DIR):
        abort(404)
    return send_from_directory(DETECTIONS_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)