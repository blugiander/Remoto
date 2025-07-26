import mss
import mss.tools
import numpy as np
import cv2
import time
import sys # Import sys for clean exit in case of no monitor

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss() # Initialize mss

        # Define the screen region to capture.
        # monitor_number = 1 for the main monitor (after 'all monitors' at index 0)
        
        # Check if there are enough monitors to select index 1
        if len(self.sct.monitors) > 1:
            self.monitor = self.sct.monitors[1] # Capture the main monitor (usually the first monitor after "all monitors")
            print(f"ScreenCapture: Using monitor: {self.monitor}")
        else:
            print("ScreenCapture Error: Not enough monitors detected to select monitor index 1.")
            print("ScreenCapture: Available monitors:", self.sct.monitors)
            print("ScreenCapture: Please ensure you have at least one external monitor or try adjusting monitor index.")
            self.monitor = None # Set monitor to None to indicate an error state

    def get_frame(self):
        if self.monitor is None:
            return None # Return None if no valid monitor was found during initialization

        try:
            # Capture the screen
            sct_img = self.sct.grab(self.monitor)
            
            # Convert the captured image from mss into a NumPy array.
            # `mss.grab()` returns an object which, when converted to a NumPy array,
            # produces an array with shape (height, width, 4) in BGRA format.
            frame = np.array(sct_img, dtype=np.uint8)

            # Convert from BGRA (mss) to BGR (OpenCV)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
        except mss.exception.ScreenShotError as e:
            print(f"ScreenCapture Error: Failed to grab screen: {e}")
            return None
        except Exception as e:
            print(f"ScreenCapture Error: An unexpected error occurred in get_frame: {e}")
            return None

    def get_frame_as_jpeg(self):
        frame = self.get_frame()
        if frame is not None:
            # Encode the image in JPEG format with quality 85
            # cv2.IMWRITE_JPEG_QUALITY is already an int, no need for int() cast
            ret, jpeg_frame = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85]) 
            if ret:
                return jpeg_frame.tobytes()
        return None

if __name__ == "__main__":
    # Example usage: Capture the screen and display in an OpenCV window
    # This block is executed only if capture.py is run directly
    capture = ScreenCapture()
    
    if capture.monitor is None:
        print("Exiting. No valid monitor found for capture.")
        sys.exit(1) # Exit if no monitor was set up

    print("Press 'q' to exit the capture window.")
    
    start_time = time.time()
    frame_count = 0

    while True:
        frame = capture.get_frame()
        if frame is not None:
            cv2.imshow("Test Schermo Remoto - Premi 'q' per uscire", frame)
            frame_count += 1
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        # Optional: Calculate and print FPS every few seconds
        if time.time() - start_time >= 5: # Print FPS every 5 seconds
            fps = frame_count / (time.time() - start_time)
            print(f"FPS: {fps:.2f}")
            frame_count = 0
            start_time = time.time()
            
    cv2.destroyAllWindows()
    print("Test cattura schermo terminato.")