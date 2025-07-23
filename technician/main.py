import asyncio, json, websockets
from viewer import mostra_immagine
from control import click, keypress

SERVER_HOST = '188.245.238.160'
SERVER_PORT = 8765
TECHNICIAN_ID = 'tecnico-001'

async def technician_loop():
    pin = input("🔑 Inserisci il PIN ricevuto dal cliente: ")

    async with websockets.connect(f"ws://{SERVER_HOST}:{SERVER_PORT}") as ws:
        await ws.send(json.dumps({
            'type': 'register',
            'role': 'technician',
            'id': TECHNICIAN_ID,
            'pin': pin
        }))
        response = json.loads(await ws.recv())

        if response.get('status') != 'connected':
            print("❌ PIN errato o client non disponibile.")
            return

        print("✅ Connesso. Ricezione schermo...")

        while True:
            msg = json.loads(await ws.recv())
            if msg.get('content', {}).get('tipo') == 'screen':
                mostra_immagine(msg['content']['data'])

asyncio.run(technician_loop())
