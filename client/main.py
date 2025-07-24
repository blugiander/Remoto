# client/main.py (modifica solo la riga asyncio.sleep)

import asyncio
import websockets
import json
import base64
import time
from capture import ScreenCapture
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID

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
                print(f"PIN da comunicare al tecnico: {pin}")
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
                    # print(f"🖼️ Inviato frame ({len(encoded_frame)} bytes).") # Manteniamo commentato
                
                # --- MODIFICA QUI: AUMENTA IL RITARDO ---
                await asyncio.sleep(0.2) # Prima era 0.1. Proviamo con 0.2 (circa 5 FPS)
                                          # Se ancora dà problemi, prova 0.3 o 0.5.
                                          # L'obiettivo è trovare un buon compromesso tra fluidità e stabilità.

    except websockets.exceptions.ConnectionClosedOK:
        print("Disconnesso dal server normalmente.")
    except websockets.exceptions.ConnectionRefused:
        print(f"ERRORE: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE CLIENT: Si è verificato un errore: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(client_loop())