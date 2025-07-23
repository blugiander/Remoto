import asyncio
import websockets
import json
from viewer import mostra_immagine
from control import click, keypress

SERVER_HOST = '188.245.238.160'    # fissa
SERVER_PORT = 8765
TECHNICIAN_ID = 'tecnico-001'     # fissa

async def technician_loop():
    pin = input("🔑 Inserisci il PIN ricevuto dal cliente: ")

    async with websockets.connect(f"ws://{SERVER_HOST}:{SERVER_PORT}") as ws:
        print("🔗 Connessione al server...")
        await ws.send(json.dumps({
            'type': 'register',
            'role': 'technician',
            'id': TECHNICIAN_ID,
            'pin': pin
        }))

        response = await ws.recv()
        status = json.loads(response)
        if status.get('status') != 'connected':
            print("❌ PIN errato o cliente non disponibile.")
            return

        print("✅ Connesso. Ricezione schermo e pronto al controllo...")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if data.get('content', {}).get('tipo') == 'screen':
                mostra_immagine(data['content']['data'])

asyncio.run(technician_loop())
