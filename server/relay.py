# server/relay.py (OPZIONALE - NON NECESSARIO PER IL FUNZIONAMENTO BASE)

import asyncio
import websockets
import json
from config import SERVER_HOST, SERVER_PORT # Importa dalla tua config.py

RELAY_PORT = 8000 # Porta su cui il relay ascolterà le connessioni in entrata

async def relay_handler(in_websocket, path):
    print(f"RELAY: Nuova connessione da {in_websocket.remote_address} al relay. Reindirizzo a {SERVER_HOST}:{SERVER_PORT}")
    out_websocket = None
    try:
        # Connessione al server principale
        async with websockets.connect(f"ws://{SERVER_HOST}:{SERVER_PORT}") as out_websocket:
            print(f"RELAY: Connesso con successo al server principale.")

            # Task per inoltrare messaggi dal client al server principale
            async def client_to_server():
                try:
                    while True:
                        message = await in_websocket.recv()
                        await out_websocket.send(message)
                        # print(f"RELAY: Inoltrato messaggio client -> server")
                except websockets.exceptions.ConnectionClosedOK:
                    print("RELAY: Connessione client chiusa normalmente.")
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"RELAY ERRORE: Connessione client chiusa inaspettatamente: {e}")
                except Exception as e:
                    print(f"RELAY ERRORE: Errore nel inoltro client -> server: {e}")
                finally:
                    if not in_websocket.closed:
                        await in_websocket.close()
                    if not out_websocket.closed:
                        await out_websocket.close()

            # Task per inoltrare messaggi dal server principale al client
            async def server_to_client():
                try:
                    while True:
                        message = await out_websocket.recv()
                        await in_websocket.send(message)
                        # print(f"RELAY: Inoltrato messaggio server -> client")
                except websockets.exceptions.ConnectionClosedOK:
                    print("RELAY: Connessione server chiusa normalmente.")
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"RELAY ERRORE: Connessione server chiusa inaspettatamente: {e}")
                except Exception as e:
                    print(f"RELAY ERRORE: Errore nel inoltro server -> client: {e}")
                finally:
                    if not in_websocket.closed:
                        await in_websocket.close()
                    if not out_websocket.closed:
                        await out_websocket.close()

            # Esegui entrambi i task in parallelo
            await asyncio.gather(client_to_server(), server_to_client())

    except websockets.exceptions.ConnectionRefusedError:
        print(f"RELAY ERRORE: Connessione rifiutata dal server principale {SERVER_HOST}:{SERVER_PORT}. Assicurati che il server sia in esecuzione.")
        await in_websocket.close()
    except Exception as e:
        print(f"RELAY ERRORE: Errore nel handler del relay: {e}")
        if out_websocket and not out_websocket.closed:
            await out_websocket.close()
        if not in_websocket.closed:
            await in_websocket.close()
    finally:
        print(f"RELAY: Connessione dal client {in_websocket.remote_address} terminata.")

async def main():
    print(f"RELAY: Avvio server Relay su ws://{SERVER_HOST}:{RELAY_PORT}")
    async with websockets.serve(relay_handler, SERVER_HOST, RELAY_PORT): # SERVER_HOST per ascoltare su tutte le interfacce disponibili
        await asyncio.Future()  # Esegui indefinitamente

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("RELAY: Server Relay interrotto manualmente.")
    except Exception as e:
        print(f"RELAY ERRORE CRITICO: {e}")