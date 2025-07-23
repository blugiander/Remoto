import mss, cv2, numpy as np, base64

def cattura_schermo():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        _, buf = cv2.imencode('.jpg', img)
        return base64.b64encode(buf).decode('utf-8')
