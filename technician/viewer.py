import cv2, base64, numpy as np

def mostra_immagine(base64_data):
    frame = cv2.imdecode(np.frombuffer(base64.b64decode(base64_data), np.uint8), cv2.IMREAD_COLOR)
    if frame is not None:
        cv2.imshow("Schermo Remoto", frame)
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
