import asyncio
import websockets

class Relay:
    def __init__(self):
        self.clients = {}
        self.technicians = {}

    async def register(self, websocket, role, id):
        if role == 'client':
            self.clients[id] = websocket
        elif role == 'technician':
            self.technicians[id] = websocket

    async def forward(self, source, target_id, message):
        target_ws = self.clients.get(target_id) or self.technicians.get(target_id)
        if target_ws:
            await target_ws.send(message)
