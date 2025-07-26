# server/main.py

import asyncio
import websockets
import json
import random
import string
import time
from datetime import datetime

from config import SERVER_HOST, SERVER_PORT # Importa dalla tua config.py

# Dizionari per gestire le connessioni
connected_clients = {}  # {client_id: websocket}
connected_technicians = {} # {technician_id: websocket}
client_pins = {} # {client_id: pin}
active_sessions = {} # {pin: {"client": websocket, "technician": websocket}}

async def generate_unique_pin():
    """Genera un PIN numerico di 6 cifre unico."""
    while True:
        pin = ''.join(random.choices(string.digits, k=6))
        if pin not in active_sessions and pin not in client_pins.values():
            return pin

async def handler(websocket):
    client_ip = websocket.remote_address[0]
    print(f"SERVER: Nuova connessione da {client_ip}.")

    try:
        # Primo messaggio per la registrazione
        registration_message_str = await websocket.recv()
        registration_message = json.loads(registration_message_str)

        msg_type = registration_message.get("type")
        role = registration_message.get("role")
        id_val = registration_message.get("id")

        if msg_type == "register":
            if role == "client":
                if id_val in connected_clients:
                    print(f"SERVER: CLIENT {id_val} ha tentato di riconnettersi senza disconnessione precedente. Chiudo la vecchia connessione.")
                    # Chiusura forzata della vecchia connessione se esiste
                    old_ws = connected_clients.get(id_val)
                    if old_ws and not old_ws.closed:
                        await old_ws.close()
                    # Rimuovi sessioni attive legate a questo client
                    for pin, session in list(active_sessions.items()):
                        if session["client"] == old_ws:
                            del active_sessions[pin]
                            if pin in client_pins:
                                del client_pins[pin]
                            print(f"SERVER: Chiusa sessione attiva e rimosso PIN {pin} per vecchio client {id_val}.")


                pin = await generate_unique_pin()
                connected_clients[id_val] = websocket
                client_pins[id_val] = pin
                print(f"SERVER: CLIENT {id_val} registrato con PIN: {pin}")

                response = {"status": "registered", "pin": pin}
                await websocket.send(json.dumps(response))

            elif role == "technician":
                tech_pin = registration_message.get("pin")
                if not tech_pin:
                    print(f"SERVER: TECNICO da {client_ip} ha tentato la registrazione senza PIN.")
                    await websocket.send(json.dumps({"status": "error", "message": "PIN richiesto per tecnico."}))
                    return

                # Trova il client_id associato al PIN
                client_id_for_pin = None
                for c_id, p in client_pins.items():
                    if p == tech_pin:
                        client_id_for_pin = c_id
                        break

                if client_id_for_pin and client_id_for_pin in connected_clients:
                    client_ws = connected_clients[client_id_for_pin]
                    
                    # Controlla se una sessione è già attiva per questo PIN
                    if tech_pin in active_sessions:
                        print(f"SERVER: Sessione per PIN {tech_pin} già attiva. Chiudo la vecchia connessione tecnico.")
                        old_tech_ws = active_sessions[tech_pin]["technician"]
                        if old_tech_ws and not old_tech_ws.closed:
                            await old_tech_ws.close() # Forzo la disconnessione del vecchio tecnico
                        # Non elimino l'intera sessione, solo rimpiazzo il tecnico
                        active_sessions[tech_pin]["technician"] = websocket
                    else:
                        active_sessions[tech_pin] = {"client": client_ws, "technician": websocket}

                    connected_technicians[id_val] = websocket # Registra il tecnico con il suo ID
                    print(f"SERVER: TECNICO {id_val} (PIN: {tech_pin}) connesso al CLIENT {client_id_for_pin}.")
                    response = {"status": "registered", "message": f"Connesso al client {client_id_for_pin}"}
                    await websocket.send(json.dumps(response))

                    # Notifica il client che un tecnico si è connesso (opzionale)
                    # await client_ws.send(json.dumps({"type": "notification", "message": "Un tecnico si è connesso alla tua sessione."}))
                else:
                    print(f"SERVER: TECNICO {id_val} ha tentato di connettersi a PIN {tech_pin} inesistente o client non connesso.")
                    await websocket.send(json.dumps({"status": "error", "message": "PIN non valido o client non connesso."}))
                    return
            else:
                print(f"SERVER: Ruolo '{role}' non riconosciuto per {client_ip}.")
                await websocket.send(json.dumps({"status": "error", "message": "Ruolo non valido."}))
                return
        else:
            print(f"SERVER: Messaggio di registrazione non valido da {client_ip}: {registration_message_str}")
            await websocket.send(json.dumps({"status": "error", "message": "Messaggio di registrazione non valido."}))
            return

        # Loop principale per routing messaggi
        while True:
            try:
                message_str = await websocket.recv()
                message = json.loads(message_str)
                
                msg_type = message.get("type")
                content_type = message.get("content_type")
                sender_id = message.get("id")

                # Ottieni la sessione attiva per il websocket corrente
                current_session_pin = None
                is_client = False
                is_technician = False

                for pin, session in active_sessions.items():
                    if session["client"] == websocket:
                        current_session_pin = pin
                        is_client = True
                        break
                    if session["technician"] == websocket:
                        current_session_pin = pin
                        is_technician = True
                        break
                
                if current_session_pin:
                    target_client_ws = active_sessions[current_session_pin]["client"]
                    target_technician_ws = active_sessions[current_session_pin]["technician"]

                    if is_client and msg_type == "message" and content_type == "screen":
                        # Client invia schermo -> Invia al tecnico associato
                        if target_technician_ws and not target_technician_ws.closed:
                            await target_technician_ws.send(message_str)
                            # print(f"SERVER: Inviato frame schermo da {sender_id} a tecnico associato (PIN: {current_session_pin}).")
                        # else:
                            # print(f"SERVER DEBUG: Tentato invio schermo da {sender_id} ma tecnico per PIN {current_session_pin} non connesso.")
                    elif is_technician and msg_type == "command":
                        # Tecnico invia comando -> Invia al client associato
                        if target_client_ws and not target_client_ws.closed:
                            await target_client_ws.send(message_str)
                            print(f"SERVER: Inviato comando da tecnico {sender_id} a client associato (PIN: {current_session_pin}).")
                        # else:
                            # print(f"SERVER DEBUG: Tentato invio comando da tecnico {sender_id} ma client per PIN {current_session_pin} non connesso.")
                    else:
                        print(f"SERVER AVVISO: Messaggio inatteso da {sender_id} (tipo: {msg_type}, contenuto: {content_type})")
                else:
                    # Messaggio da client/tecnico non in una sessione attiva
                    if websocket in connected_clients.values() and msg_type == "message" and content_type == "screen":
                        # Un client sta inviando schermate ma non ha una sessione attiva con un tecnico
                        # Questo è normale se un tecnico non si è ancora connesso al suo PIN
                        # print(f"SERVER DEBUG: Client {sender_id} invia schermo senza tecnico connesso.")
                        pass # Nessuna azione richiesta, il client continuerà a inviare
                    elif websocket in connected_technicians.values() and msg_type == "command":
                        print(f"SERVER AVVISO: Tecnico {sender_id} ha inviato un comando ma non è in una sessione attiva.")
                    else:
                        print(f"SERVER AVVISO: Messaggio non instradabile da {sender_id} (WS non in sessione): {message_str[:100]}...")


            except websockets.exceptions.ConnectionClosedOK:
                print(f"SERVER: Connessione chiusa normalmente da {client_ip}.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"SERVER ERRORE: Connessione chiusa inaspettatamente da {client_ip}: {e}")
                break
            except json.JSONDecodeError:
                print(f"SERVER ERRORE: JSON non valido ricevuto da {client_ip}: {message_str[:100]}...")
            except Exception as e:
                print(f"SERVER ERRORE: Errore durante gestione messaggio da {client_ip}: {e}")
                break # Rompe il loop in caso di errore grave

    except websockets.exceptions.ConnectionClosedOK:
        print(f"SERVER: Connessione iniziale chiusa normalmente da {client_ip}.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"SERVER ERRORE: Connessione iniziale chiusa inaspettatamente da {client_ip}: {e}")
    except json.JSONDecodeError:
        print(f"SERVER ERRORE: JSON di registrazione non valido da {client_ip}.")
    except Exception as e:
        print(f"SERVER ERRORE: Errore durante la fase di registrazione per {client_ip}: {e}")
    finally:
        # Pulizia delle connessioni e delle sessioni al termine della connessione
        print(f"SERVER: Pulizia connessione per {client_ip}...")
        is_client_disconnected = False
        is_technician_disconnected = False
        
        # Rimuovi dai client connessi
        for c_id, ws in list(connected_clients.items()):
            if ws == websocket:
                print(f"SERVER: CLIENT {c_id} disconnesso.")
                del connected_clients[c_id]
                if c_id in client_pins:
                    disconnected_pin = client_pins[c_id]
                    del client_pins[c_id]
                    print(f"SERVER: PIN {disconnected_pin} rimosso per client {c_id}.")
                    # Se era un client, rimuovi l'intera sessione attiva legata al suo PIN
                    if disconnected_pin in active_sessions:
                        tech_ws = active_sessions[disconnected_pin]["technician"]
                        if tech_ws and not tech_ws.closed:
                            print(f"SERVER: Notifico tecnico connesso al PIN {disconnected_pin} della disconnessione del client.")
                            try:
                                await tech_ws.send(json.dumps({"type": "notification", "message": "Il client si è disconnesso dalla sessione."}))
                            except Exception as e:
                                print(f"SERVER AVVISO: Fallita notifica tecnico su disconnessione client: {e}")
                        del active_sessions[disconnected_pin]
                        print(f"SERVER: Sessione attiva per PIN {disconnected_pin} terminata (client disconnesso).")
                is_client_disconnected = True
                break
        
        # Rimuovi dai tecnici connessi
        if not is_client_disconnected: # Se non era un client, potrebbe essere un tecnico
            for t_id, ws in list(connected_technicians.items()):
                if ws == websocket:
                    print(f"SERVER: TECNICO {t_id} disconnesso.")
                    del connected_technicians[t_id]
                    # Se era un tecnico, rimuovi solo il tecnico dalla sessione attiva
                    for pin, session in list(active_sessions.items()):
                        if session["technician"] == websocket:
                            print(f"SERVER: TECNICO {t_id} disconnesso dalla sessione per PIN {pin}. Sessione client rimane attiva.")
                            # Non cancelliamo la sessione intera, solo il tecnico
                            active_sessions[pin]["technician"] = None # Imposta a None per indicare che non c'è tecnico
                            # Notifica il client che il tecnico si è disconnesso (opzionale)
                            client_ws = active_sessions[pin]["client"]
                            if client_ws and not client_ws.closed:
                                print(f"SERVER: Notifico client connesso al PIN {pin} della disconnessione del tecnico.")
                                try:
                                    await client_ws.send(json.dumps({"type": "notification", "message": "Il tecnico si è disconnesso dalla sessione."}))
                                except Exception as e:
                                    print(f"SERVER AVVISO: Fallita notifica client su disconnessione tecnico: {e}")
                            break # Esci dal ciclo for dopo aver trovato e gestito il tecnico
                    is_technician_disconnected = True
                    break

async def main():
    print(f"SERVER: Avvio server WebSocket su ws://{SERVER_HOST}:{SERVER_PORT}")
    async with websockets.serve(handler, SERVER_HOST, SERVER_PORT):
        await asyncio.Future()  # Esegui indefinitamente

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("SERVER: Server interrotto manualmente.")
    except Exception as e:
        print(f"SERVER ERRORE CRITICO: {e}")