# remoto/technician/viewer.py

import cv2
import base64
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This flag will control if the OpenCV window is currently open
_is_cv_window_open = False

def mostra_immagine_cv(base64_data: str, window_name: str = "Schermo Remoto"):
    """
    Decodes a base64 string into an image and displays it in an OpenCV window.
    This function is primarily for standalone testing/debugging and will block
    the thread it's called from if not managed carefully (e.g., in a separate thread).

    Args:
        base64_data (str): The base64 encoded image data.
        window_name (str): The name of the OpenCV window.
    """
    global _is_cv_window_open
    try:
        img_bytes = base64.b64decode(base64_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is not None:
            cv2.imshow(window_name, frame)
            _is_cv_window_open = True

            # This waitKey is crucial. It processes GUI events for the OpenCV window.
            # A value of 1ms ensures it's non-blocking for this single call,
            # but if called in a loop, it will effectively "block" until 1ms passes.
            key = cv2.waitKey(1) & 0xFF

            # If 'q' is pressed or the window is closed manually
            if key == ord('q') or cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                cv2.destroyAllWindows()
                _is_cv_window_open = False
                return False # Indicate that the viewer should stop
            return True # Indicate that the viewer is still active
        else:
            logging.error("❌ Errore: Impossibile decodificare il frame dall'array NumPy.")
            return True
    except Exception as e:
        logging.error(f"❌ Errore nella visualizzazione con OpenCV: {e}", exc_info=True)
        return True # Continue trying unless an explicit stop is requested

def close_cv_window():
    """Closes all active OpenCV windows."""
    global _is_cv_window_open
    if _is_cv_window_open:
        cv2.destroyAllWindows()
        _is_cv_window_open = False
        logging.info("OpenCV window closed.")

# --- Example Usage (for standalone testing of this file) ---
if __name__ == "__main__":
    logging.info("This file demonstrates standalone OpenCV image display.")
    logging.info("It's generally NOT used directly when integrating with CustomTkinter.")
    logging.info("Generating a dummy red image for display. Press 'q' or close window to exit.")

    # Create a dummy red image (e.g., 640x480 red image)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dummy_frame[:, :, 2] = 255  # Set red channel to full intensity (BGR format)

    # Encode the dummy image to JPEG and then to base64
    ret, jpeg_encoded_frame = cv2.imencode('.jpeg', dummy_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if ret:
        base64_dummy_data = base64.b64encode(jpeg_encoded_frame.tobytes()).decode('utf-8')

        logging.info("Displaying dummy image...")
        # Simulate receiving frames
        try:
            while mostra_immagine_cv(base64_dummy_data):
                # In a real scenario, you'd get new base64_data here
                pass
        except KeyboardInterrupt:
            logging.info("\nDisplay interrupted by user.")
        finally:
            close_cv_window()
            logging.info("Viewer test finished.")
    else:
        logging.error("Failed to encode dummy image.")