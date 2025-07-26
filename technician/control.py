import json

def create_command_message(target_pin: str, command_type: str, data: dict) -> str:
    """
    Creates a JSON message string for a remote control command.

    Args:
        target_pin (str): The PIN of the client to send the command to.
        command_type (str): The type of command (e.g., 'mouse_click', 'mouse_move', 'key_press').
        data (dict): A dictionary containing command-specific data (e.g., {'x': 100, 'y': 200, 'button': 'left'}).

    Returns:
        str: A JSON string representing the command message.
    """
    # Validate command_type and data structure based on expected commands
    valid_command_types = [
        'mouse_click',
        'mouse_move',
        'mouse_scroll',
        'key_press',
        'key_down',
        'key_up',
        'mouse_drag' # Added mouse drag command
    ]

    if command_type not in valid_command_types:
        print(f"WARNING: Attempted to create an invalid command type: {command_type}")
        # You might raise an error here or return None/empty string depending on desired strictness
        # For now, we'll still attempt to send, but log a warning.

    message_content = {
        'command_type': command_type,
        'data': data
    }

    full_message = {
        'type': 'command', # The server expects type 'command' for control actions
        'role': 'technician',
        'target_id': target_pin, # Use the dynamic target_pin
        'content': message_content
    }
    return json.dumps(full_message)

# --- Example Usage (for testing purposes) ---
if __name__ == "__main__":
    test_pin = "123456" # A dummy PIN for testing

    # Example 1: Mouse click
    click_message = create_command_message(test_pin, 'mouse_click', {'x': 500, 'y': 300, 'button': 'left'})
    print(f"Click Message: {click_message}")

    # Example 2: Key press
    keypress_message = create_command_message(test_pin, 'key_press', {'key': 'enter'})
    print(f"Keypress Message: {keypress_message}")

    # Example 3: Mouse move
    mousemove_message = create_command_message(test_pin, 'mouse_move', {'x': 100, 'y': 150})
    print(f"Mouse Move Message: {mousemove_message}")

    # Example 4: Mouse scroll down
    mousescroll_message = create_command_message(test_pin, 'mouse_scroll', {'direction': 'down', 'amount': 3})
    print(f"Mouse Scroll Message: {mousescroll_message}")

    # Example 5: Key down (e.g., holding shift)
    keydown_message = create_command_message(test_pin, 'key_down', {'key': 'shift'})
    print(f"Key Down Message: {keydown_message}")

    # Example 6: Key up (e.g., releasing shift)
    keyup_message = create_command_message(test_pin, 'key_up', {'key': 'shift'})
    print(f"Key Up Message: {keyup_message}")

    # Example 7: Mouse drag
    mousedrag_message = create_command_message(test_pin, 'mouse_drag', {'x': 600, 'y': 400, 'button': 'left'})
    print(f"Mouse Drag Message: {mousedrag_message}")

    # Example 8: Invalid command type (will print a warning)
    invalid_message = create_command_message(test_pin, 'unknown_command', {'data': 'some_data'})
    print(f"Invalid Command Message: {invalid_message}")