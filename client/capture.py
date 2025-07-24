# capture.py
import mss
import mss.tools
import numpy as np
import cv2
import time

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss() # Inizializza mss
        # Definisci la regione dello schermo da catturare.
        # monitor_number = 1 per il monitor principale
        self.monitor = self.sct.monitors[1] # Cattura il monitor principale (generalmente il primo monitor dopo il "tutti i monitor")

    def get_frame(self):
        # Cattura lo schermo
        sct_img = self.sct.grab(self.monitor)
        
        # Converte l'immagine catturata da mss in un array NumPy.
        # `mss.grab()` restituisce un oggetto che, quando convertito a NumPy array,
        # produce un array con forma (altezza, larghezza, 4) in formato BGRA.
        frame = np.array(sct_img, dtype=np.uint8)

        # Converti da BGRA (mss) a BGR (OpenCV)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

    def get_frame_as_jpeg(self):
        frame = self.get_frame()
        if frame is not None:
            # Codifica l'immagine in formato JPEG con qualità 85
            ret, jpeg_frame = cv2.imencode('.jpeg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85]) 
            if ret:
                return jpeg_frame.tobytes()
        return None

if __name__ == "__main__":
    # Esempio di utilizzo: Cattura lo schermo e mostra in una finestra OpenCV
    # Questo blocco viene eseguito solo se capture.py è avviato direttamente
    capture = ScreenCapture()
    print("Premi 'q' per uscire dalla finestra di cattura.")
    while True:
        frame = capture.get_frame()
        if frame is not None:
            cv2.imshow("Test Cattura Schermo", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()