# Smoking Detection - YOLO26n Training

Train a YOLO26n model on the [Roboflow smoking-tasfx dataset](https://universe.roboflow.com/richie-lab/smoking-tasfx) for deployment on Raspberry Pi 5.

## Dataset Info

- **Source:** Roboflow — [richie-lab/smoking-tasfx v4](https://universe.roboflow.com/richie-lab/smoking-tasfx)
- **License:** CC BY 4.0
- **Size:** ~450MB, 12,638 images
- **Classes (5):** Cigarette, Person, Smoke, Vape, smoking

## Files

| File | Purpose |
|---|---|
| `download_dataset.py` | Download dataset from Roboflow |
| `train_mac.py` | Train on Mac (Apple Silicon, MPS) |
| `detect_pi.py` | Live detection on Raspberry Pi 5 |
| `requirements.txt` | Python dependencies |

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Download dataset
```bash
python download_dataset.py
```

### 3. Train
```bash
python train_mac.py
```

## Training Configuration

The script uses these settings by default:

| Parameter | Value | Notes |
|---|---|---|
| `model` | yolo26n.pt | Nano variant — small & fast |
| `epochs` | 50 | Good balance |
| `imgsz` | 640 | Image resolution |
| `batch` | -1 | Auto-max for your VRAM |
| `cache` | ram | Fast data loading |
| `workers` | 8 | Parallel data loading |
| `device` | mps | Apple Silicon GPU |

## Expected Results

After 50 epochs on the full dataset:

| Metric | Value |
|---|---|
| mAP50 | ~0.64 |
| mAP50-95 | ~0.39 |
| Per-class (Person) | 0.94 mAP50 |
| Per-class (smoking) | 0.89 mAP50 |

## After Training

### Export to NCNN for Raspberry Pi deployment

```python
from ultralytics import YOLO
model = YOLO("runs/detect/train/weights/best.pt")
model.export(format="ncnn")
```

### Transfer to Raspberry Pi

```bash
scp -r runs/detect/train/weights/best_ncnn_model pi@<PI_IP>:~/smoking-detection/
```

### Run inference on Pi

```bash
# Using PyTorch weights
python3 detect_pi.py --model best.pt

# Or using NCNN (faster on Pi 5 ARM)
python3 detect_pi.py --model best_ncnn_model
```

Then open in browser: `http://<PI_IP>:8888`

The script:
- Captures frames from a USB webcam or Pi Camera
- Runs YOLO inference
- Serves annotated video as an MJPEG stream (no GUI required)
- Runs a threaded camera capture for better FPS

## Tips for Faster Training

1. **Use `cache="ram"`** — eliminates disk I/O bottleneck
2. **Increase `batch` size** — set `batch=-1` for auto-max
3. **Freeze backbone** — add `freeze=10` to only train detection head

## Troubleshooting

**`ModuleNotFoundError: No module named 'torch'`**
→ PyTorch doesn't support Python 3.13 yet. Use Python 3.12.

**Training very slow on Mac**
→ Verify MPS is active:
```python
import torch
print(torch.backends.mps.is_available())  # Should be True
```
