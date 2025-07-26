# remoto/client/main.py

import asyncio
import websockets
import json
import base64
import time
import threading
import sys
import os # Importa il modulo os per la gestione dei percorsi
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

# --- Inizio sezione per la gestione dei percorsi di importazione ---
# Ottiene la directory corrente del file (client/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Risale alla directory radice del progetto (Remoto/)
project_root = os.path.join(current_dir, '..')
# Aggiunge la directory radice del progetto al sys.path
# Questo permette di importare moduli direttamente dalla radice, come 'config' e 'command_executor'
sys.path.append(project_root)
# --- Fine sezione per la gestione dei percorsi di importazione ---


# Assicurati che i tuoi import siano corretti e che i percorsi siano validi
# 'capture' si trova nella stessa directory 'client/', quindi è un import relativo
from .capture import ScreenCapture
# 'command_executor' si trova nella directory radice del progetto, quindi è un import diretto
from command_executor import CommandExecutor 
# 'config' si trova nella directory radice del progetto, quindi è un import diretto
from config import SERVER_HOST, SERVER_PORT, CLIENT_ID, CLIENT_PIN


class ClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Client Remoto - ID: {CLIENT_ID}")
        self.geometry("800x600")

        self.screen_capture = ScreenCapture()
        self.command_executor = CommandExecutor()
        self.websocket = None
        self.is_connected = False
        self.last_frame_time = time.time()
        self.fps_counter = 0

        # UI elements
        self.label = ctk.CTkLabel(self, text="Status: Disconnesso", font=("Arial", 16))
        self.label.pack(pady=20)

        self.pin_label = ctk.CTkLabel(self, text=f"PIN per il tecnico: {CLIENT_PIN}", font=("Arial", 24, "bold"))
        self.pin_label.pack(pady=10)

        self.connect_button = ctk.CTkButton(self, text="Connetti al Server", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

        # Frame rate display
        self.fps_label = ctk.CTkLabel(self, text="FPS: 0.00", font=("Arial", 14))
        self.fps_label.pack(pady=5)

        self.bind("<Destroy>", self.on_closing)

    async def connect_to_server(self):
        if self.is_connected:
            print("Già connesso al server.")
            return

        uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
        self.label.configure(text=f"Status: Connessione a {uri}...")
        try:
            self.websocket = await websockets.connect(uri)
            print(f"Connesso al server: {uri}")
            self.is_connected = True
            self.label.configure(text="Status: Connesso!")
            
            # Invia messaggio di registrazione con CLIENT_ID e CLIENT_PIN
            registration_message = {
                "type": "register",
                "role": "client",
                "id": CLIENT_ID,
                "pin": CLIENT_PIN
            }
            await self.websocket.send(json.dumps(registration_message))
            print(f"Inviato messaggio di registrazione: {registration_message}")

            # Avvia i loop di invio e ricezione in background
            asyncio.create_task(self.send_screen_frames())
            asyncio.create_task(self.receive_commands())

        except Exception as e:
            print(f"Errore di connessione al server: {e}")
            self.label.configure(text=f"Status: Errore di connessione - {e}")
            self.is_connected = False

    async def send_screen_frames(self):
        while self.is_connected:
            try:
                frame_jpeg_bytes = self.screen_capture.get_frame_as_jpeg()
                if frame_jpeg_bytes:
                    # Codifica base64 e invia
                    base64_frame = base64.b64encode(frame_jpeg_bytes).decode('utf-8')
                    message = {
                        "type": "frame",
                        "sender_id": CLIENT_ID,
                        "target_role": "technician", # Frame da inviare al tecnico
                        "content": base64_frame
                    }
                    await self.websocket.send(json.dumps(message))
                    
                    self.fps_counter += 1
                    if time.time() - self.last_frame_time >= 1: # Update FPS every second
                        self.fps_label.configure(text=f"FPS: {self.fps_counter / (time.time() - self.last_frame_time):.2f}")
                        self.fps_counter = 0
                        self.last_frame_time = time.time()

                await asyncio.sleep(0.01) # Small delay to avoid 100% CPU usage
            except websockets.exceptions.ConnectionClosedOK:
                print("Connessione WebSocket chiusa normalmente (send_screen_frames).")
                self.is_connected = False
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Errore di connessione WebSocket in send_screen_frames: {e}")
                self.is_connected = False
                break
            except Exception as e:
                print(f"Errore durante l'invio del frame: {e}")
                await asyncio.sleep(1) # Wait a bit before retrying

    async def receive_commands(self):
        while self.is_connected:
            try:
                message_json = await self.websocket.recv()
                message = json.loads(message_json)

                if message.get("type") == "command" and message.get("target_id") == CLIENT_ID:
                    command_type = message.get("content", {}).get("command_type")
                    command_data = message.get("content", {}).get("data")
                    
                    if command_type and command_data:
                        print(f"Ricevuto comando: {command_type} con dati: {command_data}")
                        # Esegui il comando in un thread separato per non bloccare l'UI/WebSocket
                        # Passa l'intero dizionario 'content' che contiene 'command_type' e 'data'
                        threading.Thread(target=self.command_executor.execute_command, args=(message.get("content"),)).start()
                    else:
                        print(f"Comando malformato ricevuto: {message}")
                else:
                    print(f"Messaggio ricevuto (non comando per me): {message}")

            except websockets.exceptions.ConnectionClosedOK:
                print("Connessione WebSocket chiusa normalmente (receive_commands).")
                self.is_connected = False
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Errore di connessione WebSocket in receive_commands: {e}")
                self.is_connected = False
                break
            except json.JSONDecodeError:
                print(f"Errore di decodifica JSON: {message_json}")
            except Exception as e:
                print(f"Errore durante la ricezione del comando: {e}")
                await asyncio.sleep(1) # Wait a bit before retrying

    def on_closing(self, event=None):
        print("Applicazione chiusa. Tentativo di disconnessione...")
        if self.websocket:
            # Chiudi la connessione WebSocket nel loop di asyncio
            asyncio.create_task(self.websocket.close())
        self.destroy() # Distrugge la finestra Tkinter/CustomTkinter

async def main():
    app = ClientApp()
    # Esegui il loop di asyncio in un thread separato per non bloccare la GUI Tkinter
    # Questo è un approccio comune quando si mescolano asyncio e Tkinter
    loop = asyncio.get_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    
    # Collega il metodo di connessione al button (sarà chiamato in un task asyncio)
    # È cruciale avviare la connessione in un task asyncio
    app.connect_button.configure(command=lambda: asyncio.create_task(app.connect_to_server()))

    app.mainloop()

if __name__ == "__main__":
    # Avvia l'applicazione client
    # ctk.set_appearance_mode("System") # Default value
    # ctk.set_default_color_theme("blue") # Default value
    asyncio.run(main())