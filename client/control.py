import pyautogui

def esegui_comando(data):
    tipo = data.get('tipo')
    if tipo == 'click':
        x, y = data['x'], data['y']
        pyautogui.click(x, y)
    elif tipo == 'keypress':
        key = data['key']
        pyautogui.press(key)
