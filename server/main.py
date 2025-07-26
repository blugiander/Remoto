# remoto/server/main.py

import asyncio
import websockets
import json
import logging
import sys

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dizionari per tenere traccia delle connessioni
# {pin_code: websocket}
connected_clients = {}
# {technician_id: websocket}
connected_technicians = {}
# {technician_id: target_client_pin} - per tracciare a quale client è connesso un tecnico
technician_targets = {}

async def register(websocket, message):
    role = message.get("role")
    id = message.get("id")
    pin = message.get("pin") # Per i client, questo è il loro PIN; per i tecnici, è il PIN del client a cui vogliono connettersi.

    if not role or not id:
        logging.warning(f"Tentativo di registrazione con ruolo o ID mancante: {message}")
        await websocket.send(json.dumps({"type": "error", "message": "Ruolo o ID mancante nella registrazione."}))
        return

    if role == "client":
        if not pin:
            logging.warning(f"Tentativo di registrazione client senza PIN: {message}")
            await websocket.send(json.dumps({"type": "error", "message": "PIN mancante per la registrazione client."}))
            return
        if pin in connected_clients:
            logging.warning(f"Client con PIN {pin} già connesso. Disconnessione del vecchio client.")
            # Opzionale: chiudi la vecchia connessione o ignora la nuova
            await connected_clients[pin].close() # Chiude la vecchia connessione
        connected_clients[pin] = websocket
        logging.info(f"Client registrato: ID {id}, PIN {pin}")
        await websocket.send(json.dumps({"type": "status", "message": f"Registrato come client con PIN: {pin}"}))

        # Notifica i tecnici in attesa di questo client
        for tech_id, target_pin in technician_targets.items():
            if target_pin == pin and tech_id in connected_technicians:
                try:
                    await connected_technicians[tech_id].send(json.dumps({
                        "type": "notification",
                        "message": f"Il client con PIN {pin} è ora online."
                    }))
                    logging.info(f"Notificato tecnico {tech_id} che client {pin} è online.")
                except Exception as e:
                    logging.error(f"Errore nell'invio della notifica al tecnico {tech_id}: {e}")

    elif role == "technician":
        if id in connected_technicians:
            logging.warning(f"Tecnico con ID {id} già connesso. Disconnessione del vecchio tecnico.")
            await connected_technicians[id].close()
        connected_technicians[id] = websocket
        technician_targets[id] = pin # Salva il PIN del client che il tecnico vuole controllare
        logging.info(f"Tecnico registrato: ID {id}, target PIN {pin}")
        await websocket.send(json.dumps({"type": "status", "message": f"Registrato come tecnico con ID: {id}. Tentativo di connessione al client PIN: {pin}"}))

        if pin not in connected_clients:
            await websocket.send(json.dumps({"type": "error", "message": f"Client con PIN {pin} non trovato o non online."}))
            logging.warning(f"Tecnico {id} ha tentato di connettersi a client {pin} ma non è online.")
        else:
            await websocket.send(json.dumps({
                "type": "notification",
                "message": f"Connesso con successo al client con PIN: {pin}. In attesa di frame..."
            }))
            logging.info(f"Tecnico {id} connesso a client {pin}.")

    else:
        logging.warning(f"Ruolo sconosciuto durante la registrazione: {role}")
        await websocket.send(json.dumps({"type": "error", "message": "Ruolo sconosciuto."}))

async def unregister(websocket):
    # Rimuovi il client
    client_to_remove_pin = None
    for pin, ws in connected_clients.items():
        if ws == websocket:
            client_to_remove_pin = pin
            break
    if client_to_remove_pin:
        del connected_clients[client_to_remove_pin]
        logging.info(f"Client con PIN {client_to_remove_pin} disconnesso.")
        # Notifica i tecnici che erano connessi a questo client
        for tech_id, target_pin in list(technician_targets.items()): # Usa list() per modificare il dizionario durante l'iterazione
            if target_pin == client_to_remove_pin and tech_id in connected_technicians:
                try:
                    await connected_technicians[tech_id].send(json.dumps({
                        "type": "notification",
                        "message": f"Il client con PIN {client_to_remove_pin} si è disconnesso."
                    }))
                    logging.info(f"Notificato tecnico {tech_id} che client {client_to_remove_pin} è offline.")
                except Exception as e:
                    logging.error(f"Errore nell'invio della notifica di disconnessione al tecnico {tech_id}: {e}")
                # Non rimuovere il tecnico da technician_targets, potrebbe voler aspettare il client
                # del connected_technicians[tech_id] rimuove la connessione se chiude il websocket
                if tech_id in connected_technicians and connected_technicians[tech_id].closed:
                    del connected_technicians[tech_id]
                    if tech_id in technician_targets:
                        del technician_targets[tech_id]


    # Rimuovi il tecnico
    technician_to_remove_id = None
    for tech_id, ws in connected_technicians.items():
        if ws == websocket:
            technician_to_remove_id = tech_id
            break
    if technician_to_remove_id:
        del connected_technicians[technician_to_remove_id]
        if technician_to_remove_id in technician_targets:
            del technician_targets[technician_to_remove_id]
        logging.info(f"Tecnico con ID {technician_to_remove_id} disconnesso.")


