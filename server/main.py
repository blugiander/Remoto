import websockets
import asyncio
import json
import random # Assicurati che random sia importato se lo usi per i PIN
from relay import Relay

relay = Relay()

# Assicurati che queste mappe esistano nella classe Relay o vengano inizializzate qui
# Se non esistono già, dovrebbero essere aggiunte a relay.py.__init__
# Esempio:
# class Relay:
#     def __init__(self):
#         self.clients = {}
#         self.technicians = {}
#         self.ws_to_id = {}
#         self.ws_to_role = {}
#         self.client_pins = {} # Aggiunto per gestire i PIN
#         self.technician_to_client = {} # Aggiunto per associare tecnico a client

# Funzione per gestire la connessione di un singolo websocket
async def handler(websocket):
    global relay
    try:
        # Fase di registrazione iniziale
        registration_message_str = await websocket.recv()
        registration_data = json.loads(registration_message_str)

        role = registration_data.get('role')
        id = registration_data.get('id')
        pin = registration_data.get('pin') # Questo è presente solo per i tecnici

        if not role or not id:
            print(f"Server ERRORE: Messaggio di registrazione non valido da {websocket.remote_address}. Dati: {registration_data}")
            await websocket.close()
            return

        if role == 'client':
            # Genera un PIN unico per il client
            generated_pin = str(random.randint(100000, 999999)) # Genera un PIN di 6 cifre
            await relay.register(websocket, role, id)
            relay.client_pins[id] = generated_pin # Salva il PIN associato all'ID del client
            await websocket.send(json.dumps({"status": "registered", "pin": generated_pin}))
            print(f"Server INFO: Client {id} registrato. PIN generato: {generated_pin}. Da: {websocket.remote_address}")

        elif role == 'technician':
            # Il tecnico fornisce un PIN per connettersi a un client specifico
            if pin is None:
                print(f"Server ERRORE: Tecnico {id} ha tentato la registrazione senza PIN. Da: {websocket.remote_address}")
                await websocket.send(json.dumps({"status": "invalid_pin"}))
                await websocket.close()
                return

            target_client_id = None
            # Trova il client associato al PIN fornito
            for c_id, c_pin in relay.client_pins.items():
                if c_pin == pin:
                    target_client_id = c_id
                    break

            if target_client_id:
                await relay.register(websocket, role, id)
                relay.technician_to_client[id] = target_client_id # Associa il tecnico al client
                await websocket.send(json.dumps({"status": "connected"}))
                print(f"Server INFO: Tecnico {id} registrato e collegato al client {target_client_id}. Da: {websocket.remote_address}")
            else:
                await websocket.send(json.dumps({"status": "invalid_pin"}))
                print(f"Server INFO: Tentativo di connessione tecnico {id} con PIN non valido: {pin}. Da: {websocket.remote_address}")
                await websocket.close()
                return
        else:
            print(f"Server ERRORE: Ruolo sconosciuto '{role}' durante la registrazione da {websocket.remote_address}.")
            await websocket.close()
            return

        # Loop principale per la gestione dei messaggi successivi
        async for message in websocket:
            await handle_message(websocket, message) # Passa il websocket e il messaggio

    except websockets.exceptions.ConnectionClosedOK:
        print(f"Server INFO: Connessione chiusa normalmente per {relay.ws_to_role.get(websocket, 'sconosciuto')} (ID: {relay.ws_to_id.get(websocket, 'N/A')}).")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Server ERRORE: Connessione chiusa inaspettatamente per {relay.ws_to_role.get(websocket, 'sconosciuto')} (ID: {relay.ws_to_id.get(websocket, 'N/A')}): {e}")
    except json.JSONDecodeError:
        print(f"Server ERRORE: Ricevuto JSON non valido da {websocket.remote_address}. Messaggio: {message[:100]}...")
    except Exception as e:
        print(f"Server ERRORE generale nel handler per {relay.ws_to_role.get(websocket, 'sconosciuto')} (ID: {relay.ws_to_id.get(websocket, 'N/A')}): {e}", exc_info=True)
    finally:
        # Assicurati di deregistrare il websocket alla disconnessione
        await relay.deregister(websocket)


