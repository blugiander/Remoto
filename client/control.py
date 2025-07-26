import pyautogui
import time

class CommandExecutor:
    def __init__(self):
        # Optional: Configure pyautogui settings
        # Fail-safe: Moving the mouse to the top-left corner will abort the program.
        pyautogui.FAILSAFE = False 
        # Pause: Add a small delay after each pyautogui call (in seconds)
        pyautogui.PAUSE = 0.01 
        print("CommandExecutor initialized. PyAutoGUI FAILSAFE is OFF and PAUSE is 0.01 seconds.")

    def execute_command(self, data):
        """
        Executes a remote command based on the provided data dictionary.

        Args:
            data (dict): A dictionary containing 'command_type' and 'data' for the command.
                         Expected structure:
                         {
                             "command_type": "mouse_click" | "mouse_move" | "mouse_scroll" | "key_press" | "key_down" | "key_up",
                             "data": { ... command-specific data ... }
                         }
        """
        command_type = data.get('command_type')
        command_data = data.get('data')

        if not command_type or not command_data:
            print(f"ERROR: Invalid command format received: {data}")
            return

        try:
            if command_type == 'mouse_click':
                x = command_data.get('x')
                y = command_data.get('y')
                button = command_data.get('button', 'left') # Default to left click
                
                if x is not None and y is not None:
                    pyautogui.click(x=x, y=y, button=button)
                    # print(f"DEBUG: Clicked {button} at ({x}, {y})")
                else:
                    print(f"WARNING: Mouse click command missing x or y coordinates: {command_data}")

            elif command_type == 'mouse_move':
                x = command_data.get('x')
                y = command_data.get('y')
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y, duration=0) # duration=0 for immediate movement
                    # print(f"DEBUG: Mouse moved to ({x}, {y})")
                else:
                    print(f"WARNING: Mouse move command missing x or y coordinates: {command_data}")
            
            elif command_type == 'mouse_drag':
                x = command_data.get('x')
                y = command_data.get('y')
                button = command_data.get('button', 'left')
                if x is not None and y is not None:
                    pyautogui.dragTo(x, y, button=button, duration=0)
                    # print(f"DEBUG: Mouse dragged to ({x}, {y}) with {button} button")
                else:
                    print(f"WARNING: Mouse drag command missing x or y coordinates: {command_data}")

            elif command_type == 'mouse_scroll':
                direction = command_data.get('direction')
                amount = command_data.get('amount', 1) # Default scroll amount
                
                if direction == 'up':
                    pyautogui.scroll(amount)
                    # print(f"DEBUG: Scrolled up by {amount}")
                elif direction == 'down':
                    pyautogui.scroll(-amount)
                    # print(f"DEBUG: Scrolled down by {amount}")
                else:
                    print(f"WARNING: Invalid scroll direction: {direction}")

            elif command_type == 'key_press':
                key = command_data.get('key')
                if key:
                    pyautogui.press(key)
                    # print(f"DEBUG: Pressed key: {key}")
                else:
                    print(f"WARNING: Key press command missing key: {command_data}")

            elif command_type == 'key_down':
                key = command_data.get('key')
                if key:
                    pyautogui.keyDown(key)
                    # print(f"DEBUG: Key down: {key}")
                else:
                    print(f"WARNING: Key down command missing key: {command_data}")

            elif command_type == 'key_up':
                key = command_data.get('key')
                if key:
                    pyautogui.keyUp(key)
                    # print(f"DEBUG: Key up: {key}")
                else:
                    print(f"WARNING: Key up command missing key: {command_data}")

            else:
                print(f"WARNING: Unknown command type: {command_type}")

        except Exception as e:
            print(f"ERROR: Failed to execute command '{command_type}': {e}. Data: {data}")

if __name__ == "__main__":
    # This block is for testing purposes only
    executor = CommandExecutor()
    print("Test CommandExecutor. Moving mouse to center, clicking, typing 'hello', then scrolling.")
    print("Ensure you have control over your mouse/keyboard before running this test.")
    print("Ctrl+C to stop the test.")

    try:
        # Get screen size to move mouse to center
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2

        print(f"Moving mouse to center ({center_x}, {center_y})...")
        executor.execute_command({"command_type": "mouse_move", "data": {"x": center_x, "y": center_y}})
        time.sleep(1)

        print("Clicking left button...")
        executor.execute_command({"command_type": "mouse_click", "data": {"x": center_x, "y": center_y, "button": "left"}})
        time.sleep(1)

        print("Typing 'hello world'...")
        # Note: pyautogui.write is typically better for typing full strings
        # For remote control, individual key presses are often sent.
        # Let's simulate pressing each character.
        for char in "hello world":
            executor.execute_command({"command_type": "key_press", "data": {"key": char}})
            time.sleep(0.1) # Small delay between keys
        
        executor.execute_command({"command_type": "key_press", "data": {"key": "enter"}})
        time.sleep(1)

        print("Scrolling down...")
        executor.execute_command({"command_type": "mouse_scroll", "data": {"direction": "down", "amount": 10}})
        time.sleep(1)
        
        print("Scrolling up...")
        executor.execute_command({"command_type": "mouse_scroll", "data": {"direction": "up", "amount": 10}})
        time.sleep(1)

        print("Test complete.")

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"An error occurred during test: {e}")