import asyncio
import websockets
import json
from relay import Relay
from auth import AuthManager
from config import SERVER_HOST, SERVER_PORT

relay = Relay()
auth = AuthManager()

async def handler(ws):
    try:
        async for msg in ws:
            data = json.loads(msg)
            role = data.get('role')
            id = data.get('id')
            pin = data.get('pin')
            msg_type = data.get('type')
            content = data.get('content')

            if msg_type == 'register':
                await relay.register(ws, role, id)
                if role == 'client':
                    generated_pin = auth.create_session(id)
                    await ws.send(json.dumps({'pin': generated_pin}))
                else:
                    valid = auth.verify_pin(pin)
                    if valid:
                        await ws.send(json.dumps({'status': 'connected'}))
                    else:
                        await ws.send(json.dumps({'status': 'invalid_pin'}))

            elif msg_type == 'message':
                await relay.forward(ws, data.get('target_id'), content)

    except Exception as e:
        print(f'Errore: {e}')

async def main():
    async with websockets.serve(handler, SERVER_HOST, SERVER_PORT):
        print(f"Server in ascolto su porta {SERVER_PORT}...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
