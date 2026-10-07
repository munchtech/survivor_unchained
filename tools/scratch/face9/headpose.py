"""headpose.py img[@crop] ...: the face's pitch, yaw and roll (degrees; pitch + chin up) from MediaPipe's facial
transformation matrix; the brow-to-eye gap and nose length over the face's height (10 to 152); and, over the eye's
own width (a local yardstick), the brow-to-lid gap, the gap under the brow's lower edge, and the brow's own height;
and how far down the face the eyes sit."""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\tools\assets")
import face_fit as ff  # noqa: E402
import mediapipe as mp  # noqa: E402
from mediapipe.tasks.python import BaseOptions, vision  # noqa: E402

opts = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=ff.MODEL), num_faces=1,
                                    output_facial_transformation_matrixes=True)
with vision.FaceLandmarker.create_from_options(opts) as lm:
    for p in sys.argv[1:]:
        crop = None
        if '@' in p:
            p, c = p.split('@')
            crop = [int(v) for v in c.split(',')]
        im = Image.open(p).convert('RGB')
        if crop:
            im = im.crop(crop)
        if im.height < 900:
            im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
        a = np.ascontiguousarray(np.asarray(im))
        r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=a))
        if not r.face_landmarks:
            print(p, 'no face')
            continue
        M = np.array(r.facial_transformation_matrixes[0])[:3, :3]
        pitch = np.degrees(np.arctan2(-M[1, 2], M[2, 2]))
        yaw = np.degrees(np.arcsin(np.clip(M[0, 2], -1, 1)))
        roll = np.degrees(np.arctan2(-M[0, 1], M[0, 0]))
        L = np.array([[q.x * a.shape[1], q.y * a.shape[0]] for q in r.face_landmarks[0]])
        h = np.linalg.norm(L[152] - L[10])
        gap = (np.linalg.norm(L[105] - L[159]) + np.linalg.norm(L[334] - L[386])) / 2 / h
        nose = np.linalg.norm(L[168] - L[2]) / h
        ew = (np.linalg.norm(L[33] - L[133]) + np.linalg.norm(L[263] - L[362])) / 2
        g2 = (np.linalg.norm(L[105] - L[159]) + np.linalg.norm(L[334] - L[386])) / 2 / ew
        lo = (np.linalg.norm(L[52] - L[159]) + np.linalg.norm(L[282] - L[386])) / 2 / ew
        bh = (np.linalg.norm(L[105] - L[52]) + np.linalg.norm(L[334] - L[282])) / 2 / ew
        ey = (L[[33, 133, 263, 362], 1].mean() - L[10, 1]) / h
        name = p.replace('\\', '/').split('/')
        name = ("/".join(name[-2:]))[-28:]
        print('%-28s pitch %+5.1f yaw %+5.1f | brow-eye %.3f nose %.3f | /eye w: gap %.3f under-brow %.3f brow h %.3f | eyes %.3f down' % (
            name, pitch, yaw, gap, nose, g2, lo, bh, ey))
