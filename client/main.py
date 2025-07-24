# client/main.py

import asyncio
import websockets
import json
import base64
import time
from capture import ScreenCapture 
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID
import tkinter as tk
from tkinter import messagebox
from pynput import mouse, keyboard # Importa pynput

# Inizializza controller di pynput
mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

# Funzione per mostrare il PIN in una finestra pop-up
def show_pin_dialog(pin_code):
    root = tk.Tk()
    root.withdraw() 
    messagebox.showinfo("PIN per il Tecnico", f"Il PIN per la connessione è: {pin_code}\nComunicalo al tecnico.")
    root.destroy()

# Funzione per processare i comandi di input ricevuti dal server
def process_command(command_data):
    command_type = command_data.get("type")
    
    if command_type == "mouse_click":
        x = command_data.get("x")
        y = command_data.get("y")
        button_name = command_data.get("button")
        
        # Sposta il mouse e clicca
        # Nota: La finestra del tecnico e quella del client potrebbero avere risoluzioni diverse.
        # Per ora, le coordinate sono inviate 1:1. Per maggiore precisione, si dovrebbe 
        # considerare la scala (risoluzione del tecnico / risoluzione del client).
        # Per ora, si assume che il puntatore del tecnico sia relativo alla finestra di visualizzazione.
        
        mouse_controller.position = (x, y)
        if button_name == "left":
            mouse_controller.click(mouse.Button.left)
        elif button_name == "right":
            mouse_controller.click(mouse.Button.right)
        # Puoi aggiungere altri pulsanti se necessario (es. middle)
        print(f"CLIENT DEBUG: Click simulato a ({x}, {y}) con {button_name}.")

    elif command_type == "key_press":
        key = command_data.get("key")
        
        # Mappa i nomi dei tasti speciali da stringa a oggetti pynput.Key
        pynput_key = None
        if key == "space": pynput_key = keyboard.Key.space
        elif key == "enter": pynput_key = keyboard.Key.enter
        elif key == "esc": pynput_key = keyboard.Key.esc
        elif key == "alt_l": pynput_key = keyboard.Key.alt_l
        elif key == "f4": pynput_key = keyboard.Key.f4
        elif key == "f5": pynput_key = keyboard.Key.f5 # Aggiunto F5 per refresh
        elif key == "backspace": pynput_key = keyboard.Key.backspace
        elif key == "delete": pynput_key = keyboard.Key.delete
        elif key == "shift": pynput_key = keyboard.Key.shift # Potrebbe essere shift_l o shift_r
        elif key == "ctrl": pynput_key = keyboard.Key.ctrl # Potrebbe essere ctrl_l o ctrl_r
        elif key == "alt": pynput_key = keyboard.Key.alt # Potrebbe essere alt_l o alt_r
        elif key == "tab": pynput_key = keyboard.Key.tab
        elif key == "caps_lock": pynput_key = keyboard.Key.caps_lock
        elif key == "up": pynput_key = keyboard.Key.up
        elif key == "down": pynput_key = keyboard.Key.down
        elif key == "left": pynput_key = keyboard.Key.left
        elif key == "right": pynput_key = keyboard.Key.right
        # Aggiungi altri tasti speciali di cui hai bisogno
        
        if pynput_key:
            keyboard_controller.press(pynput_key)
            keyboard_controller.release(pynput_key)
        else:
            # Per caratteri normali (una singola lettera o simbolo)
            keyboard_controller.press(key)
            keyboard_controller.release(key)
        print(f"CLIENT DEBUG: Pressione tasto simulata: {key}.")
    
    # Puoi aggiungere altri tipi di comando (es. mouse_move, mouse_scroll, key_release)
    else:
        print(f"CLIENT DEBUG: Comando sconosciuto ricevuto: {command_type}")


async def client_loop():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    print(f"🔗 Connessione al server {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            print("✅ Connesso al server.")

            # Fase di registrazione
            register_message = json.dumps({
                "type": "register",
                "role": "client",
                "id": CLIENT_ID
            })
            await ws.send(register_message)
            print(f"📝 Inviato messaggio di registrazione come client (ID: {CLIENT_ID}).")

            # Ricevi il PIN dal server
            response = await ws.recv()
            data = json.loads(response)
            pin = data.get('pin')
            if pin:
                show_pin_dialog(pin) 
            else:
                print("ERRORE: Non ho ricevuto un PIN dal server.")
                return 

            capture = ScreenCapture()
            print("Inizio cattura e invio dello schermo...")

            # --- NUOVO: Task concorrente per la ricezione dei comandi ---
            async def receive_commands(ws):
                while True:
                    try:
                        # Ricevi messaggi dal server. Il server inoltra solo il content,
                        # che è già la stringa JSON del comando.
                        command_json_string = await ws.recv()
                        command_data = json.loads(command_json_string)
                        process_command(command_data)
                    except websockets.exceptions.ConnectionClosedOK:
                        print("CLIENT DEBUG: Connessione chiusa per ricezione comandi.")
                        break
                    except json.JSONDecodeError as e:
                        print(f"CLIENT ERRORE: Errore di decodifica JSON per comando: {e}. Messaggio raw: {command_json_string[:200]}...")
                    except Exception as e:
                        print(f"CLIENT ERRORE: Errore durante elaborazione comando: {e}", exc_info=True)


            # Avvia il task di ricezione comandi
            receive_task = asyncio.create_task(receive_commands(ws))

            # Loop principale per l'invio dello schermo
            while True:
                frame_data = capture.get_frame_as_jpeg()
                if frame_data:
                    encoded_frame = base64.b64encode(frame_data).decode('utf-8')
                    # Quando il client invia un frame, lo etichetta come 'message'
                    message = json.dumps({
                        "type": "message",
                        "role": "client",
                        "id": CLIENT_ID,
                        "content": encoded_frame # Il contenuto è il frame codificato
                    })
                    await ws.send(message)
                
                await asyncio.sleep(0.2) # Regola la frequenza di invio dei frame

    except websockets.exceptions.ConnectionClosedOK:
        print("Disconnesso dal server normalmente.")
    except ConnectionRefusedError: 
        print(f"ERRORE: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE CLIENT generale: Si è verificato un errore: {e}", exc_info=True)
    finally:
        # Assicurati di annullare il task di ricezione comandi alla fine
        if 'receive_task' in locals() and not receive_task.done():
            receive_task.cancel()
            try:
                await receive_task 
            except asyncio.CancelledError:
                pass
            print("CLIENT DEBUG: Task ricezione comandi annullato.")

if __name__ == "__main__":
    asyncio.run(client_loop())