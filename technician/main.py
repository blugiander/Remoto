# technician/main.py

import asyncio
import websockets
import json
import base64
import numpy as np
import cv2
import sys
from config import SERVER_HOST, SERVER_PORT, TECHNICIAN_ID

async def technician_loop():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    print(f"🔗 Connessione al server {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            print("✅ Connesso.")

            # Fase di registrazione
            pin = input("🔑 Inserisci il PIN ricevuto dal cliente: ")
            register_message = json.dumps({
                "type": "register",
                "role": "technician",
                "id": TECHNICIAN_ID,
                "pin": pin
            })
            await ws.send(register_message)
            print(f"📝 Inviato messaggio di registrazione come tecnico (ID: {TECHNICIAN_ID}).")

            # Attendere la conferma di connessione dal server
            response = await ws.recv()
            data = json.loads(response)
            if data.get('status') == 'connected':
                print("✅ Connesso. Ricezione schermo...")
            elif data.get('status') == 'invalid_pin':
                print("❌ PIN non valido. Riprova.")
                return
            else:
                print("ERRORE: Risposta inattesa dal server durante la registrazione.")
                return

            # Loop di ricezione e visualizzazione dello schermo
            while True:
                try:
                    # Il messaggio ricevuto dal server è la stringa JSON del frame (o comando)
                    message_content_string = await ws.recv() 
                    
                    # Decodifica la stringa JSON (che è il frame codificato in base64)
                    # Non fare data.get('content') perché message_content_string è già il contenuto!
                    encoded_frame = message_content_string 
                    
                    if encoded_frame:
                        decoded_frame = base64.b64decode(encoded_frame)
                        np_array = np.frombuffer(decoded_frame, np.uint8)
                        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

                        if frame is not None:
                            cv2.imshow("Schermo Remoto", frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'): # Premi 'q' per chiudere
                                break
                        # else:
                        #     print("ERRORE: Frame decodificato è None, possibile problema di dati.")

                except websockets.exceptions.ConnectionClosedOK:
                    print("Disconnesso dal server normalmente durante la ricezione frame.")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"ERRORE: Connessione chiusa inaspettatamente dal server: {e}")
                    break
                except json.JSONDecodeError as e:
                    print(f"ERRORE: Errore di decodifica JSON dal server: {e}. Messaggio raw: {message_content_string[:200]}...")
                except Exception as e:
                    # Corretto: rimosso exc_info=True per print
                    print(f"ERRORE TECNICO durante elaborazione frame: {e}") 
            
            cv2.destroyAllWindows() # Chiudi le finestre OpenCV quando il loop termina

    except websockets.exceptions.ConnectionRefused: # Corretto: rimosso websockets.exceptions.
        print(f"ERRORE: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE TECNICO generale: {e}") # Corretto: rimosso exc_info=True per print

if __name__ == "__main__":
    asyncio.run(technician_loop())