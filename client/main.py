import asyncio
import websockets
import json
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID
from capture import cattura_schermo
from control import esegui_comando

async def client_loop():
    async with websockets.connect(f"ws://{SERVER_HOST}:{SERVER_PORT}") as ws:
        await ws.send(json.dumps({
            'type': 'register',
            'role': 'client',
            'id': CLIENT_ID
        }))

        response = await ws.recv()
        pin_data = json.loads(response)
        print(f"📌 PIN da comunicare al tecnico: {pin_data['pin']}")

        while True:
            screen = cattura_schermo()
            await ws.send(json.dumps({
                'type': 'message',
                'role': 'client',
                'id': CLIENT_ID,
                'content': {
                    'tipo': 'screen',
                    'data': screen
                }
            }))

            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
                data = json.loads(msg)
                esegui_comando(data['content'])
            except asyncio.TimeoutError:
                pass

asyncio.run(client_loop())
