"""
Download the smoking detection dataset from Roboflow.
Saves to ./smoking-dataset/
"""

from roboflow import Roboflow

API_KEY = "YOUR_API_KEY"  # Get from https://app.roboflow.com/settings/api
WORKSPACE = "richie-lab"
PROJECT = "smoking-tasfx"
VERSION = 4

print(f"Downloading {PROJECT} v{VERSION}...")
rf = Roboflow(api_key=API_KEY)
project = rf.workspace(WORKSPACE).project(PROJECT)
dataset = project.version(VERSION).download("yolov8", location="smoking-dataset")

print(f"\nDone! Dataset at: {dataset.location}")