async def handle_message(websocket, message):
    global relay
    
    # Decodifica il messaggio JSON
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print(f"Server ERRORE: Messaggio non JSON ricevuto da {websocket.remote_address}. Messaggio: {message[:100]}...")
        return

    msg_type = data.get('type')
    
    # *** MODIFICA CRITICA QUI: Otteniamo ruolo e ID del mittente dalle mappe del relay ***
    # Non ci fidiamo dei campi 'role' e 'id' all'interno del payload del messaggio stesso,
    # perché il tecnico non li include nei messaggi di 'command'.
    sender_role = relay.ws_to_role.get(websocket)
    sender_id = relay.ws_to_id.get(websocket)

    # Stampa i dati del mittente per debug
    print(f"Server DEBUG: Ricevuto messaggio. Tipo: {msg_type}, Ruolo mittente: {sender_role}, ID mittente: {sender_id}, da {websocket.remote_address}")

    msg_content = data.get('content') # Contenuto del messaggio (frame o dati del comando)
    target_id = data.get('target_id') # L'ID del destinatario (tecnico per frame, client per comando)

    if msg_type == 'message':
        # Questo è un messaggio dello schermo, inviato dal client
        if sender_role == 'client':
            # L'ID del client mittente è sender_id
            if sender_id:
                # Trova il tecnico associato a questo client
                associated_technician_id = None
                for tech_id, client_assoc_id in relay.technician_to_client.items():
                    if client_assoc_id == sender_id:
                        associated_technician_id = tech_id
                        break
                
                if associated_technician_id:
                    # Inoltra l'intero messaggio originale (come stringa) al tecnico
                    # Il relay gestirà il contenuto per il tecnico
                    await relay.forward(websocket, associated_technician_id, message) 
                    print(f"Server DEBUG: Ricevuto messaggio di tipo '{msg_type}' (schermo) da client (ID: {sender_id}).")
                else:
                    print(f"Server DEBUG: Nessun tecnico associato al client {sender_id}. Frame non inoltrato.")
            else:
                print(f"Server ERRORE: Messaggio client non registrato. (Mittente: {websocket.remote_address})")
        else:
            print(f"Server ERRORE: Messaggio di tipo 'message' ricevuto da ruolo non client: {sender_role}.")

    elif msg_type == 'command': 
        # Questo è un comando, inviato dal tecnico
        if sender_role == 'technician':
            # sender_id è l'ID del tecnico mittente. target_id è l'ID del client di destinazione.
            if msg_content and target_id:
                # Inoltra l'intero messaggio originale (come stringa) al client di destinazione
                await relay.forward(websocket, target_id, message) 
                print(f"Server DEBUG: Ricevuto messaggio di tipo '{msg_type}' da {sender_role} (ID: {sender_id}).")
                print(f"Server DEBUG: Inoltrato comando da tecnico {sender_id} a client {target_id}.") # Questo è il log chiave!
            else:
                print(f"Server DEBUG: Comando non valido da {sender_role} (ID: {sender_id}) o contenuto/target vuoto.")
        else:
            print(f"Server DEBUG: Messaggio di tipo 'command' ricevuto da ruolo non tecnico: {sender_role}.")
    else:
        print(f"Server DEBUG: Tipo di messaggio sconosciuto: {msg_type}.")


# Funzione principale per avviare il server
async def main():
    # Aggiungi client_pins e technician_to_client a Relay se non sono già lì
    # (è meglio definirli nel __init__ di Relay, ma li mettiamo qui come promemoria)
    if not hasattr(relay, 'client_pins'):
        relay.client_pins = {}
    if not hasattr(relay, 'technician_to_client'):
        relay.technician_to_client = {}

    start_server = websockets.serve(handler, "0.0.0.0", 8765)
    print("Server in ascolto su porta 8765...")
    await start_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())