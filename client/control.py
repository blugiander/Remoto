import pyautogui

def esegui_comando(data):
    if data['tipo'] == 'click':
        pyautogui.click(data['x'], data['y'])
    elif data['tipo'] == 'keypress':
        pyautogui.press(data['key'])
