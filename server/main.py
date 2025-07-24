# server/main.py

import asyncio
import websockets
import json
from relay import Relay
from auth import AuthManager
from config import SERVER_HOST, SERVER_PORT

relay = Relay()
auth = AuthManager()

async def handler(ws):
    client_address = ws.remote_address
    print(f"Server DEBUG: Nuova connessione da {client_address}")

    try:
        async for msg in ws:
            # msg è già la stringa JSON completa inviata dal client/tecnico
            data = json.loads(msg) # Parsa il messaggio JSON completo
            role = data.get('role')
            id = data.get('id')
            pin = data.get('pin')
            msg_type = data.get('type')
            
            # Il 'content' è già la stringa JSON del frame (client) o del comando (tecnico)
            # Dobbiamo estrarlo e inoltrarlo come stringa.
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
                    valid = auth.verify_pin(pin)
                    if valid:
                        await ws.send(json.dumps({'status': 'connected'}))
                        print(f"Server DEBUG: Tecnico {id} connesso con PIN {pin} valido.")
                    else:
                        await ws.send(json.dumps({'status': 'invalid_pin'}))
                        await ws.close() # Chiude la connessione se PIN non valido
                        print(f"Server DEBUG: Tecnico {id} fallito connessione: PIN {pin} non valido.")

            elif msg_type == 'message':
                print(f"Server DEBUG: Ricevuto messaggio di tipo 'message' da {role} (ID: {id}).")
                
                if content_to_forward: # Inoltra il 'content' così com'è, che è già una stringa JSON del frame/comando
                    target_id_from_sender = data.get('target_id')
                    
                    content_preview = str(content_to_forward)[:200] + ('...' if len(str(content_to_forward)) > 200 else '')
                    print(f"Server DEBUG: Chiamata relay.forward. Mittente: {id}, Target originale dal mittente: {target_id_from_sender}. Contenuto (parziale): {content_preview}")
                    
                    # NON FARE json.dumps(content_to_forward) qui, è già una stringa JSON
                    await relay.forward(ws, target_id_from_sender, content_to_forward) 
                else:
                    print(f"Server DEBUG: Messaggio di tipo 'message' da {id} con contenuto vuoto o non valido.")
            else:
                print(f"Server DEBUG: Tipo messaggio sconosciuto: {msg_type} da {id}.")

    except websockets.exceptions.ConnectionClosedOK:
        print(f"Server DEBUG: Connessione chiusa normalmente da {client_address} (ID: {relay.ws_to_id.get(ws, 'sconosciuto')}).")
    except json.JSONDecodeError as e:
        print(f"Server ERRORE: Errore di decodifica JSON dal client {client_address}: {e}. Messaggio raw: {msg[:200]}...")
    except Exception as e:
        print(f'Server ERRORE: Errore generico in handler per {client_address}: {e}', exc_info=True)
    finally:
        # Gestione della disconnessione
        relay.unregister(ws)
        print(f"Server DEBUG: Client {relay.ws_to_id.get(ws, 'sconosciuto')} disconnesso dal relay.")


async def main():
    async with websockets.serve(handler, SERVER_HOST, SERVER_PORT):
        print(f"Server in ascolto su porta {SERVER_PORT}...")
        await asyncio.Future() # Mantiene il server in esecuzione indefinitamente

if __name__ == "__main__":
    asyncio.run(main())