import asyncio
import websockets
import json
import base64
import numpy as np
import cv2
import sys
from config import SERVER_HOST, SERVER_PORT, TECHNICIAN_ID
from pynput import mouse, keyboard
import websockets.protocol # Importa websockets.protocol per accedere allo stato della connessione

# Variabili globali per la connessione WebSocket e l'event loop di asyncio
ws_global = None
asyncio_loop = None

# Funzione per gestire gli eventi del mouse e inviarli al server
def on_click(x, y, button, pressed):
    if pressed:
        button_name = str(button).split('.')[-1]
        event_data = {
            "type": "mouse_click",
            "x": x,
            "y": y,
            "button": button_name
        }
        # Controlla che la connessione sia aperta e che l'event loop sia disponibile
        if ws_global and ws_global.state == websockets.protocol.State.OPEN and asyncio_loop: 
            try:
                # Per inviare da un thread sincrono (pynput) a un loop asyncio (main),
                # devi usare run_coroutine_threadsafe e passare l'event loop.
                asyncio.run_coroutine_threadsafe(
                    ws_global.send(json.dumps({"type": "command", "target_id": "cliente-001", "content": json.dumps(event_data)})),
                    asyncio_loop 
                )
                print(f"DEBUG: Click inviato: x={x}, y={y}, button={button_name}") # DEBUG AGGIUNTO
            except Exception as e:
                print(f"ERRORE nel callback mouse durante l'invio: {e}")
        else:
            print(f"DEBUG: Connessione ws_global non aperta ({ws_global.state if ws_global else 'N/A'}) o loop non disponibile, click non inviato.") # DEBUG AGGIUNTO


# Funzione per gestire gli eventi della tastiera e inviarli al server
def on_press(key):
    try:
        char = key.char # Caratteri normali
    except AttributeError:
        char = str(key) # Tasti speciali (es. Key.space, Key.enter)
        # Semplificazione per i tasti speciali più comuni, puoi espanderla
        if 'Key.' in char:
            char = char.replace('Key.', '').lower()
        
    event_data = {
        "type": "key_press",
        "key": char
    }
    # Controlla che la connessione sia aperta e che l'event loop sia disponibile
    if ws_global and ws_global.state == websockets.protocol.State.OPEN and asyncio_loop: 
        try:
            asyncio.run_coroutine_threadsafe(
                ws_global.send(json.dumps({"type": "command", "target_id": "cliente-001", "content": json.dumps(event_data)})),
                asyncio_loop
            )
            print(f"DEBUG: Tasto inviato: {char}") # DEBUG AGGIUNTO
        except Exception as e:
            print(f"ERRORE nel callback tastiera durante l'invio: {e}")
    else:
        print(f"DEBUG: Connessione ws_global non aperta ({ws_global.state if ws_global else 'N/A'}) o loop non disponibile, tasto non inviato.") # DEBUG AGGIUNTO


async def technician_loop():
    global ws_global # Dichiara ws_global come globale per poterla assegnare
    global asyncio_loop # Dichiara asyncio_loop come globale per poterla assegnare
    
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    print(f"🔗 Connessione al server {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            ws_global = ws # Assegna la connessione WebSocket alla variabile globale
            asyncio_loop = asyncio.get_event_loop() # Ottieni e assegna l'event loop del thread principale
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
                
                # --- Avvia i listener di pynput in un executor ---
                # Questo permette ai listener sincroni di girare senza bloccare asyncio
                mouse_listener = mouse.Listener(on_click=on_click)
                keyboard_listener = keyboard.Listener(on_press=on_press)
                
                # Avvia i listener in background
                mouse_listener.start()
                keyboard_listener.start()

                print("DEBUG: Listener mouse e tastiera avviati.")

            elif data.get('status') == 'invalid_pin':
                print("❌ PIN non valido. Riprova.")
                return
            else:
                print("ERRORE: Risposta inattesa dal server durante la registrazione.")
                return

            # Loop di ricezione e visualizzazione dello schermo
            while True:
                try:
                    message_content_string = await ws.recv() 
                    encoded_frame = message_content_string 
                    
                    if encoded_frame:
                        decoded_frame = base64.b64decode(encoded_frame)
                        np_array = np.frombuffer(decoded_frame, np.uint8)
                        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

                        if frame is not None:
                            cv2.imshow("Schermo Remoto", frame)
                            # Permetti al tecnico di chiudere la finestra con 'q' o chiudendola direttamente
                            if cv2.waitKey(1) & 0xFF == ord('q'): 
                                print("DEBUG: Chiusura richiesta dall'utente.")
                                break
                    # else:
                        # print("DEBUG: Ricevuto frame vuoto o non valido.") # Per debug
                except websockets.exceptions.ConnectionClosedOK:
                    print("Disconnesso dal server normalmente durante la ricezione frame.")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"ERRORE: Connessione chiusa inaspettatamente dal server: {e}")
                    break
                except json.JSONDecodeError as e:
                    print(f"ERRORE: Errore di decodifica JSON dal server: {e}. Messaggio raw: {message_content_string[:200]}...")
                except Exception as e:
                    print(f"ERRORE TECNICO durante elaborazione frame: {e}") 
            
            cv2.destroyAllWindows() # Chiudi la finestra di OpenCV alla fine

    except ConnectionRefusedError: 
        print(f"ERRORE: Connessione rifiutata dal server {uri}. Assicurati che il server sia in esecuzione e la porta sia aperta.")
    except Exception as e:
        print(f"ERRORE TECNICO generale: {e}")
    finally:
        # Assicurati di fermare i listener di pynput alla fine
        if 'mouse_listener' in locals() and mouse_listener.running:
            mouse_listener.stop()
            print("DEBUG: Mouse listener stopped.")
        if 'keyboard_listener' in locals() and keyboard_listener.running:
            keyboard_listener.stop()
            print("DEBUG: Keyboard listener stopped.")
        # Assicurati di chiudere la connessione WebSocket se è ancora aperta
        if ws_global and ws_global.state != websockets.protocol.State.CLOSED: 
            await ws_global.close()
            print("DEBUG: WebSocket connection closed.")

if __name__ == "__main__":
    asyncio.run(technician_loop())