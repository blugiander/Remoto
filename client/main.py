# remoto/client/main.py

import asyncio
import websockets
import json
import base64
import time
import sys
import os
import random
import string
import logging

# Aggiungi per cattura schermo e controllo input
import mss
import cv2
import numpy as np
import pyautogui
import platform

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Importa configurazione
try:
    from config import SERVER_HOST, SERVER_PORT, CLIENT_ID_PREFIX
except ImportError:
    # Fallback se config.py non è presente (utile per test rapidi)
    SERVER_HOST = '188.245.238.160' # Sostituisci con l'IP del tuo server
    SERVER_PORT = 8765
    CLIENT_ID_PREFIX = 'client'
    logging.warning("config.py non trovato, usando configurazione di fallback.")

# Variabili globali per la connessione
websocket = None
is_connected = False
client_pin = None # Il PIN generato per questo client

# Funzione per generare un PIN a 6 cifre
def generate_pin():
    return ''.join(random.choices(string.digits, k=6))

# Funzione per catturare lo schermo
def capture_screen_frame():
    try:
        with mss.mss() as sct:
            # Cattura l'intero schermo. Se hai più monitor, potresti voler specificare 'monitor=1' o iterare.
            monitor = sct.monitors[1] # [0] è l'intero desktop, [1] il primo monitor
            sct_img = sct.grab(monitor)
            
            # Converti in un array NumPy (OpenCV compatibile)
            # La dimensione di sct_img.rgb è (altezza, larghezza, 3) ma è RGB, OpenCV è BGR
            frame = np.array(sct_img.pixels, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 4))
            frame = frame[:, :, :3] # Rimuovi il canale alpha
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # Converti da RGB a BGR

            # Comprimi l'immagine in JPEG per ridurre le dimensioni
            ret, jpeg_encoded_frame = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                return base64.b64encode(jpeg_encoded_frame.tobytes()).decode('utf-8')
            else:
                logging.error("Errore nella codifica JPEG del frame.")
                return None
    except mss.exception.ScreenShotError as e:
        logging.error(f"Errore di cattura schermo (MSS): {e}")
        logging.error("Assicurati che un server X sia in esecuzione (es. Xvfb su Linux headless).")
        return None
    except Exception as e:
        logging.error(f"Errore generico durante la cattura dello schermo: {e}")
        return None

async def send_screen_frames():
    global websocket, is_connected
    while is_connected:
        try:
            frame_data = capture_screen_frame()
            if frame_data:
                message = {
                    "type": "frame",
                    "role": "client",
                    "id": client_pin, # Usa il PIN come ID
                    "content": frame_data
                }
                await websocket.send(json.dumps(message))
            await asyncio.sleep(0.05) # Invia circa 20 frame al secondo
        except websockets.exceptions.ConnectionClosed:
            logging.info("Connessione chiusa durante l'invio del frame.")
            is_connected = False
            break
        except Exception as e:
            logging.error(f"Errore durante l'invio del frame: {e}")
            await asyncio.sleep(1) # Attendi un po' prima di riprovare

async def handle_commands():
    global websocket, is_connected
    while is_connected:
        try:
            message_json = await websocket.recv()
            message = json.loads(message_json)

            if message.get("type") == "command" and message.get("role") == "technician":
                command_content = message.get("content", {})
                command_type = command_content.get("command_type")
                data = command_content.get("data", {})
                
                logging.info(f"Comando ricevuto: {command_type} con dati: {data}")

                try:
                    if command_type == "mouse_move":
                        x, y = data.get("x"), data.get("y")
                        if x is not None and y is not None:
                            pyautogui.moveTo(x, y, _pause=False)
                    elif command_type == "mouse_click":
                        x, y = data.get("x"), data.get("y")
                        button = data.get("button", "left")
                        if x is not None and y is not None:
                            pyautogui.click(x, y, button=button, _pause=False)
                    elif command_type == "mouse_scroll":
                        direction = data.get("direction")
                        amount = data.get("amount", 1)
                        if direction == "up":
                            pyautogui.scroll(amount, _pause=False)
                        elif direction == "down":
                            pyautogui.scroll(-amount, _pause=False)
                    elif command_type == "mouse_drag":
                        x, y = data.get("x"), data.get("y")
                        button = data.get("button", "left")
                        if x is not None and y is not None:
                             pyautogui.dragTo(x, y, button=button, _pause=False)
                    elif command_type == "key_press":
                        key = data.get("key")
                        if key:
                            pyautogui.press(key, _pause=False)
                    elif command_type == "key_down":
                        key = data.get("key")
                        if key:
                            pyautogui.keyDown(key, _pause=False)
                    elif command_type == "key_up":
                        key = data.get("key")
                        if key:
                            pyautogui.keyUp(key, _pause=False)
                    else:
                        logging.warning(f"Comando non riconosciuto: {command_type}")
                except Exception as e:
                    logging.error(f"Errore durante l'esecuzione del comando {command_type}: {e}")
            elif message.get("type") == "status":
                logging.info(f"Server Status: {message.get('message')}")
            elif message.get("type") == "error":
                logging.error(f"Server Error: {message.get('message')}")
            elif message.get("type") == "notification":
                logging.info(f"Server Notification: {message.get('message')}")
            else:
                logging.warning(f"Messaggio ricevuto non gestito: {message}")

        except websockets.exceptions.ConnectionClosed:
            logging.info("Connessione chiusa durante la gestione dei comandi.")
            is_connected = False
            break
        except json.JSONDecodeError:
            logging.error(f"Errore di decodifica JSON nel messaggio ricevuto: {message_json}")
        except Exception as e:
            logging.error(f"Errore durante la ricezione o gestione del messaggio: {e}")
            await asyncio.sleep(1) # Attendi un po' prima di riprovare

