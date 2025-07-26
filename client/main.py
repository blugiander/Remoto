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
import threading # Per gestire il mouse move in background
<<<<<<< HEAD
import sys # Per gestire l'uscita pulita

# Importa dalla tua config.py (assicurati che config.py esista nella stessa directory)
# Esempio di config.py:
# SERVER_HOST = "188.245.238.160"
# SERVER_PORT = 8765
# CLIENT_ID = "YourUniqueClientID" # Puoi generare un UUID qui o usare qualcosa di statico per i test
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID

# --- Variabili globali per il controllo del mouse/tastiera ---
# Devono essere dichiarate a livello di modulo (globali per tutto il file)
mouse_move_thread = None
mouse_move_event = threading.Event() # Usato per segnalare al thread di movimento mouse di fermarsi
=======
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID # Importa dalla tua config.py

# Variabili per il controllo del mouse/tastiera
mouse_move_thread = None
mouse_move_event = threading.Event()
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
mouse_target_x = 0
mouse_target_y = 0

# Funzione per eseguire il click del mouse
def perform_click(x, y, button):
    print(f"CLIENT DEBUG: Eseguo click su: {x}, {y} con bottone: {button}")
<<<<<<< HEAD
    try:
        pyautogui.click(x=x, y=y, button=button)
        print(f"CLIENT DEBUG: Click eseguito: x={x}, y={y}, button={button}")
    except Exception as e:
        print(f"CLIENT ERRORE: Impossibile eseguire click su {x},{y} con {button}: {e}")

# Funzione per eseguire il movimento del mouse in un thread separato
def _mouse_move_worker():
    # Queste variabili sono globali per il modulo, quindi vanno dichiarate come tali qui
    global mouse_target_x, mouse_target_y, mouse_move_event
    print("CLIENT DEBUG: _mouse_move_worker avviato.")
    while not mouse_move_event.is_set():
        try:
            # Muovi il mouse solo se la posizione target è diversa da quella attuale
            if pyautogui.position() != (mouse_target_x, mouse_target_y):
                pyautogui.moveTo(mouse_target_x, mouse_target_y, duration=0.01) # Piccola durata per ammorbidire
        except pyautogui.FailSafeException:
            # PyAutoGUI ha un meccanismo di failsafe (spostando il mouse negli angoli)
            print("CLIENT AVVISO: Failsafe di PyAutoGUI attivato. Arresto movimento mouse.")
            mouse_move_event.set() # Ferma il worker
        except Exception as e:
            print(f"CLIENT ERRORE in _mouse_move_worker: {e}")
            break # Esci dal loop in caso di errore grave
        time.sleep(0.01) # Piccolo ritardo per non saturare la CPU
    print("CLIENT DEBUG: _mouse_move_worker terminato.")


def perform_mouse_move(x, y):
    # Anche qui, dichiara le variabili globali che verranno modificate
    global mouse_target_x, mouse_target_y, mouse_move_thread, mouse_move_event
    mouse_target_x = x
    mouse_target_y = y

    # Avvia il thread del movimento mouse se non è già attivo
    if mouse_move_thread is None or not mouse_move_thread.is_alive():
        mouse_move_event.clear() # Resetta l'evento per permettere al thread di continuare
        mouse_move_thread = threading.Thread(target=_mouse_move_worker, daemon=True)
        mouse_move_thread.start()
    # print(f"CLIENT DEBUG: Aggiornato target mouse a: {x}, {y}") # Molto verboso se in streaming


# Funzione per eseguire lo scroll del mouse
def perform_mouse_scroll(direction):
    print(f"CLIENT DEBUG: Eseguo scroll mouse: {direction}")
    try:
        if direction == "up":
            pyautogui.scroll(10) # Scroll up di 10 "unità"
        elif direction == "down":
            pyautogui.scroll(-10) # Scroll down di 10 "unità"
        print(f"CLIENT DEBUG: Scroll eseguito: {direction}")
    except Exception as e:
        print(f"CLIENT ERRORE: Impossibile eseguire scroll '{direction}': {e}")
=======
    # pyautogui.click usa internamente moveTo e mouseDown/mouseUp
    pyautogui.click(x=x, y=y, button=button)
    print(f"CLIENT DEBUG: Click eseguito: x={x}, y={y}, button={button}")
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d

