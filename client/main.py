# client/main.py

import asyncio
import websockets
import json
import base64
import time
import pyautogui
import mss
import cv2
import numpy as np
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID # Importa dalla tua config.py

# Funzione per eseguire il click del mouse
def perform_click(x, y, button):
    print(f"CLIENT DEBUG: Eseguo click su: {x}, {y} con bottone: {button}")
    pyautogui.click(x=x, y=y, button=button)
    print(f"CLIENT DEBUG: Click eseguito: x={x}, y={y}, button={button}")

# Funzione per eseguire il movimento del mouse
def perform_mouse_move(x, y):
    # print(f"CLIENT DEBUG: Eseguo movimento mouse a: {x}, {y}") # Molto verboso
    pyautogui.moveTo(x, y)

# Funzione per eseguire lo scroll del mouse
def perform_mouse_scroll(direction):
    print(f"CLIENT DEBUG: Eseguo scroll mouse: {direction}")
    if direction == "up":
        pyautogui.scroll(10) # Scroll up di 10 "unità"
    elif direction == "down":
        pyautogui.scroll(-10) # Scroll down di 10 "unità"

# Funzione per simulare la pressione di un tasto
def perform_key_press(key):
    print(f"CLIENT DEBUG: Eseguo pressione tasto: {key}")
    try:
        pyautogui_key_map = {
            'space': ' ', 'enter': 'enter', 'backspace': 'backspace',
            'tab': 'tab', 'caps_lock': 'capslock', 'num_lock': 'numlock',
            'scroll_lock': 'scrolllock',
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4', 'f5': 'f5',
            'f6': 'f6', 'f7': 'f7', 'f8': 'f8', 'f9': 'f9', 'f10': 'f10',
            'f11': 'f11', 'f12': 'f12',
            'left': 'left', 'right': 'right', 'up': 'up', 'down': 'down',
            'home': 'home', 'end': 'end', 'page_up': 'pageup', 'page_down': 'pagedown',
            'insert': 'insert', 'delete': 'delete',
            'print_screen': 'prntscrn', 'pause': 'pause',
            'alt_l': 'alt', 'alt_r': 'altright', 'ctrl_l': 'ctrl', 'ctrl_r': 'ctrlright',
            'shift_l': 'shift', 'shift_r': 'shiftright',
            'cmd_l': 'win', 'cmd_r': 'win' # 'win' per il tasto Windows
        }
        
        normalized_key = key.lower()

        if normalized_key.startswith('key.'):
            normalized_key = normalized_key.replace('key.', '')

        if normalized_key in pyautogui_key_map:
            pyautogui.press(pyautogui_key_map[normalized_key])
        else:
            pyautogui.press(key) 

        print(f"CLIENT DEBUG: Tasto '{key}' simulato.")
    except Exception as e:
        print(f"CLIENT ERRORE: Impossibile simulare tasto '{key}': {e}")


async def capture_and_send_screen(websocket):
    print(f"CLIENT: Avvio loop di invio schermo per ID: {CLIENT_ID}")
    with mss.mss() as sct:
        if len(sct.monitors) < 2:
            print("CLIENT AVVISO: Meno di due monitor rilevati. Utilizzo il primo monitor disponibile.")
            monitor_index = 1
        else:
            monitor_index = 1 

        monitor = sct.monitors[monitor_index] 
        
        # Modifica qui: usa websocket.closed per verificare che la connessione sia aperta
        while not websocket.closed:
            try:
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                encoded_frame = base64.b64encode(buffer).decode('utf-8')

                message = json.dumps({
                    "type": "message",
                    "content_type": "screen",
                    "id": CLIENT_ID,
                    "content": encoded_frame
                })

                await websocket.send(message)
                # print(f"CLIENT: Inviato frame schermo (dimensione: {len(encoded_frame)} bytes)") # Troppo verboso
                await asyncio.sleep(0.04)

            except websockets.exceptions.ConnectionClosedOK:
                print("CLIENT: Connessione chiusa normalmente (loop invio schermo).")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"CLIENT ERRORE: Connessione chiusa inaspettatamente (loop invio schermo): {e}")
                break
            except Exception as e:
                print(f"CLIENT ERRORE durante cattura e invio schermo: {e}")
                await asyncio.sleep(1)

