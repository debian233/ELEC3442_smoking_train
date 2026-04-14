"""
Smoking Detection - Train YOLO26n on Mac M5 Pro
Optimized for 48GB unified memory + MPS GPU

Usage:
    cd ~/smoking-detection
    python3 train.py
"""

import os
from ultralytics import YOLO


def main():
    # Load YOLO26n pretrained weights (auto-downloads)
    model = YOLO("yolo26n.pt")

    # Train
    results = model.train(
        data="smoking-dataset/data.yaml",
        epochs=50,
        imgsz=640,
        batch=-1,        # auto-max batch size for 48GB
        device="mps",    # Apple Silicon GPU
        workers=8,       # M5 Pro 20 cores
        cache="ram",     # cache images in RAM (48GB plenty)
        project="runs",
        name="yolo26n",
    )

    # Find the best weights
    best_path = os.path.join(str(results.save_dir), "weights", "best.pt")
    if not os.path.exists(best_path):
        print(f"\nERROR: best.pt not found at {best_path}")
        print("Training may have failed. Check the logs above.")
        return

    print(f"\nWeights saved to: {best_path}")

    # Validate
    best = YOLO(best_path)
    metrics = best.val()
    print(f"\nmAP50:    {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")

    # Export to NCNN (optimized for Raspberry Pi 5 ARM CPU)
    best.export(format="ncnn")
    print("\nDone! Files ready:")
    print(f"  PyTorch:  {best_path}")
    print(f"  NCNN:     {best_path.replace('best.pt', 'best_ncnn_model/')}")
    print("\nTransfer to Pi:")
    print(f"  scp {best_path} pi@10.0.20.67:~/smoking-detection/")


if __name__ == "__main__":
    main()
