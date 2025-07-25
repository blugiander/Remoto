import asyncio
import websockets
import json
import base64
import numpy as np
import cv2
import sys
from config import SERVER_HOST, SERVER_PORT, TECHNICIAN_ID
from pynput import mouse, keyboard
import websockets.protocol

ws_global = None
asyncio_loop = None

def on_click(x, y, button, pressed):
    if pressed:
        button_name = str(button).split('.')[-1]
        event_data = {
            "type": "mouse_click",
            "x": x,
            "y": y,
            "button": button_name
        }
        # Verifica che ws_global sia un WebSocket valido e aperto prima di inviare
        if ws_global and ws_global.state == websockets.protocol.State.OPEN and asyncio_loop: 
            try:
                # Assicurati che il target_id sia corretto.
                # Per ora, è hardcoded come "cliente-001".
                # In una versione più avanzata, potresti volerlo selezionare.
                asyncio.run_coroutine_threadsafe(
                    ws_global.send(json.dumps({"type": "command", "target_id": "cliente-001", "content": json.dumps(event_data)})),
                    asyncio_loop 
                )
                print(f"DEBUG TECNICO: Click inviato: x={x}, y={y}, button={button_name}")
            except Exception as e:
                print(f"ERRORE TECNICO nel callback mouse durante l'invio: {e}")
        else:
            print(f"DEBUG TECNICO: Connessione ws_global non aperta ({ws_global.state if ws_global else 'N/A'}) o loop non disponibile, click non inviato.")

def on_press(key):
    try:
        char = key.char
    except AttributeError:
        char = str(key)
        if 'Key.' in char:
            char = char.replace('Key.', '').lower()
        
    event_data = {
        "type": "key_press",
        "key": char
    }
    if ws_global and ws_global.state == websockets.protocol.State.OPEN and asyncio_loop: 
        try:
            # Assicurati che il target_id sia corretto.
            asyncio.run_coroutine_threadsafe(
                ws_global.send(json.dumps({"type": "command", "target_id": "cliente-001", "content": json.dumps(event_data)})),
                asyncio_loop
            )
            print(f"DEBUG TECNICO: Tasto inviato: {char}")
        except Exception as e:
            print(f"ERRORE TECNICO nel callback tastiera durante l'invio: {e}")
    else:
        print(f"DEBUG TECNICO: Connessione ws_global non aperta ({ws_global.state if ws_global else 'N/A'}) o loop non disponibile, tasto non inviato.")


async def technician_loop():
    global ws_global
    global asyncio_loop
    
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    print(f"🔗 Tecnico: Connessione al server {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            ws_global = ws
            asyncio_loop = asyncio.get_event_loop()
            print("✅ Tecnico: Connesso.")

            pin = input("🔑 Tecnico: Inserisci il PIN ricevuto dal cliente: ")
            register_message = json.dumps({
                "type": "register",
                "role": "technician",
                "id": TECHNICIAN_ID,
                "pin": pin
            })
            await ws.send(register_message)
            print(f"📝 Tecnico: Inviato messaggio di registrazione (ID: {TECHNICIAN_ID}).")

            response = await ws.recv()
            data = json.loads(response)
            if data.get('status') == 'connected':
                print("✅ Tecnico: Connesso. Ricezione schermo...")
                
                mouse_listener = mouse.Listener(on_click=on_click)
                keyboard_listener = keyboard.Listener(on_press=on_press)
                
                mouse_listener.start()
                keyboard_listener.start()

                print("DEBUG TECNICO: Listener mouse e tastiera avviati.")

            elif data.get('status') == 'invalid_pin':
                print("❌ Tecnico: PIN non valido. Riprova.")
                return
            else:
                print("ERRORE TECNICO: Risposta inattesa dal server durante la registrazione.")
                return

            # Loop principale per ricevere messaggi (schermo e altri)
            while True:
                try:
                    message_content_string = await ws.recv() 
                    
                    received_data = json.loads(message_content_string)
                    
                    if received_data.get('type') == 'message' and 'content' in received_data:
                        # Questo è il frame dello schermo dal client
                        encoded_frame = received_data['content']
                        
                        if encoded_frame:
                            decoded_frame = base64.b64decode(encoded_frame)
                            np_array = np.frombuffer(decoded_frame, np.uint8)
                            frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

                            if frame is not None:
                                cv2.imshow("Schermo Remoto", frame)
                                # cv2.waitKey(1) permette di aggiornare la finestra
                                # e cattura gli eventi tastiera (come 'q' per uscire)
                                if cv2.waitKey(1) & 0xFF == ord('q'): 
                                    print("DEBUG TECNICO: Chiusura richiesta dall'utente.")
                                    break
                            else:
                                print("ERRORE TECNICO: cv2.imdecode ha restituito None (frame corrotto/vuoto?).")
                        else:
                            print("DEBUG TECNICO: Ricevuto frame codificato Base64 vuoto.")
                    elif received_data.get('type') == 'command':
                        # Se il tecnico riceve un comando da un altro tecnico (o da se stesso tramite echo del server)
                        print(f"DEBUG TECNICO: Ricevuto un comando eco dal server: {received_data.get('content')}")
                    else:
                        print(f"DEBUG TECNICO: Ricevuto messaggio non gestito. Tipo: {received_data.get('type')}. Contenuto: {message_content_string[:200]}...")

                except websockets.exceptions.ConnectionClosedOK:
                    print("Tecnico: Disconnesso dal server normalmente durante la recezione frame.")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"ERRORE TECNICO: Connessione chiusa inaspettatamente dal server: {e}")
                    break
                except json.JSONDecodeError as e:
                    print(f"ERRORE TECNICO: Errore di decodifica JSON dal server: {e}. Messaggio raw: {message_content_string[:200]}...")
                except Exception as e:
                    print(f"ERRORE TECNICO durante elaborazione frame o visualizzazione: {e}", exc_info=True)
            
            # Chiudi la finestra OpenCV quando il loop termina
            cv2.destroyAllWindows()

    except ConnectionRefusedError: 
        print(f"ERRORE TECNICO: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE TECNICO generale nella loop principale: {e}", exc_info=True)
    finally:
        # Assicurati che i listener siano fermati correttamente
        if 'mouse_listener' in locals() and mouse_listener.running:
            mouse_listener.stop()
            print("DEBUG TECNICO: Mouse listener stopped.")
        if 'keyboard_listener' in locals() and keyboard_listener.running:
            keyboard_listener.stop()
            print("DEBUG TECNICO: Keyboard listener stopped.")
        # Chiudi la connessione WebSocket se è ancora aperta
        if ws_global and ws_global.state != websockets.protocol.State.CLOSED: 
            await ws_global.close()
            print("DEBUG TECNICO: WebSocket connection closed.")

if __name__ == "__main__":
    asyncio.run(technician_loop())