# client/main.py

import asyncio
import websockets
import json
import base64
import time
import uuid
import pyautogui
import win32api, win32con # Solo per Windows. Per Linux/Mac servono altre librerie.
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID
import mss
import cv2
import numpy as np

# Funzione per eseguire il click del mouse
def perform_click(x, y, button):
    print(f"CLIENT DEBUG: Eseguo click su: {x}, {y} con bottone: {button}")
    # pyautogui.moveTo(x, y) # Sposta il mouse (opzionale, pynput dovrebbe gestirlo)
    if button == 'left':
        pyautogui.click(x=x, y=y, button='left')
    elif button == 'right':
        pyautogui.click(x=x, y=y, button='right')
    elif button == 'middle':
        pyautogui.click(x=x, y=y, button='middle')
    print(f"CLIENT DEBUG: Click eseguito: x={x}, y={y}, button={button}")

# Funzione per simulare la pressione di un tasto
def perform_key_press(key):
    print(f"CLIENT DEBUG: Eseguo pressione tasto: {key}")
    try:
        if key.startswith('Key.'): # Pynput keys (es. Key.space)
            key_name = key.split('.')[-1]
            pyautogui.press(key_name)
        elif key == 'space': # pynput restituisce 'space' per la barra spaziatrice
            pyautogui.press(' ')
        elif key == 'backspace':
            pyautogui.press('backspace')
        elif key == 'enter':
            pyautogui.press('enter')
        elif key == 'shift' or key == 'shift_r' or key == 'shift_l':
            pyautogui.press('shift')
        elif key == 'alt' or key == 'alt_r' or key == 'alt_l':
            pyautogui.press('alt')
        elif key == 'ctrl' or key == 'ctrl_r' or key == 'ctrl_l':
            pyautogui.press('ctrl')
        elif key == 'cmd' or key == 'cmd_r' or key == 'cmd_l': # Per Windows è 'win'
             pyautogui.press('win')
        else: # Caratteri normali
            pyautogui.press(key)
        print(f"CLIENT DEBUG: Tasto '{key}' simulato.")
    except Exception as e:
        print(f"CLIENT ERRORE: Impossibile simulare tasto '{key}': {e}")


async def capture_and_send_screen(websocket):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Cattura il monitor primario (puoi cambiarlo)
        while True:
            try:
                # Cattura lo schermo
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)

                # Converti in BGR (OpenCV usa BGR, mss usa BGRA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Comprimi l'immagine in JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                encoded_frame = base64.b64encode(buffer).decode('utf-8')

                # Prepara il messaggio
                message = json.dumps({
                    "type": "message",
                    "id": CLIENT_ID,
                    "content": encoded_frame
                })

                # Invia il messaggio
                await websocket.send(message)
                await asyncio.sleep(0.05)  # Invia circa 20 FPS
            except websockets.exceptions.ConnectionClosedOK:
                print("Client: Connessione chiusa normalmente.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Client ERRORE: Connessione chiusa inaspettatamente: {e}")
                break
            except Exception as e:
                print(f"Client ERRORE durante cattura e invio schermo: {e}")
                await asyncio.sleep(1) # Riprova dopo 1 secondo

async def receive_commands(websocket):
    while True:
        try:
            command_message = await websocket.recv()
            command_data = json.loads(command_message)
            
            if command_data.get('type') == 'command' and 'content' in command_data:
                # Il "content" del messaggio del server è già una stringa JSON
                actual_command_content = json.loads(command_data['content']) 
                command_type = actual_command_content.get('type')
                
                print(f"CLIENT DEBUG: Ricevuto comando di tipo: {command_type}")

                if command_type == 'mouse_click':
                    x = actual_command_content.get('x')
                    y = actual_command_content.get('y')
                    button = actual_command_content.get('button')
                    if x is not None and y is not None and button:
                        perform_click(x, y, button)
                    else:
                        print(f"CLIENT ERRORE: Dati click incompleti: {actual_command_content}")
                elif command_type == 'key_press':
                    key = actual_command_content.get('key')
                    if key:
                        perform_key_press(key)
                    else:
                        print(f"CLIENT ERRORE: Dati tasto incompleti: {actual_command_content}")
                else:
                    print(f"CLIENT DEBUG: Comando sconosciuto ricevuto: {command_type}")
            else:
                print(f"CLIENT DEBUG: Messaggio comando non valido: {command_data}")
        except websockets.exceptions.ConnectionClosedOK:
            print("Client: Connessione chiusa normalmente durante ricezione comandi.")
            break
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Client ERRORE: Connessione chiusa inaspettatamente durante ricezione comandi: {e}")
            break
        except json.JSONDecodeError:
            print(f"CLIENT ERRORE: Ricevuto JSON non valido come comando: {command_message[:100]}...")
        except Exception as e:
            print(f"CLIENT ERRORE durante ricezione comandi: {e}")
            await asyncio.sleep(1) # Riprova dopo 1 secondo

async def main():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    print(f"🔗 Connessione al server {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connesso al server.")

            # Fase di registrazione
            register_message = json.dumps({
                "role": "client",
                "id": CLIENT_ID
            })
            await websocket.send(register_message)
            print(f"📝 Inviato messaggio di registrazione come client (ID: {CLIENT_ID}).")

            response = await websocket.recv()
            data = json.loads(response)

            if data.get('status') == 'registered':
                pin = data.get('pin')
                print(f"✅ Registrato con successo. Il tuo PIN è: {pin}")
                # Avvia i task per inviare lo schermo e ricevere i comandi
                screen_task = asyncio.create_task(capture_and_send_screen(websocket))
                command_task = asyncio.create_task(receive_commands(websocket))
                
                # Attendi che entrambi i task terminino
                await asyncio.gather(screen_task, command_task)

            else:
                print(f"ERRORE: Errore di registrazione: {data.get('status')}")

    except ConnectionRefusedError:
        print(f"ERRORE: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE: Si è verificato un errore generale: {e}")

if __name__ == "__main__":
    asyncio.run(main())