async def receive_commands(websocket):
    print("CLIENT: Avvio loop di ricezione comandi.")
    # Modifica qui: usa websocket.closed per verificare che la connessione sia aperta
    while not websocket.closed:
        try:
            command_message = await websocket.recv()
            command_data = json.loads(command_message)
            
            if command_data.get('type') == 'command' and 'data' in command_data:
                command_type = command_data.get('command_type')
                command_content = command_data.get('data')

                print(f"CLIENT DEBUG: Ricevuto comando di tipo: {command_type} con dati: {command_content}")

                if command_type == 'mouse_click':
                    x = command_content.get('x')
                    y = command_content.get('y')
                    button = command_content.get('button')
                    if x is not None and y is not None and button:
                        perform_click(x, y, button)
                    else:
                        print(f"CLIENT ERRORE: Dati click incompleti: {command_content}")
                elif command_type == 'mouse_move':
                    x = command_content.get('x')
                    y = command_content.get('y')
                    if x is not None and y is not None:
                        perform_mouse_move(x, y)
                    else:
                        print(f"CLIENT ERRORE: Dati movimento mouse incompleti: {command_content}")
                elif command_type == 'mouse_scroll':
                    direction = command_content.get('direction')
                    if direction:
                        perform_mouse_scroll(direction)
                    else:
                        print(f"CLIENT ERRORE: Dati scroll mouse incompleti: {command_content}")
                elif command_type == 'key_press':
                    key = command_content.get('key')
                    if key:
                        perform_key_press(key)
                    else:
                        print(f"CLIENT ERRORE: Dati tasto incompleti: {command_content}")
                else:
                    print(f"CLIENT DEBUG: Comando sconosciuto ricevuto: {command_type}")
            else:
                print(f"CLIENT DEBUG: Messaggio non di tipo comando valido: {command_data}")
        except websockets.exceptions.ConnectionClosedOK:
            print("CLIENT: Connessione chiusa normalmente durante ricezione comandi.")
            break
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"CLIENT ERRORE: Connessione chiusa inaspettatamente durante ricezione comandi: {e}")
            break
        except json.JSONDecodeError:
            print(f"CLIENT ERRORE: Ricevuto JSON non valido come comando: {command_message[:100]}...")
        except Exception as e:
            print(f"CLIENT ERRORE durante ricezione comandi: {e}")
            await asyncio.sleep(1)

async def connect_and_register_client():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    
    reconnect_attempts = 10
    for attempt in range(reconnect_attempts):
        try:
            async with websockets.connect(uri) as websocket:
                print("✅ CLIENT: Connesso al server.")

                registration_message = json.dumps({
                    "type": "register",
                    "role": "client",
                    "id": CLIENT_ID
                })
                await websocket.send(registration_message)
                print(f"📝 CLIENT: Inviato messaggio di registrazione (ID: {CLIENT_ID}).")

                registration_response_str = await websocket.recv()
                registration_response = json.loads(registration_response_str)

                if registration_response.get("status") == "registered" and registration_response.get("pin"):
                    client_pin = registration_response["pin"]
                    print(f"✅ CLIENT: Registrazione al server completata. Il tuo PIN di connessione è: {client_pin}")
                    
                    send_task = asyncio.create_task(capture_and_send_screen(websocket))
                    receive_task = asyncio.create_task(receive_commands(websocket))

                    # Se uno dei task finisce (es. connessione chiusa), vogliamo che anche l'altro termini.
                    # Questo blocca fino a quando non termina uno dei due.
                    done, pending = await asyncio.wait([send_task, receive_task], return_when=asyncio.FIRST_COMPLETED)
                    
                    # Cerca l'eccezione se un task è fallito
                    for task in done:
                        if task.exception():
                            print(f"ERRORE CLIENT: Un task parallelo è terminato con un'eccezione: {task.exception()}")
                    
                    # Cancella i task rimanenti se uno è terminato
                    for task in pending:
                        task.cancel()
                        try:
                            await task # Attendere che il task cancellato si fermi
                        except asyncio.CancelledError:
                            print(f"CLIENT: Task {task.get_name() if hasattr(task, 'get_name') else ''} è stato cancellato.")

                else:
                    print(f"ERRORE CLIENT: Registrazione fallita o PIN non ricevuto. Risposta: {registration_response}")
                    break

        # Modifica qui: usa ConnectionRefusedError direttamente o BaseException per catturare tutto
        # ConnectionRefusedError è una sottoclasse di OSError.
        except OSError as e: # Catch OSError che include ConnectionRefusedError
            if "Connection refused" in str(e):
                print(f"ERRORE CLIENT: Connessione rifiutata dal server ({uri}). Assicurati che il server sia in esecuzione e accessibile. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            else:
                print(f"ERRORE CLIENT: Errore di sistema durante la connessione ({uri}): {e}. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
        except websockets.exceptions.ConnectionClosed as e: # Questo include ConnectionClosedOK e ConnectionClosedError
            print(f"ERRORE CLIENT: Connessione chiusa inaspettatamente ({uri}): {e}. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"ERRORE CLIENT: Errore generale durante la connessione o l'esecuzione: {e}. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
    
    print(f"CLIENT: Falliti {reconnect_attempts} tentativi di connessione. Uscita.")

# --- BLOCCO PRINCIPALE DI ESECUZIONE ---
if __name__ == "__main__":
    print("CLIENT: Avvio del programma client...")
    try:
        asyncio.run(connect_and_register_client())
    except KeyboardInterrupt:
        print("CLIENT: Programma interrotto dall'utente.")
    finally:
        print("CLIENT: Programma terminato.")