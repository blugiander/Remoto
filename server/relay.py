# server/relay.py

import asyncio
import websockets

class Relay:
    def __init__(self):
        self.clients = {} # Mappa ID client -> WebSocket client
        self.technicians = {} # Mappa ID tecnico -> WebSocket tecnico
        self.ws_to_id = {} # Mappa WebSocket -> ID
        self.id_to_ws = {} # Mappa ID -> WebSocket

        self.client_to_technician = {} # client_id -> technician_ws
        self.technician_to_client = {} # technician_id -> client_ws

    async def register(self, websocket, role, id):
        print(f"RELAY DEBUG: Registrato {role} con ID {id}.")
        self.ws_to_id[websocket] = id
        self.id_to_ws[id] = websocket

        if role == 'client':
            self.clients[id] = websocket
        elif role == 'technician':
            self.technicians[id] = websocket

    def unregister(self, websocket):
        id = self.ws_to_id.get(websocket)
        if id:
            print(f"RELAY DEBUG: Deregistrazione di {id}.")
            if id in self.clients:
                del self.clients[id]
                # Rimuovi anche l'abbinamento se il client si disconnette
                if id in self.client_to_technician:
                    technician_ws = self.client_to_technician[id]
                    if technician_ws in self.ws_to_id:
                        technician_id = self.ws_to_id[technician_ws]
                        if technician_id in self.technician_to_client:
                            del self.technician_to_client[technician_id]
                    del self.client_to_technician[id]

            elif id in self.technicians:
                del self.technicians[id]
                # Rimuovi anche l'abbinamento se il tecnico si disconnette
                if id in self.technician_to_client:
                    client_ws = self.technician_to_client[id]
                    if client_ws in self.ws_to_id:
                        client_id = self.ws_to_id[client_ws]
                        if client_id in self.client_to_technician:
                            del self.client_to_technician[client_id]
                    del self.technician_to_client[id]

            if websocket in self.ws_to_id:
                del self.ws_to_id[websocket]
            if id in self.id_to_ws:
                del self.id_to_ws[id]

    # --- NUOVI METODI PER IL RELAY ---
    def add_pairing(self, client_id, technician_id):
        client_ws = self.get_client_ws(client_id)
        technician_ws = self.get_technician_ws(technician_id)
        if client_ws and technician_ws:
            self.client_to_technician[client_id] = technician_ws
            self.technician_to_client[technician_id] = client_ws
            print(f"RELAY DEBUG: Abbinamento creato: Client {client_id} <-> Tecnico {technician_id}")
            return True
        print(f"RELAY DEBUG: Fallito abbinamento tra Client {client_id} e Tecnico {technician_id} (WS non trovati).")
        return False

    def get_client_ws(self, client_id):
        return self.clients.get(client_id)

    def get_technician_ws(self, technician_id):
        return self.technicians.get(technician_id)

    def get_technician_for_client(self, client_id):
        # Restituisce il WebSocket del tecnico abbinato a un client
        return self.client_to_technician.get(client_id)
    
    def get_client_for_technician(self, technician_id):
        # Restituisce il WebSocket del client abbinato a un tecnico
        return self.technician_to_client.get(technician_id)

    # Questo metodo 'forward' non è più utilizzato attivamente dal server/main.py,
    # ma lo lascio per completezza.
    async def forward(self, source_websocket, target_id_from_sender, message_content_json):
        pass