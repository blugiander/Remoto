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
                else: # role == 'technician'
                    valid = auth.verify_pin(pin)
                    if valid:
                        # Associa il tecnico al client registrato con quel PIN
                        # Questo è un punto di miglioramento: il server dovrebbe sapere
                        # quale client corrisponde a quale PIN per instradare i messaggi correttamente.
                        # Per ora, assumiamo una relazione 1:1 o che 'target_id' sia sempre 'cliente-001'
                        # lato tecnico per i comandi, e che il server inoltri lo schermo
                        # dal client connesso al tecnico che ha usato il PIN di quel client.
                        await ws.send(json.dumps({'status': 'connected'}))
                    else:
                        await ws.send(json.dumps({'status': 'invalid_pin'}))

            elif msg_type == 'message':
                # Il client invia lo schermo con 'content': {'tipo': 'screen', 'data': '...'}.
                # Il tecnico invia comandi con 'content': {'tipo': 'click/keypress', 'x/key': ...}.
                
                # 'data' è il messaggio JSON completo ricevuto dal mittente (client o tecnico).
                # 'content' è il payload effettivo (es. dati dello schermo o comando).
                
                # Dobbiamo inoltrare 'content' come stringa JSON al destinatario appropriato.
                
                # Se il mittente è un client, il messaggio contiene l'ID del client stesso.
                # Per inoltrare lo schermo al tecnico, dobbiamo sapere a quale tecnico inviarlo.
                # Attualmente, non c'è una mappatura esplicita client-tecnico nel Relay.
                # Un'opzione temporanea è inviare al TECHNICIAN_ID definito (es. 'tecnico-001'),
                # o implementare una logica di accoppiamento nel Relay basata sul PIN.

                # Per questo esempio, assumo che il target_id sia contenuto nel messaggio originale
                # se proveniente dal tecnico (per i comandi), o che il server gestisca il routing
                # dello schermo dal client al tecnico associato al PIN.
                
                # Importante: `content` è già un dizionario Python. Dobbiamo serializzarlo di nuovo.
                if content:
                    # Inoltra al target_id specificato dal mittente (es. tecnico per i comandi)
                    # oppure, se è un messaggio da un client (schermo), il server deve capire a chi inviarlo.
                    # Per il tuo setup, un client ('cliente-001') ha un solo tecnico ('tecnico-001').
                    
                    # Se il messaggio proviene dal CLIENT (ruolo 'client'),
                    # allora 'id' è il CLIENT_ID (es. 'cliente-001').
                    # Dobbiamo trovare il tecnico associato a quel client.
                    # Poiché non c'è una mappatura esplicita nel Relay per questo,
                    # e il tecnico ha un 'target_id' fisso per 'cliente-001',
                    # possiamo assumere che il messaggio dello schermo dal client vada al tecnico principale.
                    
                    # Potresti anche passargli il 'target_id' dal messaggio se presente (es. nei comandi del tecnico).
                    # Se 'data' ha un 'target_id', usalo. Altrimenti, se è un messaggio di schermo da un client,
                    # il Relay dovrà avere logica per inoltrare al tecnico accoppiato al client_id.

                    # Per una soluzione più robusta:
                    # Il server deve mantenere la mappatura PIN -> client_id -> technician_ws
                    # Quindi, quando un client invia lo schermo (sapendo il suo client_id),
                    # il server può cercare il technician_ws associato al client_id.

                    # Per la logica attuale del tuo relay, potresti dover passare l'id del mittente
                    # e lasciare che il relay decida chi è il destinatario in base al ruolo.

                    # Modifica chiave: Inoltra l'intero messaggio 'data' se vuoi che il tecnico
                    # riceva la struttura completa, oppure continua a inoltrare 'content'
                    # ma assicurandoti che sia serializzato. Il tuo 'technician/main.py' si aspetta 'content'.
                    # Quindi, la modifica più diretta e corretta è:
                    await relay.forward(ws, data.get('target_id'), json.dumps(content))
                    
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Connessione chiusa normalmente da {ws.remote_address}")
    except Exception as e:
        print(f'Errore generico in handler: {e}')
    finally:
        # Gestione della disconnessione
        relay.unregister(ws)


async def main():
    async with websockets.serve(handler, SERVER_HOST, SERVER_PORT):
        print(f"Server in ascolto su porta {SERVER_PORT}...")
        await asyncio.Future() # Mantiene il server in esecuzione indefinitamente

if __name__ == "__main__":
    asyncio.run(main())