# Funzione per eseguire il movimento del mouse in un thread separato
def _mouse_move_worker():
    global mouse_target_x, mouse_target_y
    while not mouse_move_event.is_set():
        if pyautogui.position() != (mouse_target_x, mouse_target_y):
            # Usiamo pyautogui.moveTo con durata 0 per un movimento istantaneo o quasi
            pyautogui.moveTo(mouse_target_x, mouse_target_y, duration=0.01) # Piccola durata per ammorbidire
        time.sleep(0.01) # Piccolo ritardo per non saturare la CPU

def perform_mouse_move(x, y):
    global mouse_target_x, mouse_target_y, mouse_move_thread, mouse_move_event
    mouse_target_x = x
    mouse_target_y = y

    if mouse_move_thread is None or not mouse_move_thread.is_alive():
        mouse_move_event.clear()
        mouse_move_thread = threading.Thread(target=_mouse_move_worker, daemon=True)
        mouse_move_thread.start()
    # print(f"CLIENT DEBUG: Aggiornato target mouse a: {x}, {y}") # Molto verboso se in streaming


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
        # Mappatura per tasti speciali per pyautogui
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

        if normalized_key.startswith('key.'): # Rimuove il prefisso 'Key.' se presente (da pynput/keyboard)
            normalized_key = normalized_key.replace('key.', '')

        if normalized_key in pyautogui_key_map:
            pyautogui.press(pyautogui_key_map[normalized_key])
        else:
            pyautogui.press(key) # Prova a premere il tasto direttamente

        print(f"CLIENT DEBUG: Tasto '{key}' simulato.")
    except Exception as e:
        print(f"CLIENT ERRORE: Impossibile simulare tasto '{key}': {e}")


async def capture_and_send_screen(websocket_connection):
    print(f"CLIENT: Avvio loop di invio schermo per ID: {CLIENT_ID}")
    with mss.mss() as sct:
        # Configurazione per catturare il primo monitor (di solito il principale)
        # sct.monitors[0] è l'intero desktop, sct.monitors[1] è il primo monitor, ecc.
        # Se hai un solo monitor, usa sct.monitors[1] per catturarlo interamente.
        if len(sct.monitors) < 2:
            print("CLIENT AVVISO: Meno di due monitor rilevati (solo desktop o un monitor). Utilizzo il primo monitor disponibile (sct.monitors[1]).")
            monitor_index = 1
        else:
            # Assumiamo il monitor principale sia sct.monitors[1] per default.
            # Se vuoi selezionare un monitor specifico (es. il secondo), cambia in 2, 3, ecc.
            monitor_index = 1 
        
        # Verifica che il monitor esista prima di provare a usarlo
        if monitor_index >= len(sct.monitors):
            print(f"CLIENT ERRORE: Monitor {monitor_index} non trovato. Non è possibile catturare lo schermo.")
            return # Esci dalla funzione se il monitor non esiste

        monitor = sct.monitors[monitor_index] 
        
        while not websocket_connection.closed: 
            try:
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR) # Converti BGRA (con alpha) a BGR

                # Codifica il frame come JPEG per ridurre la dimensione e la latenza
                # Qualità JPEG 70 è un buon compromesso tra qualità e dimensione
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                encoded_frame = base64.b64encode(buffer).decode('utf-8')

                message = json.dumps({
                    "type": "message",
                    "content_type": "screen",
                    "id": CLIENT_ID,
                    "content": encoded_frame
                })

                await websocket_connection.send(message)
                # print(f"CLIENT: Inviato frame schermo (dimensione: {len(encoded_frame)} bytes)") # Troppo verboso, decommenta per debug
                await asyncio.sleep(0.04) # Circa 25 FPS (1/0.04 = 25)

            except websockets.exceptions.ConnectionClosedOK:
                print("CLIENT: Connessione chiusa normalmente (loop invio schermo).")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"CLIENT ERRORE: Connessione chiusa inaspettatamente (loop invio schermo): {e}")
                break
            except Exception as e:
                print(f"CLIENT ERRORE durante cattura e invio schermo: {e}")
                await asyncio.sleep(1) # Riprova dopo un breve ritardo

