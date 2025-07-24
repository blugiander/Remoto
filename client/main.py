# client/main.py

import asyncio
import websockets
import json
import base64
import time
from capture import ScreenCapture
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID
import tkinter as tk # Aggiungi questa riga
from tkinter import messagebox # Aggiungi questa riga

# Funzione per mostrare il PIN in una finestra pop-up
def show_pin_dialog(pin_code):
    root = tk.Tk()
    root.withdraw() # Nasconde la finestra principale di Tkinter
    messagebox.showinfo("PIN per il Tecnico", f"Il PIN per la connessione è: {pin_code}\nComunicalo al tecnico.")
    # Puoi aggiungere un piccolo ritardo o aspettare che l'utente chiuda la finestra,
    # ma per un client che deve inviare lo schermo, basta visualizzare e continuare.
    root.destroy()

async def client_loop():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    print(f"🔗 Connessione al server {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            print("✅ Connesso al server.")

            register_message = json.dumps({
                "type": "register",
                "role": "client",
                "id": CLIENT_ID
            })
            await ws.send(register_message)
            print(f"📝 Inviato messaggio di registrazione come client (ID: {CLIENT_ID}).")

            response = await ws.recv()
            data = json.loads(response)
            pin = data.get('pin')
            if pin:
                # --- MODIFICA QUI: CHIAMARE LA FUNZIONE PER IL POP-UP ---
                show_pin_dialog(pin)
                # print(f"PIN da comunicare al tecnico: {pin}") # Rimuovi o commenta questa riga
            else:
                print("ERRORE: Non ho ricevuto un PIN dal server.")
                return

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
                
                await asyncio.sleep(0.2)

    except websockets.exceptions.ConnectionClosedOK:
        print("Disconnesso dal server normalmente.")
    except websockets.exceptions.ConnectionRefused:
        print(f"ERRORE: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE CLIENT: Si è verificato un errore: {e}", exc_info=True)

if __name__ == "__main__":
    # La parte di show_pin_dialog deve essere avviata in un thread separato o gestita con attenzione
    # se il client_loop è blocking, ma asyncio lo gestisce bene.
    asyncio.run(client_loop())