"""Video of a performer made into motion for her: SAM 3D Body in the local
ComfyUI (Meta, SAM License; its Momentum Human Rig is Apache 2.0).

    python tools/anim/video_motion.py <video> <name> [--start S] [--seconds N] [--fps F] [--smooth W]

The stretch of the video is cut and scaled (ffmpeg), handed to ComfyUI
(http://127.0.0.1:8188) as a workflow: frames out of the video, SAM 3D
Body's body (and hands) recovered on each frame, smoothed over time, and
written as BVH (cm). The BVH lands as C:/Users/munch/Tools/mocap/video/
<name>.bvh, and clips/generated.py's table makes it a clip of hers.

For the owner's own phone video: film one person, whole body in frame
head to feet with some floor below, the phone still (propped, not held),
side-on or three-quarters for anything that moves forward and back, plain
light; then run this on it and add a row to clips/generated.py's TABLE.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

COMFY = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
COMFY_DIR = Path(os.environ.get("COMFY_SHARED", r"C:\Users\munch\AppData\Local\Comfy-Desktop\ComfyUI-Shared"))
FFMPEG = os.environ.get("FFMPEG", r"C:\Users\munch\vo-tools\ffmpeg\bin\ffmpeg.exe")
OUT = Path(os.environ.get("MOCAP_DIR", r"C:\Users\munch\Tools\mocap")) / "video"


def cut(video, name, start, seconds, fps, height=960):
    """The stretch wanted, at a size SAM 3D Body works well with."""
    dst = COMFY_DIR / "input" / f"anim_{name}.mp4"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", str(start), "-t", str(seconds), "-i", str(video),
                    "-vf", f"fps={fps},scale=-2:{height}", "-an", "-c:v", "libx264", "-crf", "16", str(dst)], check=True)
    return dst.name


def workflow(video_file, fps, smooth):
    return {
        "1": {"class_type": "LoadVideo", "inputs": {"file": video_file}},
        "2": {"class_type": "GetVideoComponents", "inputs": {"video": ["1", 0]}},
        "3": {"class_type": "SAM3DBody_Loader", "inputs": {"model_file": "sam_3d_body_dinov3_bf16.safetensors"}},
        "4": {"class_type": "SAM3DBody_Predict", "inputs": {"sam3d_body_model": ["3", 0], "image": ["2", 0],
                                                             "run_hand_refinement": True, "fov": 0.0, "batch_size": 8}},
        "5": {"class_type": "SAM3DBody_Smooth", "inputs": {"mhr_pose_data": ["4", 0], "strength": 1.0, "method": "savgol",
                                                            "window": smooth, "rotation_threshold_degrees": 30.0}},
        "6": {"class_type": "BuildPoseFile", "inputs": {"pose_data": ["5", 0], "format": "bvh", "format.units": "cm",
                                                         "fps": float(fps), "camera_translation": "centered",
                                                         "track_index": 0, "sam3d_body_model": ["3", 0]}},
        "7": {"class_type": "SaveGLB", "inputs": {"mesh": ["6", 0], "filename_prefix": "anim/video_motion"}},
    }


def post(prompt):
    req = urllib.request.Request(f"{COMFY}/prompt", data=json.dumps({"prompt": prompt}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["prompt_id"]


def wait(pid, timeout=3600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(f"{COMFY}/history/{pid}") as r:
            h = json.load(r)
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(json.dumps(st)[:2000])
            if st.get("completed"):
                return h[pid]
        time.sleep(3)
    raise TimeoutError(pid)


def run(video, name, start=0.0, seconds=10.0, fps=30, smooth=9):
    f = cut(video, name, start, seconds, fps)
    since = time.time()
    pid = post(workflow(f, fps, smooth))
    hist = wait(pid)
    # The BVH Save wrote, newest first.
    outs = sorted((COMFY_DIR / "output" / "anim").glob("video_motion*"), key=lambda p: p.stat().st_mtime, reverse=True)
    outs = [p for p in outs if p.stat().st_mtime >= since - 1]
    if not outs:
        raise RuntimeError("no output: " + json.dumps(hist.get("outputs", {}))[:1000])
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / f"{name}.bvh"
    shutil.copy(outs[0], dst)
    return dst


def main(argv):
    video, name = argv[0], argv[1]
    kw = {}
    i = 2
    while i < len(argv):
        k, v = argv[i][2:], argv[i + 1]
        kw[k] = float(v) if k in ("start", "seconds") else int(v)
        i += 2
    print(run(video, name, **kw))


if __name__ == "__main__":
    main(sys.argv[1:])