async def handler(websocket):
    try:
        async for message_json in websocket:
            message = json.loads(message_json)
            msg_type = message.get("type")
            sender_role = message.get("role")
            sender_id = message.get("id") # ID del mittente (client_id o technician_id)

            if msg_type == "register":
                await register(websocket, message)
            elif msg_type == "frame" and sender_role == "client":
                pin = sender_id # Il PIN del client è il suo ID per il server
                if pin in connected_clients and connected_clients[pin] == websocket:
                    # Inoltra il frame a tutti i tecnici che hanno questo client come target
                    for tech_id, target_pin in technician_targets.items():
                        if target_pin == pin and tech_id in connected_technicians:
                            try:
                                # Inoltra il messaggio del frame così com'è
                                # Assicurati che il messaggio contenga 'sender_id' e 'content'
                                message['sender_id'] = pin # Aggiungi/assicura sender_id per il tecnico
                                await connected_technicians[tech_id].send(json_dumps_message(message))
                            except Exception as e:
                                logging.error(f"Errore nell'inoltro del frame da {pin} a tecnico {tech_id}: {e}")
                                # Se l'invio fallisce, potremmo voler disconnettere il tecnico
                                # o gestire diversamente. Per ora, logghiamo.
                else:
                    logging.warning(f"Frame ricevuto da client non registrato o non valido: {sender_id}")
            elif msg_type == "command" and sender_role == "technician":
                target_id = message.get("target_id") # Il PIN del client a cui è destinato il comando
                if target_id and target_id in connected_clients:
                    try:
                        # Inoltra il comando al client target
                        await connected_clients[target_id].send(json_dumps_message(message))
                        # logging.info(f"Comando inoltrato da tecnico a client {target_id}")
                    except Exception as e:
                        logging.error(f"Errore nell'inoltro del comando a client {target_id}: {e}")
                else:
                    logging.warning(f"Comando ricevuto da tecnico {sender_id} per client {target_id} non trovato o non online.")
                    if websocket: # Se il websocket del tecnico è ancora aperto, invia errore
                        await websocket.send(json.dumps({"type": "error", "message": f"Client con PIN {target_id} non trovato o non online per il comando."}))
            else:
                logging.warning(f"Messaggio non gestito o malformato: {message_json}")
                if websocket:
                    await websocket.send(json.dumps({"type": "error", "message": "Messaggio non riconosciuto."}))

    except websockets.exceptions.ConnectionClosedOK:
        logging.info("Connessione WebSocket chiusa normalmente.")
    except websockets.exceptions.ConnectionClosedError as e:
        logging.error(f"Connessione WebSocket chiusa con errore: {e}")
    except json.JSONDecodeError:
        logging.error("Errore di decodifica JSON nel messaggio ricevuto.")
    except Exception as e:
        logging.critical(f"Errore imprevisto nel gestore WebSocket: {e}", exc_info=True)
    finally:
        await unregister(websocket)

def json_dumps_message(message):
    """
    Helper to dump JSON, handling potential errors for circular references etc.
    """
    try:
        return json.dumps(message)
    except TypeError as e:
        logging.error(f"Errore di serializzazione JSON: {e} - Message: {message}")
        return json.dumps({"type": "error", "message": "Errore interno di serializzazione."})

async def main():
    # Per Hetzner, assicurati che l'IP sia raggiungibile pubblicamente
    # Ascolta su tutte le interfacce disponibili
    host = "0.0.0.0" # Ascolta su tutte le interfacce
    port = 8765

    # sys.argv per prendere host e porta da riga di comando se necessario
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    logging.info(f"Server WebSocket avviato su ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future() # Mantieni il server in esecuzione indefinitamente

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server interrotto da tastiera.")
    except Exception as e:
        logging.critical(f"Errore irreversibile durante l'avvio o l'esecuzione del server: {e}", exc_info=True)