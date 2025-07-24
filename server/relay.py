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
        print(f"Relay DEBUG: Registrato {role} con ID {id}. Stato attuali tecnici: {list(self.technicians.keys())}.") # AGGIUNTO DEBUG
        #print(f"Relay DEBUG: Mappa WS-to-ID: {self.ws_to_id}") # Debug aggiuntivo se necessario
        #print(f"Relay DEBUG: Mappa WS-to-Role: {self.ws_to_role}") # Debug aggiuntivo se necessario


    async def forward(self, source_websocket, target_id_from_sender_message, message_content_json_string):
        target_ws = None
        source_role = self.ws_to_role.get(source_websocket)
        source_id = self.ws_to_id.get(source_websocket)

        print(f"Relay DEBUG: Tentativo di inoltro da {source_role} (ID: {source_id}).")
        #print(f"Relay DEBUG: Stato attuali tecnici prima del get: {list(self.technicians.keys())}.") # AGGIUNTO DEBUG QUI

        if source_role == 'client':
            # Assumiamo che 'tecnico-001' sia l'ID del tecnico che riceve i dati dello schermo.
            target_id_for_client_message = 'tecnico-001' # ID fisso del tecnico per inoltro schermo
            target_ws = self.technicians.get(target_id_for_client_message)
            print(f"Relay DEBUG: Mittente è client. Targeting tecnico '{target_id_for_client_message}'. Trovato WS? {'Sì' if target_ws else 'No'}.") # AGGIUNTO DEBUG
        elif source_role == 'technician':
            target_ws = self.clients.get(target_id_from_sender_message)
            print(f"Relay DEBUG: Mittente è tecnico. Targeting client '{target_id_from_sender_message}'. Trovato WS? {'Sì' if target_ws else 'No'}.") # AGGIUNTO DEBUG
        else:
            print(f"Relay DEBUG: Ruolo mittente sconosciuto per websocket {source_websocket}.")

        if target_ws:
            await target_ws.send(message_content_json_string)
            print(f"Relay DEBUG: Messaggio inoltrato con successo a {self.ws_to_id.get(target_ws)}.")
        else:
            print(f"Relay DEBUG: Destinatario '{target_id_from_sender_message if source_role == 'technician' else target_id_for_client_message}' non trovato o non accoppiato per inoltro (ruolo mittente: {source_role}).") # MODIFICATA STAMPA PER CHIAREZZA

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