async def receive_commands(websocket_connection):
    print("CLIENT: Avvio loop di ricezione comandi.")
    while not websocket_connection.closed:
        try:
            command_message_str = await websocket_connection.recv()
            command_data = json.loads(command_message_str)
            
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
            print(f"CLIENT ERRORE: Ricevuto JSON non valido come comando: {command_message_str[:100]}...")
        except Exception as e:
            print(f"CLIENT ERRORE durante ricezione comandi: {e}")
            await asyncio.sleep(1)

async def connect_and_register_client():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    
    reconnect_attempts = 10
    for attempt in range(reconnect_attempts):
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket: # Aggiungi ping_interval/timeout
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

                    # Attende che uno dei task (send o receive) si completi (es. per disconnessione)
                    done, pending = await asyncio.wait([send_task, receive_task], return_when=asyncio.FIRST_COMPLETED)
                    
                    # Logga eventuali eccezioni dai task completati
                    for task in done:
                        if task.exception():
                            print(f"ERRORE CLIENT: Un task parallelo è terminato con un'eccezione: {task.exception()}")
                    
                    # Cancella i task che sono ancora in esecuzione
                    for task in pending:
                        task.cancel()
                        try:
                            await task # Attende che il task cancellato si fermi pulitamente
                        except asyncio.CancelledError:
                            print(f"CLIENT: Task {task.get_name() if hasattr(task, 'get_name') else ''} è stato cancellato.")

                    print(f"CLIENT: Sessione WebSocket per client {CLIENT_ID} terminata. Riconnessione...")

                else:
                    print(f"ERRORE CLIENT: Registrazione fallita o PIN non ricevuto. Risposta: {registration_response}. Riprovo in 5 secondi...")
                    await asyncio.sleep(5)
                    continue # Prova la prossima iterazione per riconnettersi

        except OSError as e: # Cattura errori di sistema come "Connection refused"
            if "Connection refused" in str(e):
                print(f"ERRORE CLIENT: Connessione rifiutata dal server ({uri}). Assicurati che il server sia in esecuzione e accessibile. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            else:
                print(f"ERRORE CLIENT: Errore di sistema durante la connessione ({uri}): {e}. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
        except websockets.exceptions.ConnectionClosed as e: # Include ConnectionClosedOK e ConnectionClosedError
            print(f"ERRORE CLIENT: Connessione chiusa inaspettatamente ({uri}): {e}. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"ERRORE CLIENT: Errore generale durante la connessione o l'esecuzione: {e}. Riprovo in 5 secondi... ({attempt + 1}/{reconnect_attempts})")
            await asyncio.sleep(5)
    
    print(f"CLIENT: Falliti {reconnect_attempts} tentativi di connessione. Uscita.")
<<<<<<< HEAD
    sys.exit(1) # Termina il processo del client dopo falliti tentativi
=======
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d

# --- BLOCCO PRINCIPALE DI ESECUZIONE ---
if __name__ == "__main__":
    print("CLIENT: Avvio del programma client...")
    try:
        asyncio.run(connect_and_register_client())
    except KeyboardInterrupt:
        print("CLIENT: Programma interrotto dall'utente.")
    finally:
        # Assicurati di fermare il thread del mouse in caso di interruzione
<<<<<<< HEAD
        # Non è necessaria la keyword 'global' qui perché siamo a livello di modulo
        # e stiamo semplicemente accedendo alla variabile globale.
        mouse_move_event.set()
        if mouse_move_thread and mouse_move_thread.is_alive():
            print("CLIENT: In attesa della terminazione del thread di movimento mouse...")
            mouse_move_thread.join(timeout=1) # Attendi un po' per la terminazione
            if mouse_move_thread.is_alive():
                print("CLIENT AVVISO: Il thread di movimento mouse non è terminato in tempo.")
=======
        global mouse_move_event
        mouse_move_event.set()
        if mouse_move_thread and mouse_move_thread.is_alive():
            mouse_move_thread.join(timeout=1) # Attendi un po' per la terminazione
>>>>>>> 413ff6f04e84f437222564744ceed3974a03307d
        print("CLIENT: Programma terminato.")