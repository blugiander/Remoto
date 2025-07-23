import cv2
import base64
import numpy as np

def mostra_immagine(base64_data):
    img_bytes = base64.b64decode(base64_data)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is not None:
        cv2.imshow("Schermo remoto", frame)
        cv2.waitKey(1)
