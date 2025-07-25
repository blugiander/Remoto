# server/relay.py

import asyncio
import websockets
import json

class Relay:
    def __init__(self):
        self.clients = {}         # Mappa ID_CLIENT -> websocket del client
        self.technicians = {}     # Mappa ID_TECNICO -> websocket del tecnico
        self.ws_to_id = {}        # Mappa per associare un websocket al suo ID
        self.ws_to_role = {}      # Mappa per associare un websocket al suo ruolo
        
        self.client_pins = {}      # Mappa ID_CLIENT -> PIN (generato dal server)
        self.technician_to_client = {} # Mappa ID_TECNICO -> ID_CLIENT (a cui è connesso)
        print("RELAY DEBUG: Relay instance initialized with all maps.") # Aggiunto log per debug

    async def register(self, websocket, role, id):
        if role == 'client':
            self.clients[id] = websocket
        elif role == 'technician':
            self.technicians[id] = websocket
        self.ws_to_id[websocket] = id
        self.ws_to_role[websocket] = role
        print(f"RELAY DEBUG: Registrato {role} con ID {id}. Stato attuali tecnici: {list(self.technicians.keys())}, clienti: {list(self.clients.keys())}")

    async def deregister(self, websocket):
        # Quando un websocket si disconnette, rimuovilo da tutte le mappe
        if websocket in self.ws_to_id:
            id = self.ws_to_id[websocket]
            role = self.ws_to_role[websocket]

            if role == 'client' and id in self.clients:
                del self.clients[id]
                print(f"RELAY DEBUG: Client {id} disconnesso dal relay.")
                if id in self.client_pins:
                    del self.client_pins[id]
                    print(f"RELAY DEBUG: PIN {self.client_pins.get(id, 'N/A')} rimosso per client {id}.")
                
                # Rimuovi eventuali tecnici associati a questo client disconnesso
                tech_ids_to_remove = []
                for tech_id, client_assoc_id in self.technician_to_client.items():
                    if client_assoc_id == id:
                        tech_ids_to_remove.append(tech_id)
                for tech_id in tech_ids_to_remove:
                    if tech_id in self.technician_to_client:
                        del self.technician_to_client[tech_id]
                        print(f"RELAY DEBUG: Associazione tecnico {tech_id} a client {id} rimossa.")

            elif role == 'technician' and id in self.technicians:
                del self.technicians[id]
                print(f"RELAY DEBUG: Tecnico {id} disconnesso dal relay.")
                if id in self.technician_to_client:
                    del self.technician_to_client[id]
                    print(f"RELAY DEBUG: Associazione tecnico {id} rimossa.")
            
            # Rimuovi anche da ws_to_id e ws_to_role
            if websocket in self.ws_to_id:
                del self.ws_to_id[websocket]
            if websocket in self.ws_to_role:
                del self.ws_to_role[websocket]
            
            print(f"RELAY DEBUG: Stato attuali tecnici dopo disconnessione: {list(self.technicians.keys())}")
            print(f"RELAY DEBUG: Stato attuali clienti dopo disconnessione: {list(self.clients.keys())}")
        else:
            print(f"RELAY DEBUG: Tentativo di deregistrare un websocket sconosciuto: {websocket.remote_address if hasattr(websocket, 'remote_address') else 'N/A'}")


    async def forward(self, source_websocket, target_id, message_json_string):
        source_role = self.ws_to_role.get(source_websocket)
        source_id = self.ws_to_id.get(source_websocket)

        if not source_role or not source_id:
            print("RELAY ERRORE: Messaggio da un websocket non registrato durante l'inoltro.")
            return

        if source_role == 'client':
            target_ws = self.technicians.get(target_id) 
            if target_ws:
                if target_ws.open: # Controlla se il target_ws è ancora aperto prima di inviare
                    await target_ws.send(message_json_string) 
                else:
                    print(f"RELAY DEBUG: Websocket del tecnico {target_id} è chiuso. Frame non inoltrato.")
            else:
                print(f"RELAY DEBUG: Tecnico {target_id} non trovato. Frame non inoltrato.")

        elif source_role == 'technician':
            target_ws = self.clients.get(target_id)
            if target_ws:
                if target_ws.open: # Controlla se il target_ws è ancora aperto prima di inviare
                    await target_ws.send(message_json_string) 
                else:
                    print(f"RELAY DEBUG: Websocket del client {target_id} è chiuso. Comando non inoltrato.")
            else:
                print(f"RELAY DEBUG: Client {target_id} non trovato. Comando non inoltrato.")
        else:
            print(f"RELAY ERRORE: Ruolo sconosciuto ({source_role}). Messaggio non inoltrato.")