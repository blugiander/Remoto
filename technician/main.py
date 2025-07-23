import asyncio
import websockets
import json
from viewer import mostra_immagine

SERVER_HOST = '188.245.238.160'   # Sostituisci con IP pubblico VPS
SERVER_PORT = 8765
TECHNICIAN_ID = 'tecnico-001'    # identificativo tecnico

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

        response = json.loads(await ws.recv())
        if response.get('status') != 'connected':
            print("❌ PIN errato o client non disponibile.")
            return

        print("✅ Connesso. Ricezione schermo...")

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)

                # DEBUG temporaneo: mostra cosa viene ricevuto
                print("📨 Ricevuto:", data)

                if isinstance(data, dict) and data.get('tipo') == 'screen':
                    mostra_immagine(data['data'])

                elif isinstance(data, dict) and 'content' in data:
                    content = data['content']
                    if content.get('tipo') == 'screen':
                        mostra_immagine(content['data'])

            except Exception as e:
                print(f"❌ Errore durante la ricezione: {e}")

asyncio.run(technician_loop())
