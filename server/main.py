# server/main.py

import websockets
import asyncio
import json
import random
from relay import Relay # Assicurati che relay.py sia nella stessa directory

relay = Relay() # L'istanza di Relay viene creata una volta all'avvio del server

async def handler(websocket):
    global relay
    current_role = None
    current_id = None

    try:
        # Fase di registrazione iniziale
        registration_message_str = await websocket.recv()
        registration_data = json.loads(registration_message_str)

        role = registration_data.get('role')
        id = registration_data.get('id')
        pin_from_request = registration_data.get('pin') # PIN fornito dal tecnico

        if not role or not id:
            print(f"Server ERRORE: Messaggio di registrazione non valido da {websocket.remote_address}. Dati: {registration_data}")
            await websocket.close()
            return

        current_role = role
        current_id = id
        
        # Registra il websocket nel relay prima di elaborare ulteriormente
        await relay.register(websocket, role, id)

        if role == 'client':
            # Genera un PIN unico per il client e lo associa all'ID del client
            generated_pin = str(random.randint(100000, 999999)) # PIN di 6 cifre
            relay.client_pins[id] = generated_pin # Salva il PIN associato all'ID del client
            await websocket.send(json.dumps({"type": "status", "status": "registered", "role": "client", "id": id, "pin": generated_pin}))
            print(f"Server INFO: Client {id} registrato. PIN generato: {generated_pin}. Da: {websocket.remote_address}")

        elif role == 'technician':
            # Il tecnico fornisce un PIN per connettersi a un client specifico
            if pin_from_request is None:
                print(f"Server ERRORE: Tecnico {id} ha tentato la registrazione senza PIN. Da: {websocket.remote_address}")
                await websocket.send(json.dumps({"type": "status", "status": "invalid_pin"}))
                await websocket.close()
                return

            target_client_id = None
            # Trova il client associato al PIN fornito
            for c_id, c_pin in relay.client_pins.items():
                if c_pin == pin_from_request:
                    # Verifica se il client associato al PIN è attualmente connesso al server
                    if c_id in relay.clients:
                        target_client_id = c_id
                        break
                    else:
                        print(f"Server INFO: Client {c_id} associato al PIN {c_pin} non è attualmente connesso. Non posso collegare il tecnico.")
                        
            if target_client_id:
                relay.technician_to_client[id] = target_client_id # Associa il tecnico al client
                # Invia un messaggio di conferma al tecnico.
                # Includi l'ID del client a cui è stato associato il tecnico.
                await websocket.send(json.dumps({"type": "status", "status": "registered", "role": "technician", "id": id, "target_client_id": target_client_id}))
                print(f"Server INFO: Tecnico {id} registrato e collegato al client {target_client_id}. Da: {websocket.remote_address}")
            else:
                await websocket.send(json.dumps({"type": "status", "status": "invalid_pin"}))
                print(f"Server INFO: Tentativo di connessione tecnico {id} con PIN non valido o client non disponibile: {pin_from_request}. Da: {websocket.remote_address}")
                await websocket.close()
                return
        else:
            print(f"Server ERRORE: Ruolo sconosciuto '{role}' durante la registrazione da {websocket.remote_address}.")
            await websocket.close()
            return

        # Loop principale per la gestione dei messaggi successivi
        async for message in websocket:
            await handle_message(websocket, message)

    except websockets.exceptions.ConnectionClosedOK:
        print(f"Server INFO: Connessione chiusa normalmente per {relay.ws_to_role.get(websocket, 'sconosciuto')} (ID: {relay.ws_to_id.get(websocket, 'N/A')}).")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Server ERRORE: Connessione chiusa inaspettatamente per {relay.ws_to_role.get(websocket, 'sconosciuto')} (ID: {relay.ws_to_id.get(websocket, 'N/A')}): {e}")
    except json.JSONDecodeError:
        print(f"Server ERRORE: Ricevuto JSON non valido da {websocket.remote_address}. Messaggio: {registration_message_str[:100] if 'registration_message_str' in locals() else message[:100]}...")
    except Exception as e:
        print(f"Server ERRORE generale nel handler per {current_role if current_role else 'sconosciuto'} (ID: {current_id if current_id else 'N/A'}): {e}", exc_info=True)
    finally:
        # Assicurati di deregistrare il websocket alla disconnessione
        await relay.deregister(websocket)


async def handle_message(websocket, message):
    global relay
    
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print(f"Server ERRORE: Messaggio non JSON ricevuto da {websocket.remote_address}. Messaggio: {message[:100]}...")
        return

    msg_type = data.get('type')
    sender_role = relay.ws_to_role.get(websocket)
    sender_id = relay.ws_to_id.get(websocket) 

    # Assicurati che il sender_id sia valido prima di procedere
    if not sender_id or not sender_role:
        print(f"Server AVVISO: Messaggio da un websocket non identificato o non registrato. Ruolo: {sender_role}, ID: {sender_id}. Ignorato.")
        return

    print(f"Server DEBUG: Ricevuto messaggio. Tipo: {msg_type}, Ruolo mittente: {sender_role}, ID mittente: {sender_id}, da {websocket.remote_address}")

    if msg_type == 'message':
        # Questo è il tipo di messaggio usato per i frame dello schermo dal client
        if sender_role == 'client':
            # Recupera l'ID del tecnico associato a questo client
            associated_technician_id = None
            for tech_id, client_assoc_id in relay.technician_to_client.items():
                if client_assoc_id == sender_id:
                    associated_technician_id = tech_id
                    break
            
            if associated_technician_id:
                # Il messaggio originale del client contiene già l'id e content_type: "screen"
                # Semplicemente inoltriamo l'intero messaggio come ricevuto.
                print(f"Server DEBUG: Inoltro messaggio (tipo: '{msg_type}', content_type: '{data.get('content_type')}') da client {sender_id} a tecnico {associated_technician_id}.")
                await relay.forward(websocket, associated_technician_id, message) 
            else:
                print(f"Server DEBUG: Nessun tecnico associato al client {sender_id}. Messaggio (tipo: '{msg_type}') non inoltrato.")
        else:
            print(f"Server AVVISO: Messaggio di tipo '{msg_type}' ricevuto da ruolo non client: {sender_role}. Ignorato.")

    elif msg_type == 'command': 
        # Questo è il tipo di messaggio usato per i comandi (mouse, tastiera) dal tecnico
        if sender_role == 'technician':
            # Il tecnico ha già incluso il target_id nel messaggio.
            target_client_id = data.get('target_id')
            
            if target_client_id:
                print(f"Server DEBUG: Inoltro comando (tipo: '{msg_type}', command_type: '{data.get('command_type')}') da tecnico {sender_id} a client {target_client_id}.")
                await relay.forward(websocket, target_client_id, message) 
            else:
                print(f"Server DEBUG: Target client ID mancante nel comando da tecnico {sender_id}. Comando non inoltrato.")
        else:
            print(f"Server AVVISO: Messaggio di tipo '{msg_type}' ricevuto da ruolo non tecnico: {sender_role}. Ignorato.")
    else:
        print(f"Server AVVISO: Tipo di messaggio sconosciuto: '{msg_type}' da ruolo: {sender_role}, ID: {sender_id}. Messaggio: {message[:100]}...")


async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("Server in ascolto su porta 8765...")
    await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())