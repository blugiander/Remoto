# server/relay.py

import asyncio
import websockets

class Relay:
    def __init__(self):
        self.clients = {}
        self.technicians = {}
        # Mappa per associare un websocket al suo ID e ruolo
        self.ws_to_id = {}
        self.ws_to_role = {}

    async def register(self, websocket, role, id):
        if role == 'client':
            self.clients[id] = websocket
        elif role == 'technician':
            self.technicians[id] = websocket
        self.ws_to_id[websocket] = id
        self.ws_to_role[websocket] = role
        print(f"Relay DEBUG: Registrato {role} con ID {id}.")


    async def forward(self, source_websocket, target_id_from_sender_message, message_content_json_string):
        # source_websocket: il websocket del mittente (client o tecnico)
        # target_id_from_sender_message: l'ID target come specificato nel messaggio originale dal mittente (può essere None per messaggi schermo del client)
        # message_content_json_string: la stringa JSON della parte 'content' del messaggio (es. dati dello schermo o comando)

        target_ws = None
        source_role = self.ws_to_role.get(source_websocket) # Ottieni il ruolo del mittente

        print(f"Relay DEBUG: Tentativo di inoltro da {source_role} (ID: {self.ws_to_id.get(source_websocket)}).")

        if source_role == 'client':
            # Se il mittente è un client, il messaggio è un dato dello schermo.
            # Deve essere inoltrato al tecnico.
            # Assumiamo che 'tecnico-001' sia l'ID del tecnico che riceve i dati dello schermo.
            target_ws = self.technicians.get('tecnico-001')
            print(f"Relay DEBUG: Mittente è client. Targeting tecnico 'tecnico-001'.")
        elif source_role == 'technician':
            # Se il mittente è un tecnico, il messaggio è un comando.
            # Deve essere inoltrato al client specifico indicato da target_id_from_sender_message.
            target_ws = self.clients.get(target_id_from_sender_message)
            print(f"Relay DEBUG: Mittente è tecnico. Targeting client '{target_id_from_sender_message}'.")
        else:
            print(f"Relay DEBUG: Ruolo mittente sconosciuto per websocket {source_websocket}.")

        if target_ws:
            await target_ws.send(message_content_json_string)
            print(f"Relay DEBUG: Messaggio inoltrato con successo a {self.ws_to_id.get(target_ws)}.")
        else:
            print(f"Relay DEBUG: Destinatario '{target_id_from_sender_message}' non trovato o non accoppiato per inoltro (ruolo mittente: {source_role}).")

    def unregister(self, websocket):
        if websocket in self.ws_to_id:
            _id = self.ws_to_id[websocket]
            _role = self.ws_to_role[websocket]
            if _role == 'client' and _id in self.clients:
                del self.clients[_id]
                print(f"Client {_id} disconnesso.")
            elif _role == 'technician' and _id in self.technicians:
                del self.technicians[_id]
                print(f"Tecnico {_id} disconnesso.")
            del self.ws_to_id[websocket]
            del self.ws_to_role[websocket]