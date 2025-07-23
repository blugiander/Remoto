import mss
import cv2
import numpy as np
from PIL import Image
import io
import base64

def cattura_schermo():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        _, buf = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buf).decode('utf-8')
        return img_base64
