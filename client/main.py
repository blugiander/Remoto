# client/main.py

import asyncio
import websockets
import json
import base64
import time
from capture import ScreenCapture # Assicurati che capture.py sia corretto e nello stesso percorso
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID
import tkinter as tk
from tkinter import messagebox

# Funzione per mostrare il PIN in una finestra pop-up
def show_pin_dialog(pin_code):
    root = tk.Tk()
    root.withdraw() # Nasconde la finestra principale di Tkinter
    messagebox.showinfo("PIN per il Tecnico", f"Il PIN per la connessione è: {pin_code}\nComunicalo al tecnico.")
    root.destroy()

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
                show_pin_dialog(pin) # Mostra il PIN nel pop-up
                # print(f"PIN da comunicare al tecnico: {pin}") # Commentato per usare il pop-up
            else:
                print("ERRORE: Non ho ricevuto un PIN dal server.")
                return # Termina se non ricevi il PIN

            capture = ScreenCapture()
            print("Inizio cattura e invio dello schermo...")

            while True:
                frame_data = capture.get_frame_as_jpeg()
                if frame_data:
                    encoded_frame = base64.b64encode(frame_data).decode('utf-8')
                    message = json.dumps({
                        "type": "message",
                        "role": "client",
                        "id": CLIENT_ID,
                        "content": encoded_frame
                    })
                    await ws.send(message)
                    # print(f"🖼️ Inviato frame ({len(encoded_frame)} bytes).") # Troppo verboso
                
                # Regola la frequenza di invio dei frame (qui a circa 5 FPS)
                await asyncio.sleep(0.2) 

    except websockets.exceptions.ConnectionClosedOK:
        print("Disconnesso dal server normalmente.")
    # Modifica per gestire ConnectionRefusedError come eccezione built-in
    except ConnectionRefusedError: 
        print(f"ERRORE: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE CLIENT: Si è verificato un errore: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(client_loop())