async def connect_to_server():
    global websocket, is_connected, client_pin

    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    
    # Genera un PIN al primo tentativo o se la connessione è stata chiusa
    if client_pin is None:
        client_pin = generate_pin()
        logging.info(f"PIN generato per questa sessione: {client_pin}")

    reconnect_delay = 1 # Secondi
    while True:
        try:
            logging.info(f"Tentativo di connessione al server: {uri}")
            websocket = await websockets.connect(uri)
            is_connected = True
            logging.info("Connesso al server.")

            # Invia messaggio di registrazione
            registration_message = {
                "type": "register",
                "role": "client",
                "id": client_pin, # Usa il PIN come ID del client
                "pin": client_pin
            }
            await websocket.send(json.dumps(registration_message))
            logging.info(f"Inviato messaggio di registrazione: {registration_message}")

            # Avvia i task per inviare frame e ricevere comandi
            await asyncio.gather(
                send_screen_frames(),
                handle_commands()
            )

        except websockets.exceptions.ConnectionClosed as e:
            logging.warning(f"Connessione al server chiusa: {e}. Riconnessione in {reconnect_delay}s...")
            is_connected = False
        except ConnectionRefusedError:
            logging.error(f"Connessione rifiutata. Il server è in esecuzione su {SERVER_HOST}:{SERVER_PORT}?")
            is_connected = False
        except Exception as e:
            logging.error(f"Errore di connessione o inatteso: {e}. Riconnessione in {reconnect_delay}s...", exc_info=True)
            is_connected = False
        finally:
            if websocket and not websocket.closed:
                await websocket.close()
            logging.info(f"Disconnesso. Tentativo di riconnessione in {reconnect_delay} secondi...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60) # Backoff esponenziale fino a 60 secondi

async def main():
    # Disabilita il fail-safe di pyautogui se stai eseguendo su un server senza GUI
    # o se vuoi che pyautogui non termini lo script quando il mouse va negli angoli.
    # Attenzione: abilitalo solo se sai cosa stai facendo e hai un modo per fermare lo script.
    pyautogui.FAILSAFE = False # Impostalo su False per ambienti headless
    pyautogui.PAUSE = 0 # Rimuove le pause implicite tra le chiamate pyautogui

    # Configurazione specifica per Linux headless (es. Hetzner con Xvfb)
    if platform.system() == "Linux" and "DISPLAY" not in os.environ:
        logging.info("Nessuna variabile DISPLAY rilevata. Assicurati che Xvfb sia configurato.")
        logging.info("Esempio: export DISPLAY=:99 && Xvfb :99 -screen 0 1024x768x24 &")
        # Puoi anche provare a impostare una risoluzione predefinita per pyautogui,
        # anche se mss dovrebbe rilevarla correttamente se Xvfb è attivo.
        # pyautogui._size = (1024, 768) # Dimensione virtuale dello schermo se non rilevata

    logging.info(f"Client avviato. Connessione a {SERVER_HOST}:{SERVER_PORT}")
    await connect_to_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Client interrotto da tastiera.")
    finally:
        logging.info("Client terminato.")