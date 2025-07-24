# server/relay.py

import asyncio
import websockets

class Relay:
    def __init__(self):
        self.clients = {}
        self.technicians = {}
        # Mappa per associare un websocket al suo ID (per la disconnessione)
        self.ws_to_id = {}
        self.ws_to_role = {}

    async def register(self, websocket, role, id):
        if role == 'client':
            self.clients[id] = websocket
        elif role == 'technician':
            self.technicians[id] = websocket
        self.ws_to_id[websocket] = id
        self.ws_to_role[websocket] = role

    async def forward(self, source, target_id, message):
        # source è il websocket del mittente.
        # Se source è un client e invia lo schermo, dobbiamo inoltrarlo al tecnico accoppiato.
        # Se source è un tecnico e invia un comando, il target_id sarà il client.

        target_ws = None
        if source in self.clients.values(): # Se il mittente è un client (schermo)
            # Dobbiamo trovare il tecnico accoppiato a questo client.
            # Questa logica non è esplicita nel tuo codice.
            # Per ora, potresti assumere un tecnico predefinito o implementare un lookup.
            # Ad esempio, se 'tecnico-001' è sempre il destinatario degli schermi di 'cliente-001':
            if target_id == 'cliente-001': # O un altro meccanismo per trovare il tecnico
                target_ws = self.technicians.get('tecnico-001') # Assumendo ID fisso del tecnico
        elif source in self.technicians.values(): # Se il mittente è un tecnico (comando)
            target_ws = self.clients.get(target_id) # Cerca il client_id specificato

        if target_ws:
            await target_ws.send(message)
        else:
            print(f"Destinatario {target_id} non trovato o non accoppiato per inoltro.")

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