# server/main.py

import asyncio
import websockets
import json
from relay import Relay
from auth import AuthManager
from config import SERVER_HOST, SERVER_PORT

relay = Relay()
auth = AuthManager()
auth.set_relay(relay) # <--- AGGIUNTA QUESTA RIGA: Passa l'istanza di Relay ad AuthManager

async def handler(ws):
    client_address = ws.remote_address
    print(f"Server DEBUG: Nuova connessione da {client_address}")

    try:
        async for msg in ws:
            data = json.loads(msg) 
            role = data.get('role')
            id = data.get('id')
            pin = data.get('pin')
            msg_type = data.get('type')
            
            content_to_forward = data.get('content') 

            print(f"Server DEBUG: Ricevuto messaggio. Tipo: {msg_type}, Ruolo: {role}, ID: {id}, da {client_address}")

            if msg_type == 'register':
                await relay.register(ws, role, id)
                print(f"Server DEBUG: Tentativo di registrazione di {role} con ID {id}.")
                if role == 'client':
                    generated_pin = auth.create_session(id)
                    await ws.send(json.dumps({'pin': generated_pin}))
                    print(f"Server DEBUG: Client {id} registrato. PIN generato: {generated_pin}. Inviato al client.")
                else: # role == 'technician'
                    valid = auth.verify_pin(pin, technician_id=id) # <--- MODIFICATO: Passa technician_id per l'abbinamento
                    if valid:
                        await ws.send(json.dumps({'status': 'connected'}))
                        print(f"Server DEBUG: Tecnico {id} connesso con PIN {pin} valido.")
                    else:
                        await ws.send(json.dumps({'status': 'invalid_pin'}))
                        await ws.close() 
                        print(f"Server DEBUG: Tecnico {id} fallito connessione: PIN {pin} non valido.")

            elif msg_type == 'message': # Questo è per i frame dello schermo dal client
                print(f"Server DEBUG: Ricevuto messaggio di tipo 'message' (schermo) da {role} (ID: {id}).")
                if content_to_forward:
                    # Il client invia i frame allo slot tecnico della sua sessione.
                    # Dobbiamo trovare il tecnico connesso a questo client_id
                    technician_ws = relay.get_technician_for_client(id)
                    if technician_ws:
                        # Inoltra il frame direttamente al tecnico.
                        await technician_ws.send(content_to_forward) 
                        print(f"Server DEBUG: Inoltrato frame da client {id} al suo tecnico.")
                    else:
                        print(f"Server DEBUG: Nessun tecnico trovato per il client {id}. Frame non inoltrato.")
                else:
                    print(f"Server DEBUG: Messaggio di tipo 'message' da {id} con contenuto vuoto o non valido.")
            
            # --- NUOVO BLOCCO: Gestione dei comandi di input dal tecnico ---
            elif msg_type == 'command': 
                print(f"Server DEBUG: Ricevuto messaggio di tipo 'command' da {role} (ID: {id}).")
                if role == 'technician' and content_to_forward:
                    target_client_id = data.get('target_id') # Il tecnico invia a un client specifico
                    if target_client_id:
                        client_ws = relay.get_client_ws(target_client_id)
                        if client_ws:
                            # Inoltra il comando (mouse/tastiera) direttamente al client
                            await client_ws.send(content_to_forward)
                            print(f"Server DEBUG: Inoltrato comando da tecnico {id} a client {target_client_id}.")
                        else:
                            print(f"Server DEBUG: Client {target_client_id} non trovato. Comando non inoltrato.")
                    else:
                        print(f"Server DEBUG: Comando da tecnico {id} senza target_id. Comando non inoltrato.")
                else:
                    print(f"Server DEBUG: Comando non valido da {role} (ID: {id}) o contenuto vuoto.")
            # --- FINE NUOVO BLOCCO ---

            else:
                print(f"Server DEBUG: Tipo messaggio sconosciuto: {msg_type} da {id}.")

    except websockets.exceptions.ConnectionClosedOK:
        print(f"Server DEBUG: Connessione chiusa normalmente da {client_address} (ID: {relay.ws_to_id.get(ws, 'sconosciuto')}).")
    except json.JSONDecodeError as e:
        print(f"Server ERRORE: Errore di decodifica JSON dal client {client_address}: {e}. Messaggio raw: {msg[:200]}...")
    except Exception as e:
        print(f'Server ERRORE: Errore generico in handler per {client_address}: {e}')
    finally:
        relay.unregister(ws)
        print(f"Server DEBUG: Client {relay.ws_to_id.get(ws, 'sconosciuto')} disconnesso dal relay.")


async def main():
    async with websockets.serve(handler, SERVER_HOST, SERVER_PORT):
        print(f"Server in ascolto su porta {SERVER_PORT}...